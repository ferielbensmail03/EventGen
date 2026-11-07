"""Step 5 - automatic error analysis on the generated test descriptions.

Each generated example is tagged with the failure types it shows:
  repetition         a 3-gram is repeated (decoder loop)
  too_short          output < 50% of the reference length
  no_eos             reached max_len without <eos> (incomplete sentence)
  missing_title_info none of the title's content words appear (and they were producible)
  unk_heavy_ref      >= 15% of reference tokens are out of vocabulary (dataset limitation)
  generic            output is one of the 20 most frequent outputs (mode collapse)
Then the worst examples per tag are written to results/generated_examples/error_analysis.md
for manual commentary in the report.
"""
import argparse

import pandas as pd

import _bootstrap  # noqa: F401
from src import config as C


def tag_errors(per: pd.DataFrame, max_len: int = 60) -> pd.DataFrame:
    per = per.copy()
    frequent = set(per["generated"].value_counts().head(20).index)
    per["too_short"] = per["gen_len"] < 0.5 * per["ref_len"]
    per["no_eos"] = per["gen_len"] >= max_len
    per["missing_title_info"] = per["title_coverage"].fillna(1.0) == 0
    per["unk_heavy_ref"] = per["ref_unk_rate"].fillna(0) >= 0.15
    per["generic"] = per["generated"].isin(frequent) & (per["generated"].map(per["generated"].value_counts()) > 2)
    return per


TAGS = ["repetition", "too_short", "no_eos", "missing_title_info", "unk_heavy_ref", "generic"]


def main(a):
    files = sorted(C.EXAMPLES_DIR.glob("*_greedy.csv")) + sorted(C.EXAMPLES_DIR.glob("*_beam.csv"))
    if not files:
        raise SystemExit("Run scripts/04_evaluate.py first.")
    summary, md = [], ["# Error analysis (automatically selected examples)\n"]
    for f in files:
        per = tag_errors(pd.read_csv(f))
        name = f.stem
        summary.append({"run": name, **{t: round(100 * per[t].mean(), 1) for t in TAGS},
                        "rougeL_mean": round(100 * per["rougeL"].mean(), 2)})
        md.append(f"\n## {name}\n")
        for t in TAGS:
            ex = per[per[t]].sort_values("rougeL").head(a.per_tag)
            if ex.empty:
                continue
            md.append(f"\n### {t} - {100 * per[t].mean():.1f}% of test outputs\n")
            for _, r in ex.iterrows():
                md.append(f"- **Input:** {r['input_text']}\n  - **Reference:** {r['reference']}\n"
                          f"  - **Generated:** {r['generated_text']}\n  - ROUGE-L {100 * r['rougeL']:.1f}\n")
        best = per.sort_values("rougeL", ascending=False).head(a.per_tag)
        md.append("\n### best examples (highest ROUGE-L)\n")
        for _, r in best.iterrows():
            md.append(f"- **Input:** {r['input_text']}\n  - **Reference:** {r['reference']}\n"
                      f"  - **Generated:** {r['generated_text']}\n  - ROUGE-L {100 * r['rougeL']:.1f}\n")
    s = pd.DataFrame(summary)
    s.to_csv(C.METRICS_DIR / "error_rates.csv", index=False)
    (C.EXAMPLES_DIR / "error_analysis.md").write_text("\n".join(md), encoding="utf-8")
    print("% of test outputs showing each failure type:\n", s.to_string(index=False))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--per_tag", type=int, default=3)
    main(p.parse_args())
