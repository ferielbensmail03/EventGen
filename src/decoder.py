"""LSTM decoders: baseline (fixed context) and attention-based.

Both expose the same step interface so that training, greedy decoding and
beam search work for either model:

    logits, state, attn = decoder.step(y_prev, state, enc_outputs, keys, mask)
"""
from __future__ import annotations

import torch
import torch.nn as nn

from .attention import BahdanauAttention
from .vocabulary import PAD_IDX


class Decoder(nn.Module):
    """Baseline: the only information about the source is the initial state (h_S, c_S)."""

    uses_attention = False

    def __init__(self, vocab_size: int, emb_dim: int, hid_dim: int, n_layers: int = 1, dropout: float = 0.3):
        super().__init__()
        self.vocab_size = vocab_size
        self.embedding = nn.Embedding(vocab_size, emb_dim, padding_idx=PAD_IDX)
        self.dropout = nn.Dropout(dropout)
        self.rnn = nn.LSTM(emb_dim, hid_dim, num_layers=n_layers, batch_first=True,
                           dropout=dropout if n_layers > 1 else 0.0)
        self.fc_out = nn.Linear(hid_dim, vocab_size)     # hidden -> logits over the target vocabulary

    def prepare(self, enc_outputs):
        return None

    def step(self, y_prev, state, enc_outputs=None, keys=None, mask=None):
        """
        y_prev: [B] previous token ids     state: (h, c) each [L, B, H]
        returns logits [B, V], new state, None
        """
        emb = self.dropout(self.embedding(y_prev)).unsqueeze(1)      # [B, 1, E]
        out, state = self.rnn(emb, state)                            # [B, 1, H]
        logits = self.fc_out(self.dropout(out.squeeze(1)))           # [B, V]
        return logits, state, None


class AttnDecoder(nn.Module):
    """Decoder with Bahdanau attention: a new context c(t) is computed at every step."""

    uses_attention = True

    def __init__(self, vocab_size: int, emb_dim: int, hid_dim: int, enc_dim: int,
                 attn_dim: int = 256, n_layers: int = 1, dropout: float = 0.3):
        super().__init__()
        self.vocab_size = vocab_size
        self.embedding = nn.Embedding(vocab_size, emb_dim, padding_idx=PAD_IDX)
        self.dropout = nn.Dropout(dropout)
        self.attention = BahdanauAttention(enc_dim, hid_dim, attn_dim)
        # LSTM input = [embedding(y_{t-1}) ; c(t)]
        self.rnn = nn.LSTM(emb_dim + enc_dim, hid_dim, num_layers=n_layers, batch_first=True,
                           dropout=dropout if n_layers > 1 else 0.0)
        # output layer sees [s_t ; c(t) ; embedding(y_{t-1})]
        self.fc_out = nn.Linear(hid_dim + enc_dim + emb_dim, vocab_size)

    def prepare(self, enc_outputs):
        return self.attention.project_keys(enc_outputs)

    def step(self, y_prev, state, enc_outputs, keys, mask):
        emb = self.dropout(self.embedding(y_prev))                   # [B, E]
        h_top = state[0][-1]                                         # [B, H]  s_{t-1}
        context, weights = self.attention(h_top, enc_outputs, keys, mask)   # [B, H_enc], [B, S]
        rnn_in = torch.cat([emb, context], dim=-1).unsqueeze(1)      # [B, 1, E+H_enc]
        out, state = self.rnn(rnn_in, state)                         # [B, 1, H]
        feats = torch.cat([out.squeeze(1), context, emb], dim=-1)    # [B, H+H_enc+E]
        logits = self.fc_out(self.dropout(feats))                    # [B, V]
        return logits, state, weights
