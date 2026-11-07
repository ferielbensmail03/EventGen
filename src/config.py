"""Central configuration for EventGen.

Every path and hyper-parameter lives here so that training, evaluation,
inference and the Streamlit app all use exactly the same settings.
The configuration actually used for a run is saved next to its checkpoint.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# ---------------------------------------------------------------- paths
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
INTERIM_DIR = DATA_DIR / "interim"
PROCESSED_DIR = DATA_DIR / "processed"
SPLITS_DIR = DATA_DIR / "splits"
ARTIFACTS_DIR = ROOT / "artifacts"          # vocabularies + preprocessing config
MODELS_DIR = ROOT / "models"
RESULTS_DIR = ROOT / "results"
FIGURES_DIR = RESULTS_DIR / "figures"
METRICS_DIR = RESULTS_DIR / "metrics"
EXAMPLES_DIR = RESULTS_DIR / "generated_examples"
EDA_DIR = RESULTS_DIR / "eda"

RAW_FILES = {
    "datatourisme": RAW_DIR / "datatourisme" / "dd0510e1-5be5-491d-bbba-3bd2c37371c2.parquet",
    "datatourisme_csv_gz": RAW_DIR / "datatourisme" / "evenements.csv.gz",
    "huggingface": RAW_DIR / "huggingface" / "dataset_a_events.csv",
    "events_csv": RAW_DIR / "events_csv" / "Events.csv",
    "mendeley": RAW_DIR / "mendeley",
}

CLEAN_FILE = INTERIM_DIR / "datatourisme_clean.csv"
PAIRS_FILE = PROCESSED_DIR / "eventgen_pairs.csv"
CLEANING_REPORT = PROCESSED_DIR / "cleaning_report.json"
SPLIT_FILES = {s: SPLITS_DIR / f"{s}.csv" for s in ("train", "val", "test")}
SRC_VOCAB_FILE = ARTIFACTS_DIR / "src_vocab.json"
TGT_VOCAB_FILE = ARTIFACTS_DIR / "tgt_vocab.json"
PREPROC_FILE = ARTIFACTS_DIR / "preprocessing_config.json"


@dataclass
class DataConfig:
    seed: int = 42
    train_ratio: float = 0.8
    val_ratio: float = 0.1
    test_ratio: float = 0.1
    min_target_tokens: int = 8        # shorter descriptions carry almost no information
    max_target_tokens: int = 60       # longer ones are cut at the last sentence end
    max_source_tokens: int = 40
    min_freq_src: int = 2
    min_freq_tgt: int = 3
    max_vocab_src: int = 20000
    max_vocab_tgt: int = 20000


@dataclass
class ModelConfig:
    model_type: str = "baseline"      # "baseline" | "attention"
    emb_dim: int = 128
    hid_dim: int = 256
    n_layers: int = 1
    dropout: float = 0.3
    attn_dim: int = 256


@dataclass
class TrainConfig:
    batch_size: int = 32
    lr: float = 1e-3
    epochs: int = 30
    teacher_forcing: float = 0.5
    clip: float = 1.0
    patience: int = 4                  # early stopping on validation loss
    lr_patience: int = 1               # ReduceLROnPlateau
    lr_factor: float = 0.5
    num_workers: int = 0
    subset: int | None = None          # train on N examples only (smoke tests)
    tag: str = ""                      # suffix for experiment folders (e.g. "tf0.0")
    resume: bool = False               # continue from models/<name>/best.pt
    max_minutes: float | None = None   # stop after the epoch that exceeds this budget


@dataclass
class GenerationConfig:
    max_len: int = 60
    beam_width: int = 3
    length_penalty: float = 0.7        # GNMT-style: score / ((5+len)/6)^alpha
    no_repeat_ngram: int = 0           # 0 = disabled (set 3 in the app to reduce loops)
    block_unk: bool = True             # never emit <unk> at inference
    clean_output: bool = False         # decoding rules for the app, off for the reported metrics


@dataclass
class ExperimentConfig:
    data: DataConfig = field(default_factory=DataConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    train: TrainConfig = field(default_factory=TrainConfig)
    gen: GenerationConfig = field(default_factory=GenerationConfig)

    def to_dict(self) -> dict:
        return asdict(self)

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def from_dict(cls, d: dict) -> "ExperimentConfig":
        return cls(
            data=DataConfig(**d.get("data", {})),
            model=ModelConfig(**d.get("model", {})),
            train=TrainConfig(**d.get("train", {})),
            gen=GenerationConfig(**d.get("gen", {})),
        )


def experiment_dir(model_type: str, tag: str = "") -> Path:
    name = model_type if not tag else f"{model_type}_{tag}"
    return MODELS_DIR / name


def ensure_dirs() -> None:
    for d in (INTERIM_DIR, PROCESSED_DIR, SPLITS_DIR, ARTIFACTS_DIR, MODELS_DIR,
              FIGURES_DIR, METRICS_DIR, EXAMPLES_DIR, EDA_DIR):
        d.mkdir(parents=True, exist_ok=True)
