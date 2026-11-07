"""(input, target) pair construction, pair validation and leakage-safe splitting."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .config import DataConfig
from .preprocessing import serialize_event, tokenize, truncate_at_sentence


def build_pairs(clean: pd.DataFrame, cfg: DataConfig) -> tuple[pd.DataFrame, dict]:
    report = {"rows_in": int(len(clean)), "steps": []}
    df = clean.copy()
    df["input_text"] = [serialize_event(t, labels) for t, labels in zip(df["title_clean"], df["type_labels"])]

    tgt_tokens = df["description_clean"].map(tokenize)
    df["target_tokens_full"] = tgt_tokens.map(len)

    n = len(df)
    keep = df["target_tokens_full"] >= cfg.min_target_tokens
    df, tgt_tokens = df[keep], tgt_tokens[keep]
    report["steps"].append({"step": "too_short_target", "removed": int(n - len(df)),
                            "reason": f"< {cfg.min_target_tokens} tokens"})

    truncated = tgt_tokens.map(lambda t: truncate_at_sentence(t, cfg.max_target_tokens))
    n = len(df)
    ok = truncated.notna()
    df, truncated = df[ok], truncated[ok]
    report["steps"].append({"step": "no_sentence_boundary_within_max_len", "removed": int(n - len(df)),
                            "reason": f"> {cfg.max_target_tokens} tokens and no '.!?' to cut at"})
    df["was_truncated"] = df["target_tokens_full"] > cfg.max_target_tokens
    df["target_tokens"] = truncated.map(len)

    n = len(df)
    ok = df["target_tokens"] >= cfg.min_target_tokens
    df, truncated = df[ok], truncated[ok]
    report["steps"].append({"step": "too_short_after_truncation", "removed": int(n - len(df)),
                            "reason": f"< {cfg.min_target_tokens} tokens after cut"})

    # target_text is stored in its cleaned, *readable* form (case preserved);
    # lower-casing/tokenisation happen in the Dataset with the same function as inference.
    df["target_text"] = [_cut_text(text, len(toks)) for text, toks in zip(df["description_clean"], truncated)]
    df["source_tokens"] = df["input_text"].map(lambda s: len(tokenize(s)))
    df["source_dataset"] = "datatourisme"

    # ---- pair validation
    checks = {
        "empty_input": int((df["input_text"].str.strip() == "").sum()),
        "empty_target": int((df["target_text"].str.strip() == "").sum()),
        "duplicate_pairs": int(df.duplicated(subset=["input_text", "target_text"]).sum()),
        "duplicate_ids": int(df["id"].duplicated().sum()),
        "target_from_other_event": 0,   # pairs come from the same record: no join performed
    }
    report["validation"] = checks
    assert checks["empty_input"] == 0 and checks["empty_target"] == 0, checks
    df = df.drop_duplicates(subset=["input_text", "target_text"])
    report["rows_out"] = int(len(df))
    report["truncated_targets"] = int(df["was_truncated"].sum())
    cols = ["id", "input_text", "target_text", "source_dataset", "title_clean", "type_labels",
            "source_tokens", "target_tokens", "was_truncated", "title_norm", "desc_norm"]
    return df[cols].reset_index(drop=True), report


def _cut_text(text: str, n_tokens: int) -> str:
    """Return the prefix of `text` that tokenises to exactly n_tokens (keeps original casing)."""
    from .preprocessing import _TOKEN_RE, normalize_unicode
    import re
    t = re.sub(r"\s+", " ", normalize_unicode(text)).strip()
    matches = list(_TOKEN_RE.finditer(t))
    if len(matches) <= n_tokens:
        return t
    return t[: matches[n_tokens - 1].end()].strip()


# ------------------------------------------------------------------ group-based split
class _UnionFind:
    def __init__(self, n):
        self.p = list(range(n))

    def find(self, x):
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[rb] = ra


def leakage_groups(df: pd.DataFrame, prefix_tokens: int = 12) -> np.ndarray:
    """Connected components of records sharing a title OR the same description opening.

    Two events with the same title (a recurring show) or whose descriptions start
    with the same 12 tokens (near-duplicates, templates) are put in the same
    group, and a whole group goes to a single split.
    """
    uf = _UnionFind(len(df))
    for key in (df["title_norm"].values,
                df["desc_norm"].map(lambda s: " ".join(s.split()[:prefix_tokens])).values):
        first: dict = {}
        for i, k in enumerate(key):
            if k in first:
                uf.union(first[k], i)
            else:
                first[k] = i
    return np.array([uf.find(i) for i in range(len(df))])


def group_split(df: pd.DataFrame, cfg: DataConfig) -> dict[str, pd.DataFrame]:
    groups = leakage_groups(df)
    uniq = np.unique(groups)
    rng = np.random.default_rng(cfg.seed)
    rng.shuffle(uniq)
    sizes = pd.Series(groups).value_counts()
    target_train = cfg.train_ratio * len(df)
    target_val = (cfg.train_ratio + cfg.val_ratio) * len(df)
    assign, cum = {}, 0
    for g in uniq:
        cum += sizes[g]
        assign[g] = "train" if cum <= target_train else ("val" if cum <= target_val else "test")
    split = pd.Series(groups).map(assign).values
    out = {s: df[split == s].reset_index(drop=True) for s in ("train", "val", "test")}
    return out


def split_report(splits: dict[str, pd.DataFrame]) -> dict:
    total = sum(len(v) for v in splits.values())
    rep = {s: {"rows": int(len(d)), "pct": round(100 * len(d) / total, 2)} for s, d in splits.items()}
    tr_titles, tr_desc = set(splits["train"]["title_norm"]), set(splits["train"]["desc_norm"])
    for s in ("val", "test"):
        rep[s]["title_overlap_with_train"] = int(splits[s]["title_norm"].isin(tr_titles).sum())
        rep[s]["description_overlap_with_train"] = int(splits[s]["desc_norm"].isin(tr_desc).sum())
    return rep
