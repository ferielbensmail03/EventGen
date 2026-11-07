"""Step 1 - exploratory analysis of every raw source -> results/eda/."""
import json

import _bootstrap  # noqa: F401
from src.config import ensure_dirs
from src.eda import run_all

if __name__ == "__main__":
    ensure_dirs()
    res = run_all(save=True)
    for name, r in res.items():
        print(f"\n=== {name} ===")
        print(json.dumps(r, indent=1, ensure_ascii=False, default=str)[:1500])
    print("\nSaved tables, JSON and figures to results/eda/")
