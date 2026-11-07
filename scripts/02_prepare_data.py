"""Step 2 - cleaning -> pairs -> leakage-safe split -> vocabularies (train only).

Outputs
  data/interim/datatourisme_clean.csv
  data/processed/eventgen_pairs.csv + cleaning_report.json
  data/splits/{train,val,test}.csv
  artifacts/{src_vocab,tgt_vocab,preprocessing_config}.json
"""
import argparse
from dataclasses import asdict

import _bootstrap  # noqa: F401
from src import config as C
from src.data_cleaning import clean_datatourisme
from src.data_loader import load_datatourisme
from src.pairs import build_pairs, group_split, split_report
from src.preprocessing import tokenize
from src.utils import save_json, set_seed
from src.vocabulary import Vocabulary


def main(args):
    C.ensure_dirs()
    cfg = C.DataConfig()
    set_seed(cfg.seed)

    raw = load_datatourisme()
    clean, clean_rep = clean_datatourisme(raw)
    clean.to_csv(C.CLEAN_FILE, index=False)
    print(f"cleaning: {clean_rep['initial_rows']} -> {clean_rep['final_rows']} rows")
    for s in clean_rep["steps"]:
        print(f"   - {s['step']:<28} removed {s['removed']:>6}  ({s['reason']})")

    pairs, pair_rep = build_pairs(clean, cfg)
    pairs.to_csv(C.PAIRS_FILE, index=False)
    print(f"pairs: {pair_rep['rows_in']} -> {pair_rep['rows_out']} (truncated at sentence end: {pair_rep['truncated_targets']})")

    splits = group_split(pairs, cfg)
    for name, d in splits.items():
        d.to_csv(C.SPLIT_FILES[name], index=False)
    sp_rep = split_report(splits)
    print("split:", {k: v["rows"] for k, v in sp_rep.items()})

    # vocabularies from TRAIN only
    tr = splits["train"]
    src_vocab = Vocabulary(cfg.min_freq_src, cfg.max_vocab_src).build(tokenize(s) for s in tr["input_text"])
    tgt_vocab = Vocabulary(cfg.min_freq_tgt, cfg.max_vocab_tgt).build(tokenize(s) for s in tr["target_text"])
    src_vocab.save(C.SRC_VOCAB_FILE)
    tgt_vocab.save(C.TGT_VOCAB_FILE)
    cov = {s: {"src": src_vocab.coverage(tokenize(x) for x in d["input_text"]),
               "tgt": tgt_vocab.coverage(tokenize(x) for x in d["target_text"])} for s, d in splits.items()}
    print(f"vocab: src={len(src_vocab)} tgt={len(tgt_vocab)}  test coverage={cov['test']}")

    save_json({"cleaning": clean_rep, "pairs": pair_rep, "split": sp_rep,
               "vocab": {"src": {k: v for k, v in src_vocab.stats().items() if k != 'top_20'},
                         "tgt": {k: v for k, v in tgt_vocab.stats().items() if k != 'top_20'},
                         "coverage": cov}}, C.CLEANING_REPORT)
    save_json({"data_config": asdict(cfg), "lowercase": True, "unicode": "NFC + ASCII apostrophes/quotes",
               "tokenizer": "regex word tokenizer, French elisions split (l' / d' / qu'), punctuation as tokens",
               "special_tokens": {"<pad>": 0, "<unk>": 1, "<sos>": 2, "<eos>": 3},
               "input_serialization": "type : <labels> | titre : <title>"}, C.PREPROC_FILE)


if __name__ == "__main__":
    main(argparse.ArgumentParser().parse_args())
