"""Step 4 - evaluate every trained model on the TEST split (E1-E4).

  python scripts/04_evaluate.py                         # all models in models/, greedy + beam
  python scripts/04_evaluate.py --max_examples 500      # quicker: 500 random test examples

Writes results/metrics/*.json, comparison.csv/.md, results/generated_examples/*.csv,
results/figures/*.png
"""
import argparse
import time

import pandas as pd
import torch.nn as nn

import _bootstrap  # noqa: F401
from src import config as C
from src.dataset import EventDataset, make_loader
from src.evaluation import evaluate_generations
from src.inference import EventGenerator
from src.preprocessing import detokenize
from src.training import load_split, run_epoch
from src.utils import load_json, save_json, set_seed
from src.visualization import plot_attention, plot_learning_curves, plot_metric_comparison
from src.vocabulary import PAD_IDX


def trained_models():
    return sorted(d for d in C.MODELS_DIR.iterdir() if (d / "best.pt").exists())


def main(a):
    set_seed(42)
    C.ensure_dirs()
    test = load_split(a.split)
    if a.max_examples:
        test = test.sample(n=min(a.max_examples, len(test)), random_state=42).reset_index(drop=True)
    model_dirs = [C.MODELS_DIR / m for m in a.models] if a.models else trained_models()
    if not model_dirs:
        raise SystemExit("No trained model found in models/. Run scripts/03_train.py first.")

    rows, generations, histories = [], {}, {}
    for md in model_dirs:
        gen = EventGenerator(md)
        summary = load_json(md / "train_summary.json") if (md / "train_summary.json").exists() else {}
        if (md / "history.csv").exists():
            histories[md.name] = pd.read_csv(md / "history.csv")
        # teacher-forced metrics: loss, perplexity, token accuracy
        ds = EventDataset(test, gen.src_vocab, gen.tgt_vocab, gen.cfg.data.max_source_tokens,
                          gen.cfg.data.max_target_tokens)
        tf_metrics = run_epoch(gen.model, make_loader(ds, 128, shuffle=False),
                               nn.CrossEntropyLoss(ignore_index=PAD_IDX), gen.device)
        for decoding in a.decoding:
            sub = test                    # same examples for greedy and beam -> fair E3 vs E4
            t0 = time.time()
            hyps = gen.generate_batch(sub["input_text"].tolist(), method=decoding)
            dt = time.time() - t0
            metrics, per = evaluate_generations(sub, hyps, gen.tgt_vocab)
            per.insert(3, "generated_text", [detokenize(h) for h in hyps])
            per.to_csv(C.EXAMPLES_DIR / f"{md.name}_{decoding}.csv", index=False)
            generations[(md.name, decoding)] = per
            row = {"model": md.name, "decoding": decoding, "n_test": len(sub),
                   "test_loss": tf_metrics["loss"], "perplexity": tf_metrics["ppl"],
                   "token_acc": tf_metrics["token_acc"], **metrics,
                   "n_params": summary.get("n_params"), "train_time_min": (summary.get("train_time_s") or 0) / 60,
                   "best_epoch": summary.get("best_epoch"), "best_val_loss": summary.get("best_val_loss"),
                   "decode_time_s": dt}
            save_json(row, C.METRICS_DIR / f"{md.name}_{decoding}.json")
            rows.append(row)
            print(f"{md.name:<22} {decoding:<6} BLEU {metrics['bleu']:.2f}  ROUGE-L {metrics['rougeL']:.2f}  "
                  f"ppl {tf_metrics['ppl']:.1f}  acc {tf_metrics['token_acc']:.3f}  rep {metrics['repetition_rate']:.2f}")

        # attention heatmaps for a few test examples
        if gen.model.uses_attention:
            for k, i in enumerate([0, 1, 2]):
                if i >= len(test):
                    break
                res = gen.generate_from_text(test.loc[i, "input_text"], method="greedy")
                if res.attention is not None and res.tokens:
                    plot_attention(res.attention, res.source_tokens, res.tokens + ["<eos>"],
                                   C.FIGURES_DIR / f"attention_{md.name}_example{k + 1}.png",
                                   title=f"{md.name} - test example {k + 1}")

    table = pd.DataFrame(rows)
    table.to_csv(C.METRICS_DIR / "comparison.csv", index=False)
    cols = ["model", "decoding", "n_test", "test_loss", "perplexity", "token_acc", "bleu", "rouge1", "rouge2",
            "rougeL", "distinct2", "repetition_rate", "title_coverage", "avg_gen_len", "n_params",
            "train_time_min"]
    (C.METRICS_DIR / "comparison.md").write_text(table[cols].round(3).to_markdown(index=False)
                                                  if _has_tabulate() else table[cols].round(3).to_string(), encoding="utf-8")
    plot_metric_comparison(table, ["bleu", "rougeL", "perplexity", "repetition_rate"],
                           C.FIGURES_DIR / "metric_comparison.png")
    if histories:
        plot_learning_curves(histories, C.FIGURES_DIR / "learning_curves.png")

    # side-by-side qualitative table: Input | Reference | Baseline | Attention
    keys = list(generations)
    base = generations[keys[0]][["input_text", "reference"]].head(a.n_side_by_side).copy()
    for (m, d) in keys:
        base[f"{m} ({d})"] = generations[(m, d)]["generated_text"].head(a.n_side_by_side).values
    base["observations"] = ""
    base.to_csv(C.EXAMPLES_DIR / "side_by_side.csv", index=False)
    print("\n", table[cols].round(3).to_string(index=False))


def _has_tabulate():
    try:
        import tabulate  # noqa: F401
        return True
    except ImportError:
        return False


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--models", nargs="*", help="folder names in models/ (default: all trained)")
    p.add_argument("--decoding", nargs="*", default=["greedy", "beam"], choices=["greedy", "beam"])
    p.add_argument("--split", default="test", choices=["val", "test"])
    p.add_argument("--max_examples", type=int, default=0,
                   help="evaluate on a random subset of N test examples (0 = full split)")
    p.add_argument("--n_side_by_side", type=int, default=20)
    main(p.parse_args())
