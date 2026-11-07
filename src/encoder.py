"""LSTM encoder.

x_1..x_S (token ids) -> Embedding -> LSTM -> h_1..h_S (all hidden states)
                                            + (h_S, c_S) final hidden & cell states.

LSTM gates at time t (σ = sigmoid, ⊙ = element-wise product):
    f_t = σ(W_f [h_{t-1}, x_t] + b_f)     forget gate: what to erase from c_{t-1}
    i_t = σ(W_i [h_{t-1}, x_t] + b_i)     input gate:  what new information to write
    g_t = tanh(W_g [h_{t-1}, x_t] + b_g)  candidate content
    c_t = f_t ⊙ c_{t-1} + i_t ⊙ g_t       cell state (long-term memory)
    o_t = σ(W_o [h_{t-1}, x_t] + b_o)     output gate: what part of memory to expose
    h_t = o_t ⊙ tanh(c_t)                 hidden state
"""
from __future__ import annotations

import torch
import torch.nn as nn
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence

from .vocabulary import PAD_IDX


class Encoder(nn.Module):
    def __init__(self, vocab_size: int, emb_dim: int, hid_dim: int, n_layers: int = 1, dropout: float = 0.3):
        super().__init__()
        # padding_idx: the <pad> vector stays zero and receives no gradient
        self.embedding = nn.Embedding(vocab_size, emb_dim, padding_idx=PAD_IDX)
        self.dropout = nn.Dropout(dropout)
        self.rnn = nn.LSTM(emb_dim, hid_dim, num_layers=n_layers, batch_first=True,
                           dropout=dropout if n_layers > 1 else 0.0)

    def forward(self, src: torch.Tensor, src_len: torch.Tensor):
        """
        src:     [B, S]  token ids (padded)
        src_len: [B]     true lengths
        returns  outputs [B, S, H]  (zeros at padded positions)
                 (h, c)  each [n_layers, B, H]
        """
        emb = self.dropout(self.embedding(src))                       # [B, S, E]
        # packing = the LSTM skips <pad> positions, so h_S is the state after the LAST REAL token
        packed = pack_padded_sequence(emb, src_len.cpu(), batch_first=True, enforce_sorted=False)
        packed_out, (h, c) = self.rnn(packed)
        outputs, _ = pad_packed_sequence(packed_out, batch_first=True, total_length=src.size(1))
        return outputs, (h, c)
