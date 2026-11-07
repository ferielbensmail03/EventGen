"""Additive (Bahdanau) attention.

At decoder step t, with s_{t-1} the previous decoder hidden state and h_i the
encoder hidden state of source position i:

    e(t,i)     = vᵀ tanh(W_h h_i + W_s s_{t-1})          alignment score
    α(t,i)     = exp(e(t,i)) / Σ_j exp(e(t,j))            attention weight (softmax over i)
    c(t)       = Σ_i α(t,i) h_i                           context vector

Padded source positions get e = -inf, hence α = 0.
"""
from __future__ import annotations

import torch
import torch.nn as nn


class BahdanauAttention(nn.Module):
    def __init__(self, enc_dim: int, dec_dim: int, attn_dim: int):
        super().__init__()
        self.W_h = nn.Linear(enc_dim, attn_dim, bias=False)
        self.W_s = nn.Linear(dec_dim, attn_dim, bias=True)
        self.v = nn.Linear(attn_dim, 1, bias=False)

    def project_keys(self, enc_outputs: torch.Tensor) -> torch.Tensor:
        """W_h h_i does not depend on t: computed once per batch. [B,S,H] -> [B,S,A]"""
        return self.W_h(enc_outputs)

    def forward(self, dec_hidden: torch.Tensor, enc_outputs: torch.Tensor,
                keys: torch.Tensor, mask: torch.Tensor):
        """
        dec_hidden:  [B, H_dec]   s_{t-1} (top layer)
        enc_outputs: [B, S, H]    h_1..h_S
        keys:        [B, S, A]    W_h h_i (pre-computed)
        mask:        [B, S]       True on real tokens, False on <pad>
        returns context [B, H], weights [B, S]
        """
        query = self.W_s(dec_hidden).unsqueeze(1)                    # [B, 1, A]
        scores = self.v(torch.tanh(keys + query)).squeeze(-1)        # [B, S]   e(t,i)
        scores = scores.masked_fill(~mask, float("-inf"))
        weights = torch.softmax(scores, dim=-1)                      # [B, S]   α(t,i)
        context = torch.bmm(weights.unsqueeze(1), enc_outputs).squeeze(1)   # [B, H]   c(t)
        return context, weights
