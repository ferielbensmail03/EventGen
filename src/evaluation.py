"""Evaluation metrics, implemented from their definitions (no black box).

* BLEU-4 (Papineni et al., 2002): corpus-level, clipped n-gram precision p_1..p_4,
  geometric mean, brevity penalty BP = min(1, exp(1 - r/c)).
* ROUGE-1 / ROUGE-2 / ROUGE-L F1 (Lin, 2004): unigram/bigram overlap and longest
  common subsequence between hypothesis and reference, averaged over the test set.
* Token accuracy + perplexity: computed with teacher forcing in `training.run_epoch`.
* Task-specific diagnostics: distinct-n (diversity), repetition rate,
  title-information coverage (are the content words of the title in the output?).
All metrics are computed on lower-cased tokens produced by `preprocessing.tokenize`.
"""
from __future__ import annotations

import math
from collections import Counter

import numpy as np
import pandas as pd

from .preprocessing import tokenize

FR_STOPWORDS = set("""
au aux avec ce ces dans de des du elle en et eux il je la le les leur lui ma mais me même mes moi mon ne nos
notre nous on ou par pas pour qu que qui sa se ses son sur ta te tes toi ton tu un une vos votre vous c' d' j'
l' m' n' s' t' qu' y à est sont été être a ont avoir fait faire plus tout tous toute toutes cette cet
""".split())
PUNCT = set(".,;:!?()\"'-...")


def ngrams(tokens: list[str], n: int) -> Counter:
    return Counter(tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1))


def corpus_bleu(hyps: list[list[str]], refs: list[list[str]], max_n: int = 4) -> dict:
    match = [0] * max_n
    total = [0] * max_n
    hyp_len = ref_len = 0
    for h, r in zip(hyps, refs):
        hyp_len += len(h)
        ref_len += len(r)
        for n in range(1, max_n + 1):
            hc, rc = ngrams(h, n), ngrams(r, n)
            match[n - 1] += sum(min(c, rc[g]) for g, c in hc.items())
            total[n - 1] += max(len(h) - n + 1, 0)
    precisions = [m / t if t else 0.0 for m, t in zip(match, total)]
    if min(precisions) == 0:
        bleu = 0.0
    else:
        bp = 1.0 if hyp_len > ref_len else math.exp(1 - ref_len / max(hyp_len, 1))
        bleu = bp * math.exp(sum(math.log(p) for p in precisions) / max_n)
    return {"bleu": 100 * bleu, **{f"p{n + 1}": 100 * p for n, p in enumerate(precisions)},
            "hyp_ref_ratio": hyp_len / max(ref_len, 1)}


def sentence_bleu(h: list[str], r: list[str], max_n: int = 4) -> float:
    """Smoothed sentence BLEU (add-1 on n>1, Lin & Och 2004) — used only to rank examples."""
    if not h:
        return 0.0
    logs = []
    for n in range(1, max_n + 1):
        hc, rc = ngrams(h, n), ngrams(r, n)
        m = sum(min(c, rc[g]) for g, c in hc.items())
        t = max(len(h) - n + 1, 0)
        if n == 1:
            if m == 0:
                return 0.0
            logs.append(math.log(m / t))
        else:
            logs.append(math.log((m + 1) / (t + 1)))
    bp = 1.0 if len(h) > len(r) else math.exp(1 - len(r) / len(h))
    return 100 * bp * math.exp(sum(logs) / max_n)


def _f1(overlap: float, h: int, r: int) -> float:
    if h == 0 or r == 0 or overlap == 0:
        return 0.0
    p, rec = overlap / h, overlap / r
    return 2 * p * rec / (p + rec)


def lcs_len(a: list[str], b: list[str]) -> int:
    if not a or not b:
        return 0
    prev = [0] * (len(b) + 1)
    for x in a:
        cur = [0]
        for j, y in enumerate(b):
            cur.append(prev[j] + 1 if x == y else max(prev[j + 1], cur[j]))
        prev = cur
    return prev[-1]


def rouge_scores(h: list[str], r: list[str]) -> dict:
    out = {}
    for n in (1, 2):
        hc, rc = ngrams(h, n), ngrams(r, n)
        ov = sum((hc & rc).values())
        out[f"rouge{n}"] = _f1(ov, max(len(h) - n + 1, 0), max(len(r) - n + 1, 0))
    out["rougeL"] = _f1(lcs_len(h, r), len(h), len(r))
    return out


def distinct_n(hyps: list[list[str]], n: int) -> float:
    all_ngrams = [g for h in hyps for g in ngrams(h, n)]
    return len(set(all_ngrams)) / max(len(all_ngrams), 1)


def has_repetition(h: list[str], n: int = 3) -> bool:
    c = ngrams([t for t in h if t not in PUNCT], n)
    return any(v > 1 for v in c.values())


def content_words(tokens: list[str]) -> list[str]:
    return [t for t in tokens if t not in FR_STOPWORDS and t not in PUNCT and len(t) > 2 and not t.isdigit()]


def title_coverage(title: str, hyp: list[str], tgt_vocab=None) -> float | None:
    """Share of the title's content words that appear in the output.

    Only words the model CAN produce (in the target vocabulary) are counted,
    otherwise the score would mostly measure vocabulary coverage.
    """
    words = set(content_words(tokenize(title)))
    if tgt_vocab is not None:
        words = {w for w in words if w in tgt_vocab.word2idx}
    if not words:
        return None
    return len(words & set(hyp)) / len(words)


def evaluate_generations(df: pd.DataFrame, hyps: list[list[str]], tgt_vocab=None) -> tuple[dict, pd.DataFrame]:
    refs = [tokenize(t) for t in df["target_text"]]
    bleu = corpus_bleu(hyps, refs)
    rows = []
    for (_, r), h, ref in zip(df.iterrows(), hyps, refs):
        rs = rouge_scores(h, ref)
        rows.append({"id": r.get("id"), "input_text": r["input_text"], "reference": r["target_text"],
                     "generated": " ".join(h), "sent_bleu": sentence_bleu(h, ref), **rs,
                     "gen_len": len(h), "ref_len": len(ref), "repetition": has_repetition(h),
                     "title_coverage": title_coverage(r.get("title_clean", ""), h, tgt_vocab),
                     "ref_unk_rate": (sum(t not in tgt_vocab.word2idx for t in ref) / max(len(ref), 1))
                     if tgt_vocab is not None else None})
    per = pd.DataFrame(rows)
    metrics = {
        **bleu,
        "rouge1": 100 * per["rouge1"].mean(), "rouge2": 100 * per["rouge2"].mean(),
        "rougeL": 100 * per["rougeL"].mean(),
        "distinct1": distinct_n(hyps, 1), "distinct2": distinct_n(hyps, 2),
        "repetition_rate": float(per["repetition"].mean()),
        "avg_gen_len": float(per["gen_len"].mean()), "avg_ref_len": float(per["ref_len"].mean()),
        "title_coverage": float(per["title_coverage"].dropna().mean()) if per["title_coverage"].notna().any() else None,
        "n_examples": len(per),
    }
    return metrics, per
