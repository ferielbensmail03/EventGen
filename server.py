"""EventGen - web studio (API + static frontend).

    .venv/Scripts/python.exe server.py          ->  http://127.0.0.1:8000

Thin HTTP layer over the real PyTorch models (src/inference.py). Nothing is
simulated: every description returned by /api/generate comes from
EventGenerator.generate_from_text with the decoding settings sent by the UI.
The Streamlit app (app.py) is untouched and still works.

Endpoints
  GET  /api/meta        models on disk, type labels, model configs + training summaries
  POST /api/inspect     {title, types}              -> serialised input + tokens (known / <unk>)
  POST /api/generate    {title, types, models, method, beam_width, max_len, no_repeat_ngram}
                                                    -> one result per model (text, tokens, time, attention)
  GET  /api/results     comparison.csv, history.csv per model, cleaning report, error rates
  GET  /api/test-event  a random unseen test event (input + human reference)
"""
from __future__ import annotations

import ast
import json
import math
import random
import threading
import time
from pathlib import Path

import pandas as pd
import torch
import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from src import config as C
from src.config import GenerationConfig
from src.data_loader import TYPE_FR
from src.preprocessing import serialize_event, tokenize

ROOT = Path(__file__).resolve().parent
WEB = ROOT / "web"
torch.set_num_threads(max(1, min(4, torch.get_num_threads())))

MODEL_INFO = {
    "baseline": {"label": "LSTM Encoder–Decoder", "short": "Baseline",
                 "architecture": "Embedding 128 → LSTM encoder 256 → final (h, c) as a fixed context → LSTM decoder 256 → softmax"},
    "attention": {"label": "LSTM + Bahdanau attention", "short": "Attention",
                  "architecture": "Embedding 128 → LSTM encoder 256 → additive attention c(t) = Σ α(t,i)·h_i at every step → LSTM decoder 256 → softmax"},
}
TYPE_CHOICES = sorted(set(TYPE_FR.values()))

# ------------------------------------------------------------------ model cache
_lock = threading.Lock()
_cache: dict[str, tuple[float, object]] = {}      # name -> (best.pt mtime, EventGenerator)


def available_models() -> list[str]:
    if not C.MODELS_DIR.exists():
        return []
    return sorted(d.name for d in C.MODELS_DIR.iterdir() if (d / "best.pt").exists())


def get_generator(name: str):
    """Load (or reload when best.pt changed, e.g. after retraining) a model."""
    from src.inference import EventGenerator
    path = C.MODELS_DIR / name
    mtime = (path / "best.pt").stat().st_mtime
    cached = _cache.get(name)
    if cached and cached[0] == mtime:
        return cached[1]
    try:
        gen = EventGenerator(path, device="cpu")
    except Exception:
        if cached:                       # checkpoint being written by the trainer: keep the old one
            return cached[1]
        raise
    _cache[name] = (mtime, gen)
    return gen


def read_json(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def clean_num(v):
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    return v


def df_records(df: pd.DataFrame) -> list[dict]:
    return [{k: clean_num(v) for k, v in r.items()} for r in df.to_dict(orient="records")]


def bad_request(msg: str, code: int = 400):
    return JSONResponse({"error": msg}, status_code=code)


# ------------------------------------------------------------------ endpoints
async def meta(_: Request):
    models = []
    for name in available_models():
        d = C.MODELS_DIR / name
        summ = read_json(d / "train_summary.json") or {}
        kind = name.split("_")[0]
        hp = summ.get("hyperparameters", {})
        models.append({
            "name": name, "kind": kind, **MODEL_INFO.get(kind, {"label": name, "short": name, "architecture": ""}),
            "n_params": summ.get("n_params"), "best_val_loss": summ.get("best_val_loss"),
            "best_val_ppl": summ.get("best_val_ppl"), "best_epoch": summ.get("best_epoch"),
            "epochs_run": summ.get("epochs_run"), "train_size": summ.get("train_size"),
            "train_time_s": summ.get("train_time_s"), "subset": hp.get("train", {}).get("subset"),
            "updated": (d / "best.pt").stat().st_mtime,
        })
    return JSONResponse({"models": models, "types": TYPE_CHOICES,
                         "defaults": {"method": "beam", "beam_width": 3, "max_len": 60, "no_repeat_ngram": 3},
                         "input_schema": "type : <labels> | titre : <title>"})


def _parse_event(body: dict):
    title = str(body.get("title", "")).strip()
    types = [str(t) for t in body.get("types", []) if str(t) in TYPE_CHOICES]
    return title, types


async def inspect(request: Request):
    body = await request.json()
    title, types = _parse_event(body)
    src = serialize_event(title, types)
    models = available_models()
    vocab = None
    if models:
        with _lock:
            vocab = get_generator(models[0]).src_vocab.word2idx
    toks = tokenize(src)
    return JSONResponse({"serialized": src, "tokens": [{"t": t, "known": (vocab is None or t in vocab)} for t in toks],
                         "max_source_tokens": 40})


async def generate(request: Request):
    try:
        body = await request.json()
    except Exception:
        return bad_request("Invalid JSON body.")
    title, types = _parse_event(body)
    if not title:
        return bad_request("The event title is required.")
    if len(title) > 200:
        return bad_request("The title is too long (200 characters max).")
    method = body.get("method", "beam")
    if method not in ("greedy", "beam"):
        return bad_request("method must be 'greedy' or 'beam'.")
    try:
        gen_cfg = GenerationConfig(
            max_len=int(min(max(int(body.get("max_len", 60)), 5), 120)),
            beam_width=int(min(max(int(body.get("beam_width", 3)), 1), 10)),
            no_repeat_ngram=int(body.get("no_repeat_ngram", 3)) if int(body.get("no_repeat_ngram", 3)) in (0, 2, 3, 4) else 3,
            length_penalty=1.0, block_unk=True, clean_output=True)
    except (TypeError, ValueError):
        return bad_request("Invalid decoding settings.")
    available = available_models()
    names = [m for m in body.get("models", []) if m in available]
    if not names:
        return bad_request("No trained model selected (train one with scripts/03_train.py).", 404)

    src = serialize_event(title, types)
    results = []
    for name in names:
        with _lock:
            g = get_generator(name)
            t0 = time.perf_counter()
            r = g.generate_from_text(src, method=method, gen=gen_cfg)
            ms = (time.perf_counter() - t0) * 1000
        att = None
        if r.attention is not None and len(r.tokens):
            a = r.attention[: len(r.tokens) + 1, : len(r.source_tokens)]
            att = [[round(float(x), 4) for x in row] for row in a]
        kind = name.split("_")[0]
        results.append({"model": name, "kind": kind, "label": MODEL_INFO.get(kind, {}).get("label", name),
                        "text": r.text, "tokens": r.tokens, "n_tokens": len(r.tokens), "time_ms": round(ms, 1),
                        "source_tokens": r.source_tokens, "unknown": r.unknown_source_tokens,
                        "attention": att, "out_tokens": r.tokens + ["<eos>"]})
    return JSONResponse({"serialized": src, "method": method,
                         "settings": {"beam_width": gen_cfg.beam_width, "max_len": gen_cfg.max_len,
                                      "no_repeat_ngram": gen_cfg.no_repeat_ngram},
                         "results": results})


async def results(_: Request):
    out: dict = {"comparison": None, "history": {}, "cleaning": None, "errors": None}
    p = C.METRICS_DIR / "comparison.csv"
    if p.exists():
        out["comparison"] = df_records(pd.read_csv(p))
        out["comparison_updated"] = p.stat().st_mtime
    for name in available_models():
        h = C.MODELS_DIR / name / "history.csv"
        if h.exists():
            out["history"][name] = df_records(pd.read_csv(h))
    rep = read_json(C.CLEANING_REPORT)
    if rep:
        out["cleaning"] = {
            "raw_rows": rep.get("cleaning", {}).get("initial_rows"),
            "pairs": rep.get("pairs", {}).get("rows_out"),
            "split": {k: v.get("rows") for k, v in rep.get("split", {}).items() if isinstance(v, dict)},
            "src_vocab": rep.get("vocab", {}).get("src", {}).get("size"),
            "tgt_vocab": rep.get("vocab", {}).get("tgt", {}).get("size"),
        }
    e = C.METRICS_DIR / "error_rates.csv"
    if e.exists():
        out["errors"] = df_records(pd.read_csv(e))
    return JSONResponse(out)


_test_df: pd.DataFrame | None = None


async def test_event(_: Request):
    global _test_df
    if _test_df is None:
        if not C.SPLIT_FILES["test"].exists():
            return bad_request("Test split not found.", 404)
        _test_df = pd.read_csv(C.SPLIT_FILES["test"])
    row = _test_df.iloc[random.randrange(len(_test_df))]
    try:
        types = [t for t in ast.literal_eval(row["type_labels"]) if t in TYPE_CHOICES]
    except Exception:
        types = []
    return JSONResponse({"title": row["title_clean"], "types": types, "reference": row["target_text"]})


async def index(_: Request):
    return FileResponse(WEB / "index.html")


app = Starlette(routes=[
    Route("/", index),
    Route("/api/meta", meta),
    Route("/api/inspect", inspect, methods=["POST"]),
    Route("/api/generate", generate, methods=["POST"]),
    Route("/api/results", results),
    Route("/api/test-event", test_event),
    Mount("/", StaticFiles(directory=WEB), name="web"),
])

def no_cache(asgi_app):
    """Always serve the latest frontend files (no stale index.html / app.js after an update)."""
    async def wrapped(scope, receive, send):
        async def send_nc(message):
            if message["type"] == "http.response.start":
                headers = [(k, v) for k, v in message.get("headers", []) if k.lower() != b"cache-control"]
                message = {**message, "headers": headers + [(b"cache-control", b"no-cache")]}
            await send(message)
        await asgi_app(scope, receive, send_nc if scope["type"] == "http" else send)
    return wrapped


asgi = no_cache(app)

if __name__ == "__main__":
    uvicorn.run(asgi, host="127.0.0.1", port=8000)
