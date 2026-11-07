"""Inference: event fields -> description, with greedy decoding or beam search.

Pipeline (identical to training preprocessing):
event fields -> serialize_event -> normalize -> tokenize -> ids (UNK for unknown words)
-> truncate to max_source_tokens -> encoder -> decoder starts from <sos>
-> next token = argmax (greedy) or best partial hypotheses (beam)
-> feed the prediction back -> stop at <eos> or max_len -> ids -> words -> detokenize.
No reference description is used at any point.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch

from .config import SRC_VOCAB_FILE, TGT_VOCAB_FILE, GenerationConfig
from .preprocessing import detokenize, serialize_event, tokenize
from .seq2seq import Seq2Seq
from .training import load_model
from .vocabulary import EOS_IDX, PAD_IDX, SOS_IDX, UNK_IDX, Vocabulary


def _blocked_ids(block_unk: bool) -> list[int]:
    return [PAD_IDX, SOS_IDX] + ([UNK_IDX] if block_unk else [])


WEAK_ENDINGS = ("de", "du", "des", "la", "le", "les", "l'", "d'", "à", "au", "aux", "et", "un", "une",
                ",", "en", "pour", "par", "sur", "avec", "dans")


def _apply_rules(scores, y, rules):
    """Decoding rules: no number absent from the input, no doubled token, no end on a weak word."""
    if rules is None:
        return
    numbers, weak, stops = rules
    scores[:, numbers.to(scores.device)] = float("-inf")
    scores[torch.arange(len(y), device=scores.device), y] = float("-inf")
    is_weak = torch.isin(y, weak.to(scores.device))
    for tok in stops:
        scores[is_weak, tok] = float("-inf")


def _ngram_block(seq: list[int], n: int) -> set[int]:
    """Tokens that would recreate an n-gram already present in `seq`."""
    if n <= 0 or len(seq) < n - 1:
        return set()
    prefix = tuple(seq[-(n - 1):]) if n > 1 else tuple()
    banned = set()
    for i in range(len(seq) - n + 1):
        if tuple(seq[i:i + n - 1]) == prefix:
            banned.add(seq[i + n - 1])
    return banned


@torch.no_grad()
def greedy_decode(model: Seq2Seq, src, src_len, max_len: int = 60, block_unk: bool = True,
                  no_repeat_ngram: int = 0, rules=None):
    """Batched greedy decoding: y_t = argmax_y P(y | y_<t, X).

    returns list of id lists (without <sos>/<eos>), attention [B, T, S] or None
    """
    enc, state, keys, mask = model.encode(src, src_len)
    B = src.size(0)
    y = torch.full((B,), SOS_IDX, dtype=torch.long, device=src.device)
    outs = [[] for _ in range(B)]
    done = torch.zeros(B, dtype=torch.bool, device=src.device)
    attns = []
    blocked = _blocked_ids(block_unk)
    for t in range(max_len):
        logits, state, attn = model.decoder.step(y, state, enc, keys, mask)
        logits[:, blocked] = float("-inf")
        _apply_rules(logits, y, rules)
        if t == 0:
            logits[:, EOS_IDX] = float("-inf")             # no empty description
        if no_repeat_ngram:
            for b in range(B):
                for tok in _ngram_block(outs[b], no_repeat_ngram):
                    logits[b, tok] = float("-inf")
        y = logits.argmax(-1)
        if attn is not None:
            attns.append(attn)
        for b in range(B):
            if not done[b]:
                if y[b].item() == EOS_IDX:
                    done[b] = True
                else:
                    outs[b].append(y[b].item())
        if done.all():
            break
    attn = torch.stack(attns, dim=1) if attns else None
    return outs, attn


@torch.no_grad()
def beam_search(model: Seq2Seq, src, src_len, beam_width: int = 3, max_len: int = 60,
                length_penalty: float = 0.7, block_unk: bool = True, no_repeat_ngram: int = 0, rules=None):
    """Beam search for ONE source sequence (src: [1, S]).

    Keeps the `beam_width` partial sequences with the highest cumulative
    log-probability Σ log P(y_t | y_<t, X). A hypothesis ending with <eos> is
    moved to `finished`. Final choice: highest score / lp(len) with
    lp(len) = ((5 + len) / 6) ** length_penalty, which stops the search from
    systematically preferring short outputs.
    returns (ids, attention [T, S] or None, normalised score)
    """
    enc, state, keys, mask = model.encode(src, src_len)
    K = beam_width
    blocked = _blocked_ids(block_unk)
    beams = [([], 0.0, state, [])]                   # (ids, logp, (h,c), attention rows)
    finished = []

    def lp(n):
        return ((5 + n) / 6) ** length_penalty

    for t in range(max_len):
        n = len(beams)
        y = torch.tensor([b[0][-1] if b[0] else SOS_IDX for b in beams], device=src.device)
        h = torch.cat([b[2][0] for b in beams], dim=1)
        c = torch.cat([b[2][1] for b in beams], dim=1)
        logits, (h2, c2), attn = model.decoder.step(
            y, (h, c), enc.expand(n, -1, -1), None if keys is None else keys.expand(n, -1, -1),
            mask.expand(n, -1))
        logp = torch.log_softmax(logits, dim=-1)
        logp[:, blocked] = float("-inf")
        _apply_rules(logp, y, rules)
        if t == 0:
            logp[:, EOS_IDX] = float("-inf")
        if no_repeat_ngram:
            for i, b in enumerate(beams):
                for tok in _ngram_block(b[0], no_repeat_ngram):
                    logp[i, tok] = float("-inf")
        cand_scores = (logp + torch.tensor([b[1] for b in beams], device=src.device).unsqueeze(1))
        top_scores, top_idx = cand_scores.view(-1).topk(min(2 * K, cand_scores.numel()))
        new_beams = []
        V = logp.size(1)
        for s, flat in zip(top_scores.tolist(), top_idx.tolist()):
            if s == float("-inf"):
                continue
            i, tok = divmod(flat, V)
            ids, _, _, att = beams[i]
            att_new = att + ([attn[i].cpu()] if attn is not None else [])
            if tok == EOS_IDX:
                finished.append((ids, s / lp(len(ids) + 1), att_new))
            else:
                new_beams.append((ids + [tok], s, (h2[:, i:i + 1].contiguous(), c2[:, i:i + 1].contiguous()), att_new))
            if len(new_beams) == K:
                break
        beams = new_beams
        if len(finished) >= K or not beams:
            break
    if not finished:                                   # max_len reached without <eos>
        finished = [(b[0], b[1] / lp(len(b[0])), b[3]) for b in beams]
    ids, score, att = max(finished, key=lambda f: f[1])
    attn_mat = torch.stack(att).numpy() if att else None
    return ids, attn_mat, score


@dataclass
class GenerationResult:
    text: str
    tokens: list[str]
    source_tokens: list[str]
    unknown_source_tokens: list[str]
    attention: np.ndarray | None        # [T_out(+eos), S]
    method: str


class EventGenerator:
    """High-level API used by the evaluation scripts and the Streamlit app."""

    def __init__(self, model_dir: Path, device=None):
        self.model, self.cfg = load_model(model_dir, device)
        self.device = next(self.model.parameters()).device
        self.src_vocab = Vocabulary.load(SRC_VOCAB_FILE)
        self.tgt_vocab = Vocabulary.load(TGT_VOCAB_FILE)
        self.name = Path(model_dir).name

    def encode_source(self, input_text: str):
        toks = tokenize(input_text)[: self.cfg.data.max_source_tokens]
        ids = self.src_vocab.encode(toks)
        src = torch.tensor([ids], device=self.device)
        return src, torch.tensor([len(ids)]), toks

    def _rules(self, source_tokens: list[str]):
        words = self.tgt_vocab.word2idx
        numbers = [i for w, i in words.items() if any(c.isdigit() for c in w) and w not in source_tokens]
        weak = [words[w] for w in WEAK_ENDINGS if w in words]
        stops = [EOS_IDX] + [words[w] for w in (",", ".", "!") if w in words]
        return torch.tensor(numbers, dtype=torch.long), torch.tensor(weak, dtype=torch.long), stops

    def generate_from_text(self, input_text: str, method: str = "greedy",
                           gen: GenerationConfig | None = None) -> GenerationResult:
        gen = gen or self.cfg.gen
        src, src_len, toks = self.encode_source(input_text)
        rules = self._rules(toks) if gen.clean_output else None
        if method == "greedy":
            outs, attn = greedy_decode(self.model, src, src_len, gen.max_len, gen.block_unk, gen.no_repeat_ngram, rules)
            ids, attn = outs[0], (attn[0].cpu().numpy() if attn is not None else None)
        elif method == "beam":
            ids, attn, _ = beam_search(self.model, src, src_len, gen.beam_width, gen.max_len,
                                       gen.length_penalty, gen.block_unk, gen.no_repeat_ngram, rules)
        else:
            raise ValueError(method)
        words = self.tgt_vocab.decode(ids)
        unk = [t for t in toks if t not in self.src_vocab.word2idx]
        return GenerationResult(detokenize(words), words, toks, unk, attn, method)

    def generate(self, title: str, type_labels: list[str] | None = None, method: str = "greedy",
                 gen: GenerationConfig | None = None) -> GenerationResult:
        return self.generate_from_text(serialize_event(title, type_labels or []), method, gen)

    @torch.no_grad()
    def generate_batch(self, input_texts: list[str], method: str = "greedy", batch_size: int = 128,
                       gen: GenerationConfig | None = None) -> list[list[str]]:
        """Token lists for many inputs (greedy is batched, beam is per example)."""
        gen = gen or self.cfg.gen
        results: list[list[str]] = []
        if method == "beam":
            for s in input_texts:
                src, src_len, _ = self.encode_source(s)
                ids, _, _ = beam_search(self.model, src, src_len, gen.beam_width, gen.max_len,
                                        gen.length_penalty, gen.block_unk, gen.no_repeat_ngram)
                results.append(self.tgt_vocab.decode(ids))
            return results
        for i in range(0, len(input_texts), batch_size):
            chunk = input_texts[i:i + batch_size]
            seqs = [self.src_vocab.encode(tokenize(s)[: self.cfg.data.max_source_tokens]) for s in chunk]
            lens = torch.tensor([len(s) for s in seqs])
            src = torch.full((len(seqs), int(lens.max())), PAD_IDX, dtype=torch.long)
            for j, s in enumerate(seqs):
                src[j, : len(s)] = torch.tensor(s)
            outs, _ = greedy_decode(self.model, src.to(self.device), lens, gen.max_len,
                                    gen.block_unk, gen.no_repeat_ngram)
            results.extend(self.tgt_vocab.decode(o) for o in outs)
        return results
