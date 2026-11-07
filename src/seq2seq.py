"""Encoder-decoder wrapper with teacher forcing."""
from __future__ import annotations

import random

import torch
import torch.nn as nn

from .config import ModelConfig
from .decoder import AttnDecoder, Decoder
from .encoder import Encoder
from .vocabulary import PAD_IDX


class Seq2Seq(nn.Module):
    def __init__(self, encoder: Encoder, decoder: nn.Module):
        super().__init__()
        self.encoder = encoder
        self.decoder = decoder

    @property
    def uses_attention(self) -> bool:
        return self.decoder.uses_attention

    def encode(self, src, src_len):
        enc_outputs, state = self.encoder(src, src_len)   # baseline: state = fixed context vector
        mask = src != PAD_IDX                              # [B, S]
        keys = self.decoder.prepare(enc_outputs)
        return enc_outputs, state, keys, mask

    def forward(self, src, src_len, tgt, teacher_forcing: float = 0.5, return_attention: bool = False):
        """
        src [B,S], tgt [B,T] = <sos> y1 .. yn <eos> <pad>...
        Predicts y1..<eos> from <sos>..yn  ->  logits [B, T-1, V]

        Teacher forcing: at each step, with probability `teacher_forcing`, the next
        decoder input is the ground-truth token y_t; otherwise it is the model's own
        prediction argmax(logits_t) (what happens at inference time).
        """
        enc_outputs, state, keys, mask = self.encode(src, src_len)
        B, T = tgt.shape
        logits_all, attn_all = [], []
        y = tgt[:, 0]                                       # <sos>
        for t in range(1, T):
            logits, state, attn = self.decoder.step(y, state, enc_outputs, keys, mask)
            logits_all.append(logits)
            if return_attention and attn is not None:
                attn_all.append(attn)
            use_truth = random.random() < teacher_forcing
            y = tgt[:, t] if use_truth else logits.argmax(-1)
        logits = torch.stack(logits_all, dim=1)
        attn = torch.stack(attn_all, dim=1) if attn_all else None
        return (logits, attn) if return_attention else logits


def build_model(cfg: ModelConfig, src_vocab_size: int, tgt_vocab_size: int) -> Seq2Seq:
    enc = Encoder(src_vocab_size, cfg.emb_dim, cfg.hid_dim, cfg.n_layers, cfg.dropout)
    if cfg.model_type == "baseline":
        dec = Decoder(tgt_vocab_size, cfg.emb_dim, cfg.hid_dim, cfg.n_layers, cfg.dropout)
    elif cfg.model_type == "attention":
        dec = AttnDecoder(tgt_vocab_size, cfg.emb_dim, cfg.hid_dim, enc_dim=cfg.hid_dim,
                          attn_dim=cfg.attn_dim, n_layers=cfg.n_layers, dropout=cfg.dropout)
    else:
        raise ValueError(f"unknown model_type {cfg.model_type!r}")
    model = Seq2Seq(enc, dec)
    _init_weights(model)
    return model


def _init_weights(model: nn.Module) -> None:
    for name, p in model.named_parameters():
        if "embedding" in name:
            nn.init.normal_(p, 0, 0.1)
            with torch.no_grad():
                p[PAD_IDX].zero_()
        elif "weight" in name and p.dim() > 1:
            nn.init.xavier_uniform_(p)
        elif "bias" in name:
            nn.init.zeros_(p)
            if "rnn.bias_ih" in name:                   # forget-gate bias = 1 (gate order i,f,g,o)
                n = p.size(0) // 4
                with torch.no_grad():
                    p[n:2 * n].fill_(1.0)
