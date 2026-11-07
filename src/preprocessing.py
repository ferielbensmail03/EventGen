"""Text normalisation, tokenisation and detokenisation.

The SAME functions are used for training, validation, test and inference
(the app imports them too), which guarantees preprocessing consistency.

Design choices (French text):
* Unicode NFC + typographic apostrophes/quotes mapped to ASCII.
* Lower-casing: yes. With ~30k training pairs, keeping case would split the
  vocabulary ("Concert" / "concert") and multiply rare words. Display text is
  re-capitalised by `detokenize`.
* Punctuation kept as separate tokens (. , ! ? : ; ( ) - ' ") because it
  structures the generated sentences.
* French elisions are split after the apostrophe: "l'atelier" -> ["l'", "atelier"],
  so "l'" and "atelier" are both frequent tokens instead of one rare word.
* Hyphenated words stay together ("vide-grenier", "jeune-public").
"""
from __future__ import annotations

import re
import unicodedata

PAD, UNK, SOS, EOS = "<pad>", "<unk>", "<sos>", "<eos>"
SPECIAL_TOKENS = [PAD, UNK, SOS, EOS]

_TRANSLATE = str.maketrans({
    "’": "'", "‘": "'", "ʼ": "'", "´": "'", "`": "'",
    "“": '"', "”": '"', "«": '"', "»": '"', "„": '"',
    "–": "-", "—": "-", "−": "-", "…": "...",
    " ": " ", " ": " ", " ": " ", "​": "",
    "œ": "oe", "Œ": "Oe", "æ": "ae",
})

_ELISION = r"(?:jusqu|lorsqu|puisqu|quoiqu|presqu|qu|[cdjlmnst])'"
_NUMBER = r"[0-9]+(?:[.,][0-9]+)+"                    # 14.30 / 2,5 kept as one token
_WORD = r"[0-9a-zà-öø-ÿ]+(?:-[0-9a-zà-öø-ÿ]+)*"       # vide-grenier, 14h30
_TOKEN_RE = re.compile(rf"aujourd'hui|{_ELISION}|{_NUMBER}|{_WORD}|\.\.\.|[^\sa-z0-9à-öø-ÿ]",
                       re.IGNORECASE)


def normalize_unicode(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    return text.translate(_TRANSLATE)


def normalize(text: str, lowercase: bool = True) -> str:
    """Unicode + whitespace normalisation (+ lowercasing)."""
    if text is None:
        return ""
    text = normalize_unicode(str(text))
    text = re.sub(r"\s+", " ", text).strip()
    return text.lower() if lowercase else text


def tokenize(text: str, lowercase: bool = True) -> list[str]:
    """'Join l'atelier aujourd'hui !' -> ['join', "l'", 'atelier', "aujourd'hui", '!']"""
    return _TOKEN_RE.findall(normalize(text, lowercase))


_NO_SPACE_BEFORE = {".", ",", ")", "...", "%"}
_NO_SPACE_AFTER = {"("}


def detokenize(tokens: list[str], capitalize: bool = True) -> str:
    """Inverse of `tokenize` for display (French typography: space before ! ? : ;)."""
    out = ""
    prev = None
    for tok in tokens:
        if tok in SPECIAL_TOKENS and tok != UNK:
            continue
        if prev is None:
            out = tok
        elif tok in _NO_SPACE_BEFORE or prev.endswith("'") or prev in _NO_SPACE_AFTER:
            out += tok
        else:
            out += " " + tok
        prev = tok
    if capitalize and out:
        out = re.sub(r"(^|[.!?]\s+)([a-zà-ÿ])", lambda m: m.group(1) + m.group(2).upper(), out)
    return out


def truncate_at_sentence(tokens: list[str], max_len: int) -> list[str] | None:
    """Cut a token list to <= max_len tokens, ending on a sentence boundary.

    Returns None when no sentence boundary exists inside the window (the
    example is then discarded rather than ending mid-sentence).
    """
    if len(tokens) <= max_len:
        return tokens
    window = tokens[:max_len]
    for i in range(len(window) - 1, 0, -1):
        if window[i] in {".", "!", "?", "..."}:
            return window[: i + 1]
    return None


# ------------------------------------------------------------------ input serialisation
def serialize_event(title: str, type_labels: list[str] | None) -> str:
    """Structured event -> source sequence fed to the encoder.

    Example: ('Concert - Rod Barthet', ['concert', 'musique'])
             -> 'type : concert , musique | titre : concert - rod barthet'
    Field markers ('type :', 'titre :') let the encoder know which field a word comes from.
    """
    types = " , ".join(type_labels) if type_labels else "non précisé"
    return f"type : {types} | titre : {title}"
