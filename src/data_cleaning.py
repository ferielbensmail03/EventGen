"""Cleaning of the DATAtourisme source.

Every step logs how many rows it removes, so the cleaning report in the
technical report is computed, not invented. Raw files are never overwritten:
the result is written to data/interim/.
"""
from __future__ import annotations

import html
import re
import unicodedata

import pandas as pd

from .data_loader import decode_datatourisme
from .preprocessing import normalize, normalize_unicode

URL_RE = re.compile(r"(?:https?://|www\.)\S+|\b[\w-]+\.(?:fr|com|org|net|eu|bzh|info)(?:/\S*)?\b", re.I)
EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
PHONE_RE = re.compile(r"(?:\+33\s?|0)[1-9](?:[\s.-]?\d{2}){4}")
TAG_RE = re.compile(r"<[^>]{1,200}>")
ESCAPED_UNICODE_RE = re.compile(r"\\u([0-9a-fA-F]{4})")
# emojis, pictographs, dingbats, private-use and control characters
JUNK_RE = re.compile(
    "[\U0001F000-\U0001FAFF☀-➿-️‍←-⇿■-◿⬀-⯿]"
)
REPEAT_PUNCT_RE = re.compile(r"([!?,;:])\1+")
DOTS_RE = re.compile(r"\.{3,}")
BULLET_RE = re.compile(r"(^|\s)[•▪●◆►✓✔➢➤\*]+\s*")


def clean_text(text: str | None) -> str:
    """Conservative cleaning: removes noise, keeps sentences and punctuation."""
    if text is None or (isinstance(text, float) and pd.isna(text)):
        return ""
    t = html.unescape(str(text))
    # encoding problem found in EDA: literal escape sequences such as "BROUNÏAK"
    t = ESCAPED_UNICODE_RE.sub(lambda m: chr(int(m.group(1), 16)), t)
    t = t.replace("\\n", " ").replace("\\t", " ")
    t = re.sub(r"\\([.\-_*#()\[\]!])", r"\1", t)   # markdown escapes: www\.site\-x\.com
    t = TAG_RE.sub(" ", t)
    t = normalize_unicode(t)
    t = "".join(ch for ch in t if unicodedata.category(ch)[0] != "C" or ch in "\n\t")
    t = EMAIL_RE.sub(" ", t)             # e-mails first (their domain would match URL_RE)
    t = URL_RE.sub(" ", t)               # privacy + no information for generation
    t = PHONE_RE.sub(" ", t)
    t = JUNK_RE.sub(" ", t)
    t = BULLET_RE.sub(r"\1", t)
    t = re.sub(r"\s*\n+\s*", " ", t)     # line breaks -> single space
    t = DOTS_RE.sub("...", t)
    t = REPEAT_PUNCT_RE.sub(r"\1", t)
    t = re.sub(r"([A-Za-zÀ-ÿ]{2,})([.!?])([A-ZÀ-Ý][a-zà-ÿ])", r"\1\2 \3", t)   # 'fin.Venez' -> 'fin. Venez'
    t = re.sub(r"\(\s*\)", " ", t)       # empty brackets left by removed URLs
    t = re.sub(r"(?<=[:;,])(\s*[/|])+", "", t)     # 'Infos : / ' left by removed contacts
    t = re.sub(r"(\s[/|])+\s*$", "", t)
    t = re.sub(r"\s+([,.])", r"\1", t)
    t = re.sub(r"\s+", " ", t).strip(" -:;,/|")
    return t


def clean_datatourisme(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Return (clean dataframe, report). Each removal step is counted."""
    report: dict = {"source": "DATAtourisme (data.gouv.fr) - flux evenements",
                    "initial_rows": int(len(raw)), "steps": []}

    def log(step: str, before: int, after: int, why: str):
        report["steps"].append({"step": step, "removed": int(before - after),
                                "remaining": int(after), "reason": why})

    df = decode_datatourisme(raw)
    report["empty_columns_dropped"] = [c for c in raw.columns if raw[c].isna().all()]

    n = len(df)
    df = df.drop_duplicates(subset="id")
    log("duplicate_event_id", n, len(df), "same DATAtourisme URI twice")

    n = len(df)
    df = df[df["description"].notna() & df["description"].astype(str).str.strip().ne("")]
    log("missing_description", n, len(df), "no target text: cannot be a training pair (never fabricated)")

    n = len(df)
    df = df[df["title"].notna() & df["title"].astype(str).str.strip().ne("")]
    log("missing_title", n, len(df), "title is the essential input field")

    n = len(df)
    df = df[(df["description_lang"].fillna("fr") == "fr") & (df["title_lang"].fillna("fr") == "fr")]
    log("non_french", n, len(df), "single-language (French) model")

    df["title_clean"] = df["title"].map(clean_text)
    df["description_clean"] = df["description"].map(clean_text)
    df["n_type_labels"] = df["type_labels"].map(len)

    n = len(df)
    df = df[df["description_clean"].str.len() > 0]
    log("empty_after_cleaning", n, len(df), "description contained only URL / phone / e-mail / tags")

    n = len(df)
    same = df["description_clean"].map(normalize) == df["title_clean"].map(normalize)
    df = df[~same]
    log("description_equals_title", n, len(df), "target identical to input: nothing to generate")

    df["title_norm"] = df["title_clean"].map(normalize)
    df["desc_norm"] = df["description_clean"].map(normalize)

    n = len(df)
    df = df.drop_duplicates(subset=["title_norm", "desc_norm"])
    log("duplicate_pair", n, len(df), "same (title, description) published twice (recurring dates)")

    n = len(df)
    df = df.drop_duplicates(subset=["desc_norm"])
    log("duplicate_description", n, len(df),
        "identical description shared by different events (boilerplate); one kept to avoid memorisation and leakage")

    report["corrupted_type_rows_kept"] = int((df["n_type_labels"] == 0).sum())
    report["final_rows"] = int(len(df))
    keep = ["id", "type", "type_labels", "title", "title_clean", "description", "description_clean",
            "title_norm", "desc_norm"]
    return df[keep].reset_index(drop=True), report
