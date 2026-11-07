"""Matplotlib figures (EDA, learning curves, attention heatmaps, comparisons)."""
from __future__ import annotations

from pathlib import Path

import sys

import matplotlib

if "ipykernel" not in sys.modules:      # scripts / Streamlit: no display needed
    matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

COLORS = {"baseline": "#64748b", "attention": "#7c3aed", "train": "#2563eb", "val": "#f97316"}
plt.rcParams.update({"figure.dpi": 110, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": 0.25, "font.size": 10})


def _save(fig, path: Path | None):
    if path:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, bbox_inches="tight", dpi=150)
    return fig


def plot_missing(df: pd.DataFrame, title: str, path: Path | None = None):
    miss = df.isna().mean().sort_values() * 100
    fig, ax = plt.subplots(figsize=(7, max(2.5, 0.28 * len(miss))))
    ax.barh(miss.index, miss.values, color=["#ef4444" if v > 50 else "#2563eb" for v in miss.values])
    ax.set_xlabel("% missing")
    ax.set_xlim(0, 100)
    ax.set_title(title)
    for i, v in enumerate(miss.values):
        ax.text(min(v + 1, 92), i, f"{v:.0f}%", va="center", fontsize=8)
    return _save(fig, path)


def plot_length_hist(lengths: dict[str, pd.Series], title: str, path: Path | None = None, clip: int = 300):
    fig, ax = plt.subplots(figsize=(7, 3.5))
    for name, s in lengths.items():
        ax.hist(s.clip(upper=clip), bins=60, alpha=0.6, label=f"{name} (median {s.median():.0f})")
    ax.set_xlabel(f"words per description (clipped at {clip})")
    ax.set_ylabel("count")
    ax.set_title(title)
    ax.legend()
    return _save(fig, path)


def plot_bar_counts(counts: pd.Series, title: str, path: Path | None = None, top: int = 20, xlabel="count"):
    counts = counts.head(top)[::-1]
    fig, ax = plt.subplots(figsize=(7, max(2.5, 0.3 * len(counts))))
    ax.barh([str(i) for i in counts.index], counts.values, color="#2563eb")
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    return _save(fig, path)


def plot_learning_curves(histories: dict[str, pd.DataFrame], path: Path | None = None):
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.8))
    for name, h in histories.items():
        c = COLORS.get(name.split("_")[0], None)
        axes[0].plot(h["epoch"], h["train_loss"], "--", color=c, label=f"{name} train")
        axes[0].plot(h["epoch"], h["val_loss"], "-", color=c, label=f"{name} val")
        axes[1].plot(h["epoch"], h["val_ppl"], "-o", ms=3, color=c, label=name)
    axes[0].set(title="Cross-entropy loss per token", xlabel="epoch", ylabel="loss")
    axes[1].set(title="Validation perplexity", xlabel="epoch", ylabel="perplexity")
    for a in axes:
        a.legend(fontsize=8)
    fig.tight_layout()
    return _save(fig, path)


def plot_attention(attn: np.ndarray, src_tokens: list[str], out_tokens: list[str],
                   path: Path | None = None, title: str = "Attention weights α(t,i)"):
    attn = attn[: len(out_tokens), : len(src_tokens)]
    fig, ax = plt.subplots(figsize=(max(5, 0.38 * len(src_tokens)), max(4, 0.26 * len(out_tokens))))
    im = ax.imshow(attn, cmap="Purples", aspect="auto", vmin=0)
    ax.set_xticks(range(len(src_tokens)))
    ax.set_xticklabels(src_tokens, rotation=70, ha="right", fontsize=8)
    ax.set_yticks(range(len(out_tokens)))
    ax.set_yticklabels(out_tokens, fontsize=8)
    ax.set_xlabel("source (encoder) tokens")
    ax.set_ylabel("generated tokens")
    ax.grid(False)
    ax.set_title(title)
    fig.colorbar(im, ax=ax, fraction=0.03)
    fig.tight_layout()
    return _save(fig, path)


def plot_metric_comparison(table: pd.DataFrame, metrics: list[str], path: Path | None = None):
    fig, axes = plt.subplots(1, len(metrics), figsize=(3.2 * len(metrics), 3.4))
    axes = np.atleast_1d(axes)
    for ax, m in zip(axes, metrics):
        colors = [COLORS.get(str(n).split("_")[0], "#94a3b8") for n in table["model"]]
        labels = [f"{a}\n{b}" for a, b in zip(table["model"], table["decoding"])]
        ax.bar(labels, table[m], color=colors)
        ax.set_title(m)
        ax.tick_params(axis="x", labelsize=7)
        for i, v in enumerate(table[m]):
            ax.text(i, v, f"{v:.2f}", ha="center", va="bottom", fontsize=7)
    fig.tight_layout()
    return _save(fig, path)
