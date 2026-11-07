"""PyTorch Dataset / DataLoader with dynamic padding."""
from __future__ import annotations

import pandas as pd
import torch
from torch.nn.utils.rnn import pad_sequence
from torch.utils.data import DataLoader, Dataset

from .preprocessing import tokenize
from .vocabulary import PAD_IDX, Vocabulary


class EventDataset(Dataset):
    """Tokenises + numericalises every pair once (same functions as inference)."""

    def __init__(self, df: pd.DataFrame, src_vocab: Vocabulary, tgt_vocab: Vocabulary,
                 max_src_len: int, max_tgt_len: int):
        self.df = df.reset_index(drop=True)
        # source: truncated to max_src_len, no <sos>/<eos>
        self.src = [src_vocab.encode(tokenize(s), max_len=max_src_len) for s in self.df["input_text"]]
        # target: <sos> w1 ... wn <eos>, total length <= max_tgt_len + 2
        self.tgt = [tgt_vocab.encode(tokenize(t), add_sos_eos=True, max_len=max_tgt_len + 2)
                    for t in self.df["target_text"]]

    def __len__(self) -> int:
        return len(self.src)

    def __getitem__(self, i):
        return torch.tensor(self.src[i], dtype=torch.long), torch.tensor(self.tgt[i], dtype=torch.long), i


def collate(batch):
    """Pad to the longest sequence of the batch (not of the dataset) -> less wasted compute."""
    src, tgt, idx = zip(*batch)
    src_len = torch.tensor([len(s) for s in src], dtype=torch.long)
    src = pad_sequence(src, batch_first=True, padding_value=PAD_IDX)   # [B, S]
    tgt = pad_sequence(tgt, batch_first=True, padding_value=PAD_IDX)   # [B, T]
    return src, src_len, tgt, torch.tensor(idx)


def make_loader(ds: EventDataset, batch_size: int, shuffle: bool, seed: int = 42, num_workers: int = 0):
    g = torch.Generator()
    g.manual_seed(seed)
    return DataLoader(ds, batch_size=batch_size, shuffle=shuffle, collate_fn=collate,
                      generator=g, num_workers=num_workers)
