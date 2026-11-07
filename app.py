"""EventGen - Streamlit demo.

    streamlit run app.py

Generates a French event description from (title, event type) with the trained
baseline and attention encoder-decoders, compares them side by side, shows the
attention weights, explores unseen test examples and displays the experiment results.
"""
from __future__ import annotations

import json
import random

import pandas as pd
import streamlit as st

from src import config as C
from src.config import GenerationConfig
from src.data_loader import TYPE_FR
from src.evaluation import rouge_scores
from src.preprocessing import serialize_event, tokenize

st.set_page_config(page_title="EventGen", page_icon="✨", layout="wide", initial_sidebar_state="expanded")

# ---------------------------------------------------------------------------- style
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"], .stMarkdown, .stTextInput, .stButton { font-family: 'Inter', sans-serif; }
.block-container { padding-top: 3.2rem; max-width: 1250px; }
.hero { background: radial-gradient(1200px 300px at 0% 0%, #a78bfa 0%, transparent 60%),
        linear-gradient(120deg, #1e1b4b 0%, #4c1d95 55%, #7c3aed 100%);
        border-radius: 22px; padding: 30px 34px; color: #fff; margin-bottom: 18px;
        box-shadow: 0 18px 40px -18px rgba(76,29,149,.55); }
.hero h1 { font-size: 2.3rem; font-weight: 800; margin: 0 0 6px 0; color: #fff; letter-spacing: -.02em; }
.hero p { margin: 0; opacity: .88; font-size: 1.02rem; }
.pill { display:inline-block; background: rgba(255,255,255,.14); border: 1px solid rgba(255,255,255,.25);
        padding: 3px 11px; border-radius: 999px; font-size: .78rem; margin: 12px 6px 0 0; }
.card { background: #ffffff; border: 1px solid #ece9f7; border-radius: 18px; padding: 20px 22px;
        box-shadow: 0 6px 22px -14px rgba(30,27,75,.35); height: 100%; }
.card h4 { margin: 0 0 4px 0; font-size: .82rem; text-transform: uppercase; letter-spacing: .08em; color:#6d28d9; }
.card .model { font-size: .78rem; color: #64748b; margin-bottom: 10px; }
.card .gen { font-size: 1.06rem; line-height: 1.65; color: #1e1b4b; }
.card.ref { background: #f8fafc; border-style: dashed; }
.card.ref .gen { color:#334155; }
.kpi { background:#fff; border:1px solid #ece9f7; border-radius:16px; padding:14px 16px; }
.kpi .v { font-size:1.55rem; font-weight:800; color:#1e1b4b; }
.kpi .l { font-size:.76rem; color:#64748b; text-transform:uppercase; letter-spacing:.06em; }
.tag { display:inline-block; background:#f3e8ff; color:#6d28d9; border-radius:8px; padding:2px 8px;
       font-size:.75rem; margin:2px 4px 2px 0; font-family: ui-monospace, monospace; }
.tag.unk { background:#fee2e2; color:#b91c1c; }
.muted { color:#64748b; font-size:.85rem; }
div.stButton > button[kind="primary"] { background: linear-gradient(90deg,#6d28d9,#7c3aed); border:0;
       border-radius: 12px; padding: .55rem 1.3rem; font-weight: 600; }
.stTabs [data-baseweb="tab-list"] { gap: 6px; }
.stTabs [data-baseweb="tab"] { border-radius: 10px 10px 0 0; padding: 8px 16px; }
</style>
""", unsafe_allow_html=True)

MODEL_LABELS = {"baseline": "LSTM Encoder–Decoder (baseline)", "attention": "LSTM + Bahdanau attention"}
TYPE_CHOICES = sorted(set(TYPE_FR.values()))
EXAMPLES = [
    ("Concert de jazz au jardin", ["concert", "musique"]),
    ("Marché de Noël artisanal", ["marché", "vente"]),
    ("Atelier cuisine pour les enfants", ["atelier", "jeune public"]),
    ("Exposition de peintures contemporaines", ["exposition", "arts visuels"]),
    ("Randonnée nocturne aux flambeaux", ["randonnée", "événement sportif"]),
    ("Vide-grenier du printemps", ["vide-grenier", "vente"]),
]


# ---------------------------------------------------------------------------- loading
def available_models() -> list[str]:
    if not C.MODELS_DIR.exists():
        return []
    return sorted(d.name for d in C.MODELS_DIR.iterdir() if (d / "best.pt").exists())


@st.cache_resource(show_spinner="Loading model…")
def get_generator(name: str):
    from src.inference import EventGenerator
    return EventGenerator(C.MODELS_DIR / name, device="cpu")


@st.cache_data
def load_test() -> pd.DataFrame | None:
    return pd.read_csv(C.SPLIT_FILES["test"]) if C.SPLIT_FILES["test"].exists() else None


def esc(s: str) -> str:
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def card(title: str, subtitle: str, text: str, extra: str = "", ref: bool = False):
    st.markdown(f"<div class='card{' ref' if ref else ''}'><h4>{esc(title)}</h4><div class='model'>{esc(subtitle)}</div>"
                f"<div class='gen'>{esc(text) or '<i>(empty)</i>'}</div>{extra}</div>", unsafe_allow_html=True)


def kpi(col, value, label):
    col.markdown(f"<div class='kpi'><div class='v'>{value}</div><div class='l'>{esc(label)}</div></div>",
                 unsafe_allow_html=True)


# ---------------------------------------------------------------------------- sidebar
models = available_models()
with st.sidebar:
    st.markdown("### ⚙️ Decoding")
    method = st.radio("Strategy", ["greedy", "beam"], index=1, horizontal=True,
                      help="Greedy: argmax at each step. Beam: keeps the k best partial sentences.")
    beam_width = st.slider("Beam width", 2, 8, 3, disabled=method != "beam")
    max_len = st.slider("Max output tokens", 10, 80, 60)
    no_repeat = st.select_slider("Block repeated n-grams", options=[0, 2, 3, 4], value=3,
                                 help="0 = off. Forbids generating an n-gram twice (reduces loops).")
    gen_cfg = GenerationConfig(max_len=max_len, beam_width=beam_width, no_repeat_ngram=no_repeat,
                               length_penalty=1.0, block_unk=True)
    st.markdown("### 🧠 Models")
    shown = st.multiselect("Compare", models, default=[m for m in models if m in ("baseline", "attention")] or models)
    if not models:
        st.error("No trained model in `models/`.\n\nRun `python scripts/03_train.py --model baseline` "
                 "and `--model attention` (or the Colab notebook) first.")
    st.markdown("---")
    st.caption("EventGen · PyTorch encoder–decoder trained from scratch on DATAtourisme (French events). "
               "No pretrained language model is used.")

st.markdown("""
<div class="hero">
  <h1>✨ EventGen</h1>
  <p>From an event's title and type to a French description, generated token by token by an LSTM
     encoder–decoder trained from scratch.</p>
  <span class="pill">PyTorch</span><span class="pill">LSTM Encoder–Decoder</span>
  <span class="pill">Bahdanau attention</span><span class="pill">Greedy &amp; beam search</span>
  <span class="pill">DATAtourisme · 32k pairs</span>
</div>
""", unsafe_allow_html=True)

tab_gen, tab_test, tab_res, tab_how = st.tabs(["🪄 Generate", "🔍 Unseen test events", "📊 Results", "🏗️ How it works"])

# ---------------------------------------------------------------------------- generate
with tab_gen:
    if "title" not in st.session_state:
        st.session_state.title, st.session_state.types = EXAMPLES[0][0], EXAMPLES[0][1]
    st.markdown("<span class='muted'>Try an example:</span>", unsafe_allow_html=True)
    ex_cols = st.columns(3)
    for k, (t, ty) in enumerate(EXAMPLES):
        col = ex_cols[k % 3]
        if col.button(t, use_container_width=True, key=f"ex_{t}"):
            st.session_state.title, st.session_state.types = t, ty
    c1, c2 = st.columns([3, 2])
    title = c1.text_input("Event title (titre)", key="title", placeholder="e.g. Festival de musique baroque")
    types = c2.multiselect("Event type(s)", TYPE_CHOICES, key="types",
                           help="Labels derived from the DATAtourisme ontology. Empty = 'non précisé'.")
    go = st.button("Generate description", type="primary", disabled=not (models and shown and title.strip()))

    if go:
        src_text = serialize_event(title.strip(), types)
        results = {}
        for name in shown:
            g = get_generator(name)
            results[name] = g.generate_from_text(src_text, method=method, gen=gen_cfg)
        cols = st.columns(len(results))
        for col, (name, r) in zip(cols, results.items()):
            with col:
                kind = name.split("_")[0]
                card(name, f"{MODEL_LABELS.get(kind, name)} · {method}", r.text,
                     f"<div class='muted' style='margin-top:10px'>{len(r.tokens)} tokens</div>")
        first = next(iter(results.values()))
        with st.expander("Model input: serialisation, tokens, unknown words", expanded=False):
            st.code(src_text, language=None)
            vocab = get_generator(next(iter(results))).src_vocab.word2idx
            st.markdown(" ".join(f"<span class='tag{'' if t in vocab else ' unk'}'>{esc(t)}</span>"
                                 for t in first.source_tokens), unsafe_allow_html=True)
            if first.unknown_source_tokens:
                st.caption(f"🔴 {len(first.unknown_source_tokens)} word(s) unseen in training → mapped to <unk>.")
        att = {n: r for n, r in results.items() if r.attention is not None and r.tokens}
        if att:
            from src.visualization import plot_attention
            with st.expander("Attention heatmap α(t, i)", expanded=True):
                st.caption("Each row is a generated word; each column a source token. Darker = the decoder "
                           "looked more at that input token when producing the word. Attention weights are "
                           "an indication of what the model uses, not a full explanation.")
                for n, r in att.items():
                    fig = plot_attention(r.attention, r.source_tokens, r.tokens + ["<eos>"], title=n)
                    st.pyplot(fig, use_container_width=True)

# ---------------------------------------------------------------------------- test explorer
with tab_test:
    test = load_test()
    if test is None:
        st.info("Test split not found. Run `python scripts/02_prepare_data.py`.")
    elif not models:
        st.info("Train a model first.")
    else:
        st.markdown("<span class='muted'>These events were never seen during training. The reference "
                    "description is shown only for comparison: it is not given to the model.</span>",
                    unsafe_allow_html=True)
        if "test_idx" not in st.session_state:
            st.session_state.test_idx = 0
        a, b, _ = st.columns([1, 1, 4])
        if a.button("🎲 Random event", use_container_width=True):
            st.session_state.test_idx = random.randrange(len(test))
        idx = b.number_input("Index", 0, len(test) - 1, key="test_idx", label_visibility="collapsed")
        row = test.iloc[int(idx)]
        st.code(row["input_text"], language=None)
        ref_toks = tokenize(row["target_text"])
        cols = st.columns(1 + len(shown))
        with cols[0]:
            card("Reference", "human-written (DATAtourisme)", row["target_text"], ref=True)
        for col, name in zip(cols[1:], shown):
            r = get_generator(name).generate_from_text(row["input_text"], method=method, gen=gen_cfg)
            sc = rouge_scores(r.tokens, ref_toks)
            with col:
                card(name, f"{method} decoding", r.text,
                     f"<div class='muted' style='margin-top:10px'>ROUGE-L {100 * sc['rougeL']:.1f} · "
                     f"ROUGE-1 {100 * sc['rouge1']:.1f}</div>")

# ---------------------------------------------------------------------------- results
with tab_res:
    rep_path = C.CLEANING_REPORT
    if rep_path.exists():
        rep = json.loads(rep_path.read_text(encoding="utf-8"))
        k = st.columns(5)
        kpi(k[0], f"{rep['cleaning']['initial_rows']:,}", "raw DATAtourisme rows")
        kpi(k[1], f"{rep['pairs']['rows_out']:,}", "clean (input, target) pairs")
        kpi(k[2], f"{rep['split']['train']['rows']:,} / {rep['split']['val']['rows']:,} / {rep['split']['test']['rows']:,}",
            "train / val / test")
        kpi(k[3], f"{rep['vocab']['src']['size']:,}", "source vocabulary")
        kpi(k[4], f"{rep['vocab']['tgt']['size']:,}", "target vocabulary")
        st.write("")
    cmp_path = C.METRICS_DIR / "comparison.csv"
    if cmp_path.exists():
        t = pd.read_csv(cmp_path)
        cols = ["model", "decoding", "n_test", "bleu", "rouge1", "rouge2", "rougeL", "perplexity", "token_acc",
                "repetition_rate", "distinct2", "title_coverage", "avg_gen_len", "n_params", "train_time_min"]
        st.markdown("#### Test-set metrics (computed by `scripts/04_evaluate.py`)")
        st.dataframe(t[[c for c in cols if c in t.columns]].round(3), use_container_width=True, hide_index=True)
    else:
        st.info("No evaluation yet: run `python scripts/04_evaluate.py`.")
    figs = [("learning_curves.png", "Learning curves"), ("metric_comparison.png", "Metric comparison")]
    figs += [(p.name, p.stem.replace("_", " ")) for p in sorted(C.FIGURES_DIR.glob("attention_*.png"))[:3]]
    for fname, cap in figs:
        p = C.FIGURES_DIR / fname
        if p.exists():
            st.image(str(p), caption=cap, use_container_width=True)
    err = C.METRICS_DIR / "error_rates.csv"
    if err.exists():
        st.markdown("#### Failure types (% of test outputs, `scripts/05_error_analysis.py`)")
        st.dataframe(pd.read_csv(err), use_container_width=True, hide_index=True)

# ---------------------------------------------------------------------------- how it works
with tab_how:
    st.graphviz_chart("""
    digraph G { rankdir=LR; bgcolor="transparent";
      node [shape=box style="rounded,filled" fontname="Inter" fontsize=11 color="#c4b5fd" fillcolor="#f5f3ff"];
      edge [color="#7c3aed"];
      in [label="type : concert | titre : …"]; tok [label="normalise +\\ntokenise"]; ids [label="word2idx\\n(<unk>)"];
      emb [label="Embedding\\n128-d"]; enc [label="LSTM encoder\\n256-d"];
      ctx [label="(h_S, c_S)\\nbaseline context" fillcolor="#ede9fe"];
      att [label="Bahdanau attention\\nc(t)=Σ α(t,i) h_i" fillcolor="#ddd6fe"];
      dec [label="LSTM decoder\\n<sos> → … → <eos>"]; lin [label="Linear + softmax\\nP(y_t | y_<t, X)"];
      out [label="greedy / beam\\n→ description"];
      in -> tok -> ids -> emb -> enc -> ctx -> dec; enc -> att [style=dashed]; att -> dec [style=dashed];
      dec -> lin -> out; lin -> dec [label=" y_t fed back" fontsize=9 style=dotted];
    }""", use_container_width=True)
    st.markdown("""
**Task.** Conditional generation P(Y | X): X = event type labels + title (serialised), Y = the event
description published on DATAtourisme (French, ≤ 60 tokens).

**Baseline.** The encoder's final hidden and cell states are the *only* information the decoder gets
about the input (fixed-size context vector).

**Attention.** At every step the decoder scores all encoder states,
e(t,i) = vᵀ tanh(W_h h_i + W_s s_{t-1}), normalises them with a softmax into α(t,i), and reads
c(t) = Σ α(t,i) h_i, so it can copy information (e.g. words of the title) from any input position.

**Training.** Token-level cross-entropy (PAD ignored), Adam (lr 1e-3), teacher forcing 0.5,
gradient clipping 1.0, early stopping on validation loss.

**Inference.** No reference is used: the decoder starts from `<sos>` and feeds back its own predictions
until `<eos>` or the maximum length. `<unk>` is never emitted.
""")
