"""Vocabulary: word2idx / idx2word built from the TRAINING split only."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Iterable

from .preprocessing import EOS, PAD, SOS, SPECIAL_TOKENS, UNK

PAD_IDX, UNK_IDX, SOS_IDX, EOS_IDX = 0, 1, 2, 3


class Vocabulary:
    """
    <pad> (0) fills sequences up to the batch length; ignored by the loss and masked in attention.
    <unk> (1) replaces words that are rare or never seen in training.
    <sos> (2) first decoder input: "start generating".
    <eos> (3) the decoder emits it to say "the description is finished".
    """

    def __init__(self, min_freq: int = 1, max_size: int | None = None):
        self.min_freq = min_freq
        self.max_size = max_size
        self.word2idx: dict[str, int] = {t: i for i, t in enumerate(SPECIAL_TOKENS)}
        self.idx2word: list[str] = list(SPECIAL_TOKENS)
        self.freqs: Counter = Counter()

    # ---------------------------------------------------------------- build
    def build(self, token_lists: Iterable[list[str]]) -> "Vocabulary":
        for toks in token_lists:
            self.freqs.update(toks)
        items = [(w, c) for w, c in self.freqs.items() if c >= self.min_freq and w not in self.word2idx]
        items.sort(key=lambda x: (-x[1], x[0]))          # deterministic order
        if self.max_size:
            items = items[: self.max_size - len(SPECIAL_TOKENS)]
        for w, _ in items:
            self.word2idx[w] = len(self.idx2word)
            self.idx2word.append(w)
        return self

    def __len__(self) -> int:
        return len(self.idx2word)

    # ---------------------------------------------------------------- encode / decode
    def encode(self, tokens: list[str], add_sos_eos: bool = False, max_len: int | None = None) -> list[int]:
        ids = [self.word2idx.get(t, UNK_IDX) for t in tokens]
        if max_len is not None:
            ids = ids[: max_len - (2 if add_sos_eos else 0)]
        if add_sos_eos:
            ids = [SOS_IDX] + ids + [EOS_IDX]
        return ids

    def decode(self, ids: Iterable[int], stop_at_eos: bool = True) -> list[str]:
        out = []
        for i in ids:
            i = int(i)
            if i == EOS_IDX and stop_at_eos:
                break
            if i in (PAD_IDX, SOS_IDX):
                continue
            out.append(self.idx2word[i] if 0 <= i < len(self.idx2word) else UNK)
        return out

    # ---------------------------------------------------------------- stats
    def coverage(self, token_lists: Iterable[list[str]]) -> float:
        total = known = 0
        for toks in token_lists:
            total += len(toks)
            known += sum(t in self.word2idx for t in toks)
        return known / max(total, 1)

    def stats(self) -> dict:
        n_total = len(self.freqs)
        return {
            "size": len(self),
            "distinct_training_words": n_total,
            "kept_words": len(self) - len(SPECIAL_TOKENS),
            "min_freq": self.min_freq,
            "max_size": self.max_size,
            "top_20": self.freqs.most_common(20),
        }

    # ---------------------------------------------------------------- io
    def save(self, path: Path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(json.dumps({
            "min_freq": self.min_freq, "max_size": self.max_size,
            "idx2word": self.idx2word, "freqs": dict(self.freqs),
        }, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "Vocabulary":
        d = json.loads(Path(path).read_text(encoding="utf-8"))
        v = cls(d["min_freq"], d["max_size"])
        v.idx2word = d["idx2word"]
        v.word2idx = {w: i for i, w in enumerate(v.idx2word)}
        v.freqs = Counter(d.get("freqs", {}))
        assert v.idx2word[:4] == [PAD, UNK, SOS, EOS]
        return v
