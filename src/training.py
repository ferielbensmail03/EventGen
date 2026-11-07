"""Training loop: cross-entropy, Adam, gradient clipping, early stopping, checkpoints.

Loss: token-level cross-entropy = mean over non-<pad> target tokens of
      -log P(y_t | y_<t, X)   (negative log-likelihood of the reference token).
<pad> positions are excluded with ignore_index=PAD_IDX.
"""
from __future__ import annotations

import math
import time
from pathlib import Path

import pandas as pd
import torch
import torch.nn as nn

from .config import (SPLIT_FILES, SRC_VOCAB_FILE, TGT_VOCAB_FILE, ExperimentConfig,
                     experiment_dir)
from .dataset import EventDataset, make_loader
from .seq2seq import Seq2Seq, build_model
from .utils import count_parameters, get_device, save_json, set_seed
from .vocabulary import PAD_IDX, Vocabulary


def run_epoch(model: Seq2Seq, loader, criterion, device, optimizer=None, clip: float = 1.0,
              teacher_forcing: float = 0.5) -> dict:
    """One pass over `loader`. Training if an optimizer is given, otherwise evaluation.

    Evaluation always uses teacher_forcing=1.0, so the validation loss is the exact
    token-level NLL of the references (the quantity behind perplexity).
    """
    train = optimizer is not None
    model.train(train)
    tot_loss = tot_tokens = correct = 0.0
    with torch.set_grad_enabled(train):
        for src, src_len, tgt, _ in loader:
            src, src_len, tgt = src.to(device), src_len.to(device), tgt.to(device)
            logits = model(src, src_len, tgt, teacher_forcing=teacher_forcing if train else 1.0)
            gold = tgt[:, 1:]                                         # [B, T-1]
            loss = criterion(logits.reshape(-1, logits.size(-1)), gold.reshape(-1))
            if train:
                optimizer.zero_grad()
                loss.backward()                                       # backpropagation through time
                nn.utils.clip_grad_norm_(model.parameters(), clip)    # avoids exploding gradients
                optimizer.step()                                      # Adam update
            mask = gold != PAD_IDX
            n_tok = mask.sum().item()
            tot_loss += loss.item() * n_tok
            tot_tokens += n_tok
            correct += ((logits.argmax(-1) == gold) & mask).sum().item()
    avg = tot_loss / max(tot_tokens, 1)
    return {"loss": avg, "ppl": math.exp(min(avg, 50)), "token_acc": correct / max(tot_tokens, 1)}


def load_vocabs():
    return Vocabulary.load(SRC_VOCAB_FILE), Vocabulary.load(TGT_VOCAB_FILE)


def load_split(name: str) -> pd.DataFrame:
    return pd.read_csv(SPLIT_FILES[name])


def train_model(cfg: ExperimentConfig, verbose: bool = True) -> dict:
    set_seed(cfg.data.seed)
    device = get_device()
    src_vocab, tgt_vocab = load_vocabs()
    train_df, val_df = load_split("train"), load_split("val")
    if cfg.train.subset:
        train_df = train_df.sample(n=min(cfg.train.subset, len(train_df)), random_state=cfg.data.seed)
        val_df = val_df.sample(n=min(max(cfg.train.subset // 8, 64), len(val_df)), random_state=cfg.data.seed)

    ds_tr = EventDataset(train_df, src_vocab, tgt_vocab, cfg.data.max_source_tokens, cfg.data.max_target_tokens)
    ds_va = EventDataset(val_df, src_vocab, tgt_vocab, cfg.data.max_source_tokens, cfg.data.max_target_tokens)
    dl_tr = make_loader(ds_tr, cfg.train.batch_size, shuffle=True, seed=cfg.data.seed)
    dl_va = make_loader(ds_va, cfg.train.batch_size * 2, shuffle=False)

    model = build_model(cfg.model, len(src_vocab), len(tgt_vocab)).to(device)
    n_params = count_parameters(model)
    criterion = nn.CrossEntropyLoss(ignore_index=PAD_IDX)
    optimizer = torch.optim.Adam(model.parameters(), lr=cfg.train.lr)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="min",
                                                           factor=cfg.train.lr_factor,
                                                           patience=cfg.train.lr_patience)
    out_dir = experiment_dir(cfg.model.model_type, cfg.train.tag)
    out_dir.mkdir(parents=True, exist_ok=True)
    cfg.save(out_dir / "config.json")
    if verbose:
        print(f"[{out_dir.name}] device={device} params={n_params:,} train={len(ds_tr)} val={len(ds_va)}")

    history, best, bad_epochs, t0 = [], float("inf"), 0, time.time()
    start = 1
    if cfg.train.resume and (out_dir / "best.pt").exists():
        # continue from the best checkpoint (e.g. after a time limit or a Colab disconnect)
        ckpt = torch.load(out_dir / "best.pt", map_location=device, weights_only=False)
        model.load_state_dict(ckpt["model_state"])
        if "optimizer_state" in ckpt:
            optimizer.load_state_dict(ckpt["optimizer_state"])
        if (out_dir / "history.csv").exists():
            history = pd.read_csv(out_dir / "history.csv").to_dict("records")
            history = [r for r in history if r["epoch"] <= ckpt["epoch"]]
        best, start = ckpt["val_loss"], ckpt["epoch"] + 1
        t0 -= sum(r["epoch_time_s"] for r in history)          # cumulated training time
        if verbose:
            print(f"  resumed from epoch {ckpt['epoch']} (val loss {best:.3f})")
    t_run = time.time()
    for epoch in range(start, start + cfg.train.epochs):
        te = time.time()
        tr = run_epoch(model, dl_tr, criterion, device, optimizer, cfg.train.clip, cfg.train.teacher_forcing)
        va = run_epoch(model, dl_va, criterion, device)
        scheduler.step(va["loss"])
        row = {"epoch": epoch, "train_loss": tr["loss"], "train_ppl": tr["ppl"], "train_token_acc": tr["token_acc"],
               "val_loss": va["loss"], "val_ppl": va["ppl"], "val_token_acc": va["token_acc"],
               "lr": optimizer.param_groups[0]["lr"], "epoch_time_s": time.time() - te}
        history.append(row)
        improved = va["loss"] < best - 1e-4
        if improved:
            best, bad_epochs = va["loss"], 0
            torch.save({"model_state": model.state_dict(), "config": cfg.to_dict(), "epoch": epoch,
                        "val_loss": va["loss"], "n_params": n_params,
                        "optimizer_state": optimizer.state_dict(),
                        "src_vocab_size": len(src_vocab), "tgt_vocab_size": len(tgt_vocab)},
                       out_dir / "best.pt")
        else:
            bad_epochs += 1
        pd.DataFrame(history).to_csv(out_dir / "history.csv", index=False)
        save_json(_summary(out_dir, n_params, best, history, t0, device, ds_tr, ds_va, cfg),
                  out_dir / "train_summary.json")        # rewritten every epoch: survives a Colab disconnect
        if verbose:
            print(f"  epoch {epoch:02d} | train {tr['loss']:.3f} | val {va['loss']:.3f} "
                  f"(ppl {va['ppl']:.1f}, acc {va['token_acc']:.3f}) | {row['epoch_time_s']:.0f}s"
                  f"{'  *best*' if improved else ''}")
        if cfg.train.max_minutes and (time.time() - t_run) / 60 > cfg.train.max_minutes:
            if verbose:
                print(f"  time budget of {cfg.train.max_minutes} min reached")
            break
        if bad_epochs >= cfg.train.patience:
            if verbose:
                print(f"  early stopping: no improvement for {cfg.train.patience} epochs")
            break

    summary = _summary(out_dir, n_params, best, history, t0, device, ds_tr, ds_va, cfg)
    save_json(summary, out_dir / "train_summary.json")
    return summary


def _summary(out_dir, n_params, best, history, t0, device, ds_tr, ds_va, cfg) -> dict:
    return {"model": out_dir.name, "n_params": n_params, "best_val_loss": best,
            "best_val_ppl": math.exp(min(best, 50)),
            "best_epoch": int(min(history, key=lambda r: r["val_loss"])["epoch"]),
            "epochs_run": len(history), "train_time_s": time.time() - t0, "device": str(device),
            "train_size": len(ds_tr), "val_size": len(ds_va), "hyperparameters": cfg.to_dict()}


def load_model(model_dir: Path, device=None) -> tuple[Seq2Seq, ExperimentConfig]:
    device = device or get_device()
    ckpt = torch.load(Path(model_dir) / "best.pt", map_location=device, weights_only=False)
    cfg = ExperimentConfig.from_dict(ckpt["config"])
    model = build_model(cfg.model, ckpt["src_vocab_size"], ckpt["tgt_vocab_size"]).to(device)
    model.load_state_dict(ckpt["model_state"])
    model.eval()
    return model, cfg
