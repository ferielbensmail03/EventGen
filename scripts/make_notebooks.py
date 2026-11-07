"""Generates the notebooks in notebooks/ (kept in a script so they stay in sync with src/)."""
from pathlib import Path

import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
NB = ROOT / "notebooks"
SETUP = """import sys, os
from pathlib import Path
ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
sys.path.insert(0, str(ROOT)); os.chdir(ROOT)
import pandas as pd, numpy as np, matplotlib.pyplot as plt, json
pd.set_option("display.max_colwidth", 160); pd.set_option("display.width", 200)
%matplotlib inline"""


def md(s):
    return nbf.v4.new_markdown_cell(s.strip())


def code(s):
    return nbf.v4.new_code_cell(s.strip())


def write(name, cells):
    nb = nbf.v4.new_notebook()
    nb["cells"] = cells
    nb["metadata"]["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
    NB.mkdir(exist_ok=True)
    nbf.write(nb, NB / name)
    print("wrote", name)


# ============================================================================ 00 Colab
write("00_colab_run_all.ipynb", [
    md("""# EventGen - full pipeline on Colab / Kaggle (GPU)
Runtime ▸ Change runtime type ▸ **T4 GPU**. Upload `EventGen.zip` (the project folder) to the session
or to Google Drive, then run the cells in order. Every step is a script of `scripts/`, so the
notebook and the command line give identical results."""),
    code("""# Option A: zip uploaded to the Colab session
!unzip -q -o /content/EventGen.zip -d /content/ && echo unzipped
# Option B: from Google Drive
# from google.colab import drive; drive.mount('/content/drive')
# !unzip -q -o /content/drive/MyDrive/EventGen.zip -d /content/
%cd /content/EventGen
!pip -q install -r requirements.txt
import torch; print("GPU:", torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else "")"""),
    md("## 1. EDA of every source and 2. cleaning → pairs → split → vocabularies"),
    code("!python scripts/01_eda.py | tail -5\n!python scripts/02_prepare_data.py"),
    md("""## 3. Training (E1 baseline, E2 attention)
Same data, same embedding/hidden sizes, same optimiser, same teacher-forcing ratio and the same
early-stopping rule for both models. On a T4 one epoch takes about 1-2 min; `--max_minutes` is a safety net."""),
    code("!python scripts/03_train.py --model baseline --epochs 30 --max_minutes 60"),
    code("!python scripts/03_train.py --model attention --epochs 30 --max_minutes 80"),
    md("""### Optional - teacher-forcing study (0.0 / 1.0, attention model)
Results land in `models/attention_tf0.0` and `models/attention_tf1.0` and are evaluated automatically."""),
    code("RUN_TF_STUDY = False\nif RUN_TF_STUDY:\n"
         "    !python scripts/03_train.py --model attention --tf 0.0 --tag tf0.0 --epochs 15 --max_minutes 40\n"
         "    !python scripts/03_train.py --model attention --tf 1.0 --tag tf1.0 --epochs 15 --max_minutes 40"),
    md("## 4. Evaluation on the test split (E3 greedy, E4 beam) and 5. error analysis"),
    code("!python scripts/04_evaluate.py\n!python scripts/05_error_analysis.py"),
    code("import pandas as pd\npd.read_csv('results/metrics/comparison.csv').round(3)"),
    md("## 6. Download the trained models and results (to run the Streamlit app locally)"),
    code("!zip -q -r /content/eventgen_trained.zip models artifacts results data/splits data/processed/cleaning_report.json\n"
         "from google.colab import files; files.download('/content/eventgen_trained.zip')"),
])

# ============================================================================ 01 EDA
write("01_dataset_inventory_eda.ipynb", [
    md("""# 01 - Dataset inventory and exploratory analysis
Every number below is computed from the raw files (`src/eda.py`). Raw files are only read."""),
    code(SETUP + "\nfrom src import eda, data_loader as dl\nfrom src.config import EDA_DIR\nprint(dl.available_sources())"),
    md("## A. DATAtourisme (data.gouv.fr) - French tourism events"),
    code("raw = dl.load_datatourisme()\nprint(raw.shape)\neda.structural_summary(raw)"),
    code("raw.head(5)"),
    code("dec = dl.decode_datatourisme(raw)\ndec[['title','type_labels','description']].sample(5, random_state=1)"),
    code("dt = eda.eda_datatourisme(save=True)\n{k: v for k, v in dt.items() if k not in ('columns',)}"),
    md("""**Reading.** 13 of the 17 columns (theme, dates, address, city, coordinates, contacts, lastupdate)
are **100 % empty** in this extract: only `id`, `label` (title), `type` (ontology path) and `comment`
(description) carry information. Descriptions are French, short (median ≈ 26 words) and real
(written by tourist offices). This limits the input to *title + event type*."""),
    code("from IPython.display import Image, display\nfor f in ['datatourisme_missing','datatourisme_types','datatourisme_lengths','datatourisme_words']:\n    display(Image(EDA_DIR / f'{f}.png'))"),
    md("## B. Hugging Face `eliel2003/events`"),
    code("hf = dl.load_huggingface(); print(hf.shape)\ndisplay(eda.structural_summary(hf))\nprint(hf.event_narrative.iloc[0][:800])"),
    code("eda.eda_huggingface(save=True)"),
    md("""**Reading.** Clean and complete, with rich structured fields, but **synthetic** (LLM-generated)
and only 3 000 rows. The narratives are *post-event reports* in markdown (Objective / Execution
highlights / Outcome), not promotional descriptions, and long (~104 words) for an LSTM decoder."""),
    md("## C. Events.csv (Irish events)"),
    code("ev = dl.load_events_csv(); print(ev.shape)\ndisplay(eda.structural_summary(ev))\neda.eda_events_csv(save=True)"),
    md("""**Reading.** English, real descriptions, but each event is repeated once per date: only
≈ 900 unique descriptions remain, which is too few to train a seq2seq model from scratch.
It also contains contact phone numbers and URLs."""),
    md("## D. Mendeley (DOI 10.17632/g2sdzmssgh.2)"),
    code("men = eda.eda_mendeley(save=True)\nmen"),
    code("files = dl.load_mendeley(); k = next(iter(files)); print(k)\nprint(files[k].iloc[0, 0][:1200])"),
    md("""**Reading.** Life-event narratives (hiring, firing, birth, death) written by an AI model for
simulated personas, plus human/AI *classification* labels ("does the narrative match the prompt?").
They are not organised events, the labels are classification targets (not generation targets) and the
prompts contain sensitive persona attributes (gender, minority group, income). **Excluded.**"""),
    md("## Size comparison and decision"),
    code("res = eda.run_all(save=False)\nsizes = eda.dataset_size_comparison(res, save=True)\nsizes"),
    code("display(Image(EDA_DIR / 'dataset_sizes.png'))"),
    md("""| Canonical field | DATAtourisme | Hugging Face | Events.csv | Mendeley |
|---|---|---|---|---|
| Event name | `label` | - (only `event_id`) | `Name` | - |
| Event type | `type` (ontology path) | `event_type` | `Event Type` (3 values) | life event kind |
| Location | empty | `city` (Israel) | `Venue Name`, `County` | persona location |
| Date | empty | `month`, `year`, `season` | `Start Date` | - |
| Audience / objective / tone | - | - | - | - |
| Description | `comment` (FR, real) | `event_narrative` (EN, synthetic) | `Description` (EN) | AI-generated narrative |
| Language | French | English | English | English |

**Decision.** Primary dataset: **DATAtourisme** (largest real corpus, short targets suited to an LSTM,
a single language). Hugging Face, Events.csv and Mendeley are **not merged**: different languages,
writing styles (report vs. promotion vs. personal post) and input schemas would make P(Y|X) incoherent.
`evenements.csv.gz` is another extract of the same DATAtourisme feed (same schema, most ids shared) and is
not needed."""),
])

# ============================================================================ 02 cleaning
write("02_cleaning_pairs_split.ipynb", [
    md("# 02 - Cleaning, (input, target) construction and leakage-safe split"),
    code(SETUP + "\nfrom src import config as C\nfrom src.data_loader import load_datatourisme\n"
         "from src.data_cleaning import clean_datatourisme, clean_text\n"
         "from src.pairs import build_pairs, group_split, split_report"),
    md("## Text cleaning, one function applied to titles and descriptions"),
    code("""samples = ["<p>Concert &amp; dégustation !!!</p> Infos : www.mairie.fr / 06 12 34 56 78",
           "Les Débhordeurs de la cie BROUN\\\\u00cfAK.Venez nombreux 🎉🎉",
           "Réservation : www\\\\.domaine\\\\-citadelle\\\\.com. Dès 12 ans"]
for s in samples: print(repr(s), "\\n ->", clean_text(s), "\\n")"""),
    md("""Removed: HTML tags/entities, URLs, e-mails and phone numbers (no information for generation and
personal contact data), emojis and control characters, literal `\\uXXXX` escapes (an encoding problem found
in the EDA), markdown escapes, repeated punctuation and line breaks. Kept: accents, case, punctuation and
sentence structure."""),
    code("clean, rep = clean_datatourisme(load_datatourisme())\npd.DataFrame(rep['steps'])"),
    code("print('initial', rep['initial_rows'], '-> final', rep['final_rows'])\nprint('empty columns dropped:', rep['empty_columns_dropped'])\nprint('rows with corrupted / generic type kept (input = \"non précisé\"):', rep['corrupted_type_rows_kept'])"),
    md("""## Pairs
* **input_text** = `type : <labels> | titre : <title>`: the structured fields that really exist.
* **target_text** = the event's own description (same record, so no join can mismatch them).
* Targets shorter than 8 tokens are dropped; longer than 60 tokens are cut at the **last sentence
  end** inside the window (never mid-sentence)."""),
    code("cfg = C.DataConfig()\npairs, prep = build_pairs(clean, cfg)\nprep"),
    code("pairs[['input_text','target_text']].sample(10, random_state=3)"),
    code("fig, ax = plt.subplots(1, 2, figsize=(11, 3.2))\npairs.source_tokens.hist(bins=40, ax=ax[0]); ax[0].set_title('input tokens')\n"
         "pairs.target_tokens.hist(bins=40, ax=ax[1]); ax[1].set_title('target tokens (after cut)')\nplt.show()"),
    md("""## Group split 80 / 10 / 10
Records sharing a **title** (a recurring show) or the **same first 12 description tokens**
(templates, near-duplicates) are linked; each connected group goes entirely to one split, so the test
set contains no recycled description."""),
    code("splits = group_split(pairs, cfg)\nsplit_report(splits)"),
])

# ============================================================================ 03 preprocessing
write("03_preprocessing_vocab_embeddings.ipynb", [
    md("# 03 - Normalisation, tokenisation, vocabulary, padding and embeddings"),
    code(SETUP + "\nimport torch\nfrom src import config as C\nfrom src.preprocessing import normalize, tokenize, detokenize\n"
         "from src.vocabulary import Vocabulary\nfrom src.dataset import EventDataset, collate"),
    md("""## Normalisation + tokenisation
* Unicode NFC, typographic apostrophes/quotes → ASCII (`’` → `'`), whitespace collapsed.
* **Lower-casing**: yes, to avoid splitting the vocabulary (Concert / concert); outputs are re-capitalised for display.
* Punctuation becomes separate tokens; French elisions are split (`l'atelier` → `l'` `atelier`);
  hyphenated words and numbers stay whole (`vide-grenier`, `14h30`, `2,5`)."""),
    code("""for s in ["Join l’atelier aujourd’hui, à 14h30 !", "Vide-grenier (entrée : 2,5 €)..."]:
    t = tokenize(s); print(s, "\\n  ->", t, "\\n  <-", detokenize(t))"""),
    code("train = pd.read_csv(C.SPLIT_FILES['train']); test = pd.read_csv(C.SPLIT_FILES['test'])\n"
         "for i in range(3):\n    print('RAW :', train.target_text[i]); print('PREP:', tokenize(train.target_text[i])); print()"),
    md("## Vocabularies (built on the TRAINING split only)"),
    code("src_v = Vocabulary.load(C.SRC_VOCAB_FILE); tgt_v = Vocabulary.load(C.TGT_VOCAB_FILE)\n"
         "print('source vocab', len(src_v), '| target vocab', len(tgt_v))\nprint(src_v.idx2word[:12]); print(tgt_v.stats()['top_20'])"),
    code("for name, df in [('train', train), ('test', test)]:\n"
         "    print(name, 'target coverage (share of tokens known):', round(tgt_v.coverage(tokenize(t) for t in df.target_text), 4))"),
    code("freqs = pd.Series(tgt_v.freqs).sort_values(ascending=False).values\nplt.figure(figsize=(6,3)); plt.loglog(range(1, len(freqs)+1), freqs)\n"
         "plt.axhline(tgt_v.min_freq, color='r', ls='--', label=f'min_freq={tgt_v.min_freq}')\nplt.title('Zipf curve of target words (train)'); plt.xlabel('rank'); plt.ylabel('frequency'); plt.legend(); plt.show()"),
    md("""Special tokens: `<pad>`=0 fills batches (ignored by the loss, masked in attention), `<unk>`=1 replaces
words below `min_freq` or unseen, `<sos>`=2 starts decoding, `<eos>`=3 ends it."""),
    md("## Numerical encoding, padding and masks"),
    code("ds = EventDataset(train.head(4), src_v, tgt_v, 40, 60)\nprint(train.input_text[0]); print(ds.src[0])\nprint([src_v.idx2word[i] for i in ds.src[0]])\n"
         "src, src_len, tgt, _ = collate([ds[i] for i in range(4)])\nprint('src', tuple(src.shape), 'lengths', src_len.tolist()); print(src)\nprint('mask (True = real token)'); print(src != 0)"),
    md("""## Embeddings
A token id is an arbitrary integer: id 812 is not "closer" to 813 than to 5. `nn.Embedding(V, 128)` is a
learnable V×128 matrix whose row *i* is the dense vector of word *i*; it is updated by backpropagation like
any weight, so words used in similar contexts end up with similar vectors. `padding_idx=0` keeps the
`<pad>` vector at zero."""),
    code("emb = torch.nn.Embedding(len(src_v), 128, padding_idx=0)\nx = emb(src)\nprint('ids', tuple(src.shape), '-> vectors', tuple(x.shape)); print('pad vector norm:', emb.weight[0].norm().item())"),
    code("""from src.training import load_model
import torch.nn.functional as F
if (C.MODELS_DIR / 'attention' / 'best.pt').exists():
    m, _ = load_model(C.MODELS_DIR / 'attention', 'cpu'); E = m.decoder.embedding.weight.detach()
    for w in ['concert', 'marché', 'enfants', 'randonnée']:
        if w in tgt_v.word2idx:
            sims = F.cosine_similarity(E[tgt_v.word2idx[w]].unsqueeze(0), E)
            print(w, '->', [tgt_v.idx2word[i] for i in sims.topk(7).indices.tolist()[1:]])"""),
])

# ============================================================================ 04 models + training
write("04_models_training.ipynb", [
    md("# 04 - Encoder-decoder architectures, teacher forcing and training"),
    code(SETUP + "\nimport torch\nfrom src import config as C\nfrom src.seq2seq import build_model\nfrom src.utils import count_parameters\n"
         "from src.vocabulary import Vocabulary\nsrc_v = Vocabulary.load(C.SRC_VOCAB_FILE); tgt_v = Vocabulary.load(C.TGT_VOCAB_FILE)"),
    md("""## Architectures
**E1 baseline**: Embedding(128) → LSTM encoder(256) → (h_S, c_S) initialises → LSTM decoder(256) → Linear → softmax.
The whole input is squeezed into one fixed-size state: long or information-rich inputs get compressed.

**E2 attention**: same encoder; at every decoder step Bahdanau attention computes
e(t,i) = vᵀ tanh(W_h h_i + W_s s_{t−1}), α(t,i) = softmax_i e(t,i), c(t) = Σ_i α(t,i) h_i;
the LSTM input is [emb(y_{t−1}); c(t)] and the output layer sees [s_t; c(t); emb(y_{t−1})]."""),
    code("for kind in ['baseline', 'attention']:\n    cfg = C.ModelConfig(model_type=kind)\n    m = build_model(cfg, len(src_v), len(tgt_v))\n"
         "    print(f'{kind:<10} {count_parameters(m):>12,} parameters'); print(m, '\\n')"),
    md("## Tensor shapes through one forward pass"),
    code("""from src.dataset import EventDataset, collate
train = pd.read_csv(C.SPLIT_FILES['train']).head(8)
ds = EventDataset(train, src_v, tgt_v, 40, 60); src, src_len, tgt, _ = collate([ds[i] for i in range(8)])
m = build_model(C.ModelConfig(model_type='attention'), len(src_v), len(tgt_v)).eval()
enc_out, (h, c) = m.encoder(src, src_len)
print('src', tuple(src.shape), '| encoder outputs', tuple(enc_out.shape), '| h', tuple(h.shape), '| c', tuple(c.shape))
logits, attn = m(src, src_len, tgt, teacher_forcing=1.0, return_attention=True)
print('target', tuple(tgt.shape), '-> logits', tuple(logits.shape), '| attention', tuple(attn.shape))
print('attention rows sum to 1:', torch.allclose(attn.sum(-1), torch.ones_like(attn.sum(-1))))"""),
    md("""## Teacher forcing
At step t the next decoder input is the **ground-truth** y_t with probability `teacher_forcing`
(0.5 here), otherwise the model's own prediction. With 1.0 training is fast and stable but the model never
sees its own mistakes (**exposure bias**); with 0.0 it trains exactly as it will generate but learns
slowly at first. At inference there is no reference, so generated tokens are always fed back.

## Loss and optimiser
Cross-entropy per non-pad token: L = −(1/N) Σ log P(y_t | y_<t, X) (`ignore_index=<pad>`). Adam (lr 1e-3)
updates each parameter with adaptive, momentum-smoothed steps from the gradients obtained by
backpropagation through time; gradients are clipped to norm 1.0; LR halved when the validation loss
plateaus; early stopping after 4 epochs without improvement; best checkpoint saved.

## Training
Training is done by `scripts/03_train.py` (or `00_colab_run_all.ipynb` on GPU). Set `TRAIN = True` to
retrain from here."""),
    code("TRAIN = False\nif TRAIN:\n    from src.config import ExperimentConfig\n    from src.training import train_model\n"
         "    for kind in ['baseline', 'attention']:\n        cfg = ExperimentConfig(); cfg.model.model_type = kind\n        print(train_model(cfg))"),
    code("""from src.visualization import plot_learning_curves
hist = {d.name: pd.read_csv(d / 'history.csv') for d in sorted(C.MODELS_DIR.iterdir()) if (d / 'history.csv').exists()}
for k, h in hist.items(): print(k); display(h.round(3))
if hist: plot_learning_curves(hist); plt.show()"""),
    code("""summ = {d.name: json.load(open(d / 'train_summary.json', encoding='utf-8')) for d in sorted(C.MODELS_DIR.iterdir()) if (d / 'train_summary.json').exists()}
pd.DataFrame(summ).T[['n_params','best_epoch','epochs_run','best_val_loss','best_val_ppl','train_time_s','device','train_size']]"""),
    md("""**How to read the curves.** Train and validation losses both decreasing = still learning (more epochs
could help). Validation loss rising while training loss keeps falling = overfitting: early stopping keeps the
best epoch. Both high and flat = underfitting (capacity or learning-rate problem). Note that the training loss
is measured with teacher forcing 0.5 and the validation loss with 1.0, so they are not on exactly the same footing."""),
])

# ============================================================================ 05 evaluation
write("05_inference_evaluation_errors.ipynb", [
    md("# 05 - Inference, decoding strategies, evaluation and error analysis"),
    code(SETUP + "\nfrom src import config as C\nfrom src.inference import EventGenerator\nfrom src.visualization import plot_attention\n"
         "models = [d.name for d in sorted(C.MODELS_DIR.iterdir()) if (d / 'best.pt').exists()]\nprint(models)\n"
         "gens = {m: EventGenerator(C.MODELS_DIR / m, 'cpu') for m in models}"),
    md("""## Inference on new events (no reference available)
title + types → serialise → normalise → tokenise → ids → encoder → `<sos>` → predict → feed back → … → `<eos>`."""),
    code("""events = [("Concert de jazz au jardin", ["concert", "musique"]), ("Marché de Noël artisanal", ["marché", "vente"]),
          ("Atelier cuisine pour les enfants", ["atelier", "jeune public"])]
for title, types in events:
    print('INPUT:', title, types)
    for m, g in gens.items():
        for method in ['greedy', 'beam']:
            print(f'  {m:<10} {method:<6}', g.generate(title, types, method).text)
    print()"""),
    md("""## Greedy vs beam search
Greedy: y_t = argmax P(y_t | y_<t, X): fast but locally optimal. Beam (width 3) keeps the 3 partial
sentences with the highest cumulative log-probability Σ log P; hypotheses ending in `<eos>` are set aside, and
the final choice is normalised by length ((5+|y|)/6)^0.7 so short outputs are not favoured unfairly."""),
    code("""test = pd.read_csv(C.SPLIT_FILES['test'])
for i in [0, 7, 21]:
    r = test.iloc[i]; print('INPUT    :', r.input_text); print('REFERENCE:', r.target_text)
    for m, g in gens.items():
        for method in ['greedy', 'beam']:
            print(f'{m:<10}{method:<7}:', g.generate_from_text(r.input_text, method).text)
    print()"""),
    md("## Test-set metrics (from `scripts/04_evaluate.py`)"),
    code("cmp = pd.read_csv(C.METRICS_DIR / 'comparison.csv')\ncmp[['model','decoding','n_test','bleu','rouge1','rouge2','rougeL','perplexity','token_acc','repetition_rate','distinct2','title_coverage','avg_gen_len','n_params','train_time_min']].round(3)"),
    code("from IPython.display import Image\nfor f in ['learning_curves.png', 'metric_comparison.png']:\n    p = C.FIGURES_DIR / f\n    if p.exists(): display(Image(p))"),
    md("""**Metrics.** BLEU-4 (n-gram precision + brevity penalty) and ROUGE-1/2/L (overlap / longest common
subsequence, F1) compare with ONE reference, while many different descriptions are valid for the same
event: low absolute values are expected and they mostly rank systems. Perplexity = exp(mean token NLL) under
teacher forcing; token accuracy = share of reference tokens predicted at the right position given the true
prefix (it ignores fluency and the error propagation of free generation). Repetition rate, distinct-2 and
title coverage are added to diagnose loops, genericity and the use of input information."""),
    md("## Attention weights"),
    code("""if 'attention' in gens:
    for i in [0, 7]:
        r = gens['attention'].generate_from_text(test.input_text[i], 'greedy')
        plot_attention(r.attention, r.source_tokens, r.tokens + ['<eos>'], title=test.input_text[i][:70]); plt.show()"""),
    md("""Attention is often sharp on title words that are copied, and diffuse on function words
(the decoder's language model handles them). Attention weights show *where the decoder reads*, not a
causal explanation of the prediction."""),
    md("## Side-by-side table and error analysis"),
    code("pd.read_csv(C.EXAMPLES_DIR / 'side_by_side.csv').head(10)"),
    code("pd.read_csv(C.METRICS_DIR / 'error_rates.csv')"),
    code("from IPython.display import Markdown\nMarkdown((C.EXAMPLES_DIR / 'error_analysis.md').read_text(encoding='utf-8')[:12000])"),
])
