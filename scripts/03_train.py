"""Step 3 - train a model.

  python scripts/03_train.py --model baseline
  python scripts/03_train.py --model attention
  python scripts/03_train.py --model attention --tf 0.0 --tag tf0.0     (teacher-forcing study)
  python scripts/03_train.py --model baseline --subset 2000 --epochs 2  (smoke test on CPU)
"""
import argparse

import _bootstrap  # noqa: F401
from src.config import ExperimentConfig, ensure_dirs
from src.training import train_model

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--model", choices=["baseline", "attention"], required=True)
    p.add_argument("--epochs", type=int)
    p.add_argument("--batch_size", type=int)
    p.add_argument("--lr", type=float)
    p.add_argument("--tf", type=float, help="teacher forcing ratio")
    p.add_argument("--emb_dim", type=int)
    p.add_argument("--hid_dim", type=int)
    p.add_argument("--n_layers", type=int)
    p.add_argument("--dropout", type=float)
    p.add_argument("--patience", type=int)
    p.add_argument("--subset", type=int)
    p.add_argument("--resume", action="store_true", help="continue from the saved best checkpoint")
    p.add_argument("--max_minutes", type=float, help="time budget (stops after the current epoch)")
    p.add_argument("--tag", default="")
    p.add_argument("--threads", type=int, help="CPU threads for PyTorch")
    a = p.parse_args()

    if a.threads:
        import torch
        torch.set_num_threads(a.threads)
    ensure_dirs()
    cfg = ExperimentConfig()
    cfg.model.model_type = a.model
    for k, target in [("epochs", cfg.train), ("batch_size", cfg.train), ("lr", cfg.train),
                      ("patience", cfg.train), ("subset", cfg.train), ("max_minutes", cfg.train),
                      ("emb_dim", cfg.model), ("hid_dim", cfg.model), ("n_layers", cfg.model),
                      ("dropout", cfg.model)]:
        if getattr(a, k) is not None:
            setattr(target, k, getattr(a, k))
    if a.tf is not None:
        cfg.train.teacher_forcing = a.tf
    cfg.train.tag = a.tag
    cfg.train.resume = a.resume
    summary = train_model(cfg)
    print({k: v for k, v in summary.items() if k != "hyperparameters"})
