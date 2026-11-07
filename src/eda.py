"""Exploratory analysis of every source. All numbers are computed from the files."""
from __future__ import annotations

import re
from collections import Counter

import pandas as pd

from . import data_loader as dl
from .config import EDA_DIR
from .preprocessing import tokenize
from .utils import save_json
from .visualization import plot_bar_counts, plot_length_hist, plot_missing

HTML_RE = re.compile(r"<[a-zA-Z/][^>]*>")
URL_RE = re.compile(r"https?://|www\.")
FRENCH_HINTS = set("le la les des du une est et pour avec dans sur vous au aux".split())
ENGLISH_HINTS = set("the and of to with for is in on you your at our".split())


def guess_language(text: str) -> str:
    """Tiny stop-word heuristic (enough to tell FR from EN on these sources)."""
    words = re.findall(r"[a-zà-ÿ]+", str(text).lower())[:80]
    fr = sum(w in FRENCH_HINTS for w in words)
    en = sum(w in ENGLISH_HINTS for w in words)
    if fr == en == 0:
        return "unknown"
    return "fr" if fr > en else "en"


def structural_summary(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        "dtype": df.dtypes.astype(str),
        "non_null": df.notna().sum(),
        "missing_pct": (df.isna().mean() * 100).round(2),
        "n_unique": df.apply(lambda s: s.astype(str).nunique()),
        "example": df.apply(lambda s: str(s.dropna().iloc[0])[:80] if s.notna().any() else None),
    })


def text_summary(texts: pd.Series, short_threshold: int = 8) -> dict:
    t = texts.dropna().astype(str)
    words = t.str.split().str.len()
    langs = t.sample(min(len(t), 3000), random_state=0).map(guess_language).value_counts(normalize=True)
    return {
        "non_null": int(len(t)), "null": int(texts.isna().sum()),
        "empty": int((t.str.strip() == "").sum()),
        "chars_mean": round(float(t.str.len().mean()), 1), "chars_min": int(t.str.len().min()),
        "chars_max": int(t.str.len().max()),
        "words_mean": round(float(words.mean()), 1), "words_median": float(words.median()),
        "words_min": int(words.min()), "words_max": int(words.max()),
        "very_short_lt_%d_words" % short_threshold: int((words < short_threshold).sum()),
        "duplicate_texts": int(t.duplicated().sum()),
        "with_html_tags": int(t.str.contains(HTML_RE).sum()),
        "with_urls": int(t.str.contains(URL_RE).sum()),
        "with_markdown_bold": int(t.str.contains(r"\*\*", regex=True).sum()),
        "language_share_sample": {k: round(float(v), 3) for k, v in langs.items()},
    }


def vocab_stats(texts: pd.Series, top: int = 30) -> tuple[dict, Counter]:
    c: Counter = Counter()
    for s in texts.dropna().astype(str):
        c.update(tokenize(s))
    singletons = sum(1 for v in c.values() if v == 1)
    return {"tokens": int(sum(c.values())), "types": len(c), "singletons": singletons,
            "singleton_pct": round(100 * singletons / max(len(c), 1), 1)}, c


# ------------------------------------------------------------------ per source
def eda_datatourisme(save: bool = True) -> dict:
    raw = dl.load_datatourisme()
    dec = dl.decode_datatourisme(raw)
    types = Counter(t for labels in dec["type_labels"] for t in labels)
    out = {
        "source": "DATAtourisme - data.gouv.fr (Licence Ouverte / Etalab 2.0)",
        "rows": len(raw), "columns": list(raw.columns),
        "memory_mb": round(raw.memory_usage(deep=True).sum() / 1e6, 1),
        "fully_empty_columns": [c for c in raw.columns if raw[c].isna().all()],
        "duplicate_ids": int(raw["id"].duplicated().sum()),
        "corrupted_type_rows": int((dec["type_labels"].map(len) == 0).sum()),
        "title": text_summary(dec["title"]),
        "description": text_summary(dec["description"]),
        "description_language_tags": dec["description_lang"].value_counts(dropna=False).to_dict(),
        "top_types": types.most_common(25),
    }
    vs, counter = vocab_stats(dec["description"].dropna().sample(min(10000, dec["description"].notna().sum()),
                                                                 random_state=0))
    out["description_vocab_sample10k"] = vs
    if save:
        EDA_DIR.mkdir(parents=True, exist_ok=True)
        structural_summary(raw).to_csv(EDA_DIR / "datatourisme_structure.csv")
        plot_missing(raw, "DATAtourisme - missing values per column", EDA_DIR / "datatourisme_missing.png")
        plot_bar_counts(pd.Series(dict(types.most_common(20))), "DATAtourisme - event type labels (top 20)",
                        EDA_DIR / "datatourisme_types.png")
        plot_length_hist({"description": dec["description"].dropna().str.split().str.len()},
                         "DATAtourisme - description length", EDA_DIR / "datatourisme_lengths.png")
        content = Counter({w: c for w, c in counter.items() if len(w) > 3})
        plot_bar_counts(pd.Series(dict(content.most_common(25))), "DATAtourisme - frequent words (>3 chars)",
                        EDA_DIR / "datatourisme_words.png")
        save_json(out, EDA_DIR / "datatourisme_eda.json")
    return out


def eda_huggingface(save: bool = True) -> dict:
    df = dl.load_huggingface()
    out = {
        "source": "Hugging Face eliel2003/events (synthetic event-management data)",
        "rows": len(df), "columns": list(df.columns),
        "memory_mb": round(df.memory_usage(deep=True).sum() / 1e6, 1),
        "duplicate_rows": int(df.duplicated().sum()), "duplicate_ids": int(df["event_id"].duplicated().sum()),
        "categorical_cardinality": {c: int(df[c].nunique()) for c in
                                    ["event_type", "client_industry", "city", "season", "catering_style"]},
        "event_narrative": text_summary(df["event_narrative"]),
        "narrative_style": "post-event report (Objective / Execution Highlights / Outcome) in markdown",
    }
    if save:
        structural_summary(df).to_csv(EDA_DIR / "huggingface_structure.csv")
        plot_bar_counts(df["event_type"].value_counts(), "Hugging Face - event_type", EDA_DIR / "hf_event_type.png")
        save_json(out, EDA_DIR / "huggingface_eda.json")
    return out


def eda_events_csv(save: bool = True) -> dict:
    df = dl.load_events_csv()
    out = {
        "source": "Events.csv - Irish events listing (URLs point to Irish venues, County column = Irish counties)",
        "rows": len(df), "columns": list(df.columns),
        "memory_mb": round(df.memory_usage(deep=True).sum() / 1e6, 1),
        "duplicate_rows": int(df.duplicated().sum()),
        "unique_names": int(df["Name"].nunique()),
        "unique_descriptions": int(df["Description"].nunique()),
        "event_type_values": df["Event Type"].value_counts().to_dict(),
        "county_top": df["County"].value_counts().head(8).to_dict(),
        "description": text_summary(df["Description"]),
    }
    if save:
        structural_summary(df).to_csv(EDA_DIR / "events_csv_structure.csv")
        plot_missing(df, "Events.csv - missing values", EDA_DIR / "events_csv_missing.png")
        save_json(out, EDA_DIR / "events_csv_eda.json")
    return out


def eda_mendeley(save: bool = True) -> dict:
    files = dl.load_mendeley()
    out = {"source": "Mendeley Data DOI 10.17632/g2sdzmssgh.2 (life-event narratives generated by an AI model)",
           "files": {k: {"rows": len(v), "columns": list(v.columns)} for k, v in files.items()}}
    texts = [v[c] for v in files.values() for c in ("TEXT", "ABSTRACT") if c in v.columns]
    if texts:
        s = pd.concat(texts)
        out["event_kinds"] = sorted(set(re.findall(r"\[Event: ([a-z]+)\]", " ".join(s.astype(str)))))
        out["labels"] = sorted({str(x) for v in files.values() for c in ("CLASSIFICATION", "INCLUDE")
                                if c in v.columns for x in v[c].dropna().unique()})
        out["text"] = text_summary(s)
        out["contains_persona_attributes"] = bool(s.str.contains("Gender|Income|MINORITY", regex=True).any())
    if save:
        save_json(out, EDA_DIR / "mendeley_eda.json")
    return out


def dataset_size_comparison(results: dict, save: bool = True):
    sizes = pd.Series({
        "DATAtourisme (with description)": results["datatourisme"]["description"]["non_null"],
        "Hugging Face": results["huggingface"]["rows"],
        "Events.csv (unique desc.)": results["events_csv"]["unique_descriptions"],
        "Mendeley (human-tagged orig.)": sum(v["rows"] for k, v in results["mendeley"]["files"].items()
                                             if k.startswith("human_tagged_original")),
    }).sort_values(ascending=False)
    if save:
        plot_bar_counts(sizes, "Usable text records per source", EDA_DIR / "dataset_sizes.png", xlabel="records")
    return sizes


def run_all(save: bool = True) -> dict:
    avail = dl.available_sources()
    res = {}
    if avail["datatourisme"]:
        res["datatourisme"] = eda_datatourisme(save)
    if avail["huggingface"]:
        res["huggingface"] = eda_huggingface(save)
    if avail["events_csv"]:
        res["events_csv"] = eda_events_csv(save)
    if avail["mendeley"]:
        res["mendeley"] = eda_mendeley(save)
    if len(res) == 4:
        dataset_size_comparison(res, save)
    return res
