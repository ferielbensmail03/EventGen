"""Loaders for every raw source.

Raw files are only READ here, never modified. Each loader returns a pandas
DataFrame; DATAtourisme literals (stored as Python-dict strings such as
"{'@value': '...', '@language': 'fr'}") are decoded into plain text columns.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pandas as pd

from .config import RAW_FILES

# Tokens of the DATAtourisme `type` path that carry no information
GENERIC_TYPE_TOKENS = {
    "schema:Event", "EntertainmentAndEvent", "PointOfInterest", "urn:resource",
    "schema:Product", "Product", "olo:OrderedList", "PlaceOfInterest",
    "schema:LocalBusiness", "schema:Place",
}

# English ontology class -> French label (used to build the model input)
TYPE_FR = {
    "CulturalEvent": "événement culturel", "SportsEvent": "événement sportif",
    "ShowEvent": "spectacle", "SocialEvent": "événement social", "SaleEvent": "vente",
    "MusicEvent": "musique", "Concert": "concert", "Market": "marché",
    "LocalAnimation": "animation locale", "ChildrensEvent": "jeune public",
    "TraditionalCelebration": "fête traditionnelle", "ExhibitionEvent": "exposition",
    "Exhibition": "exposition", "TheaterEvent": "théâtre", "Visit": "visite",
    "Practice": "pratique", "Traineeship": "stage", "Conference": "conférence",
    "Festival": "festival", "Rambling": "randonnée", "SportsCompetition": "compétition sportive",
    "BusinessEvent": "événement professionnel", "Game": "jeu", "ScreeningEvent": "projection",
    "SportsAndLeisurePlace": "lieu de loisirs", "FairOrShow": "foire ou salon",
    "TrainingWorkshop": "atelier", "CulturalSite": "site culturel", "GarageSale": "vide-grenier",
    "Reading": "lecture", "BricABrac": "brocante", "OpenDay": "portes ouvertes",
    "MovieTheater": "cinéma", "Cinema": "cinéma", "Theater": "théâtre", "Parade": "défilé",
    "VisualArtsEvent": "arts visuels", "SportsDemonstration": "démonstration sportive",
    "ActivityProvider": "prestataire d'activités", "CulturalActivityProvider": "prestataire culturel",
    "Landform": "site naturel", "NaturalHeritage": "patrimoine naturel",
    "Commemoration": "commémoration", "Congress": "congrès", "CircusPlace": "cirque",
    "Cirque": "cirque", "Opera": "opéra", "Carnival": "carnaval", "Rally": "rallye",
    "Recital": "récital", "ReligiousEvent": "événement religieux",
    "IntroductionCourse": "initiation", "Seminar": "séminaire", "ArtistSigning": "dédicace",
    "Tour": "circuit", "WalkingTour": "balade", "Accommodation": "hébergement",
    "LodgingBusiness": "hébergement", "Dance": "danse", "DanceEvent": "danse",
    "Workshop": "atelier", "Competition": "compétition", "Tasting": "dégustation",
    "Fair": "foire", "Show": "spectacle", "Course": "cours", "Meeting": "rencontre",
    "Harvest": "récolte", "PilgrimageAndProcession": "pèlerinage", "CraftsmanShop": "artisanat",
    "Store": "boutique", "Cinematheque": "cinémathèque", "RentalAccommodation": "hébergement",
    "ArcheologicalSite": "site archéologique",
}


def _literal_value(s):
    """Decode "{'@value': 'x', '@language': 'fr'}" -> ('x', 'fr'). Robust to junk."""
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return None, None
    if not isinstance(s, str):
        return str(s), None
    try:
        v = ast.literal_eval(s)
    except (ValueError, SyntaxError):
        return s, None                 # already plain text
    if isinstance(v, dict):
        return v.get("@value"), v.get("@language")
    if isinstance(v, list):            # several literals: keep the French one first
        for item in v:
            if isinstance(item, dict) and item.get("@language") == "fr":
                return item.get("@value"), "fr"
        if v and isinstance(v[0], dict):
            return v[0].get("@value"), v[0].get("@language")
    return str(v), None


def parse_type_path(type_str: str) -> list[str]:
    """'schema:Event/CulturalEvent/.../Concert/urn:resource' -> ['concert', 'événement culturel'].

    Returns [] for the 1 279 corrupted values ('u/r/n/:/r/e/s/o/u/r/c/e').
    """
    if not isinstance(type_str, str):
        return []
    parts = type_str.split("/")
    if sum(len(p) == 1 for p in parts) > len(parts) / 2:   # corrupted: split char by char
        return []
    labels: list[str] = []
    for p in parts:
        if p in GENERIC_TYPE_TOKENS:
            continue
        p = p.split(":")[-1]                                # schema:MusicEvent -> MusicEvent
        if p in GENERIC_TYPE_TOKENS or not p:
            continue
        fr = TYPE_FR.get(p)
        if fr is None:                                      # unknown class: keep it readable
            continue
        if fr not in labels:
            labels.append(fr)
    # most specific labels first: put generic "événement ..." classes last
    labels.sort(key=lambda x: x.startswith("événement"))
    return labels


def load_datatourisme(path: Path | None = None) -> pd.DataFrame:
    path = Path(path or RAW_FILES["datatourisme"])
    df = pd.read_parquet(path)
    return df


def decode_datatourisme(df: pd.DataFrame) -> pd.DataFrame:
    """Add decoded columns: title, title_lang, description, description_lang, type_labels."""
    out = df.copy()
    t = out["label"].map(_literal_value)
    c = out["comment"].map(_literal_value)
    out["title"] = t.map(lambda x: x[0])
    out["title_lang"] = t.map(lambda x: x[1])
    out["description"] = c.map(lambda x: x[0])
    out["description_lang"] = c.map(lambda x: x[1])
    out["type_labels"] = out["type"].map(parse_type_path)
    return out


def load_datatourisme_csv_gz(path: Path | None = None) -> pd.DataFrame:
    return pd.read_csv(path or RAW_FILES["datatourisme_csv_gz"], sep=None, engine="python")


def load_huggingface(path: Path | None = None) -> pd.DataFrame:
    return pd.read_csv(path or RAW_FILES["huggingface"])


def load_events_csv(path: Path | None = None) -> pd.DataFrame:
    return pd.read_csv(path or RAW_FILES["events_csv"])


def load_mendeley(root: Path | None = None) -> dict[str, pd.DataFrame]:
    """Every CSV found under data/raw/mendeley, keyed by 'folder/file'."""
    root = Path(root or RAW_FILES["mendeley"])
    out = {}
    for f in sorted(root.rglob("*.csv")):
        out[f"{f.parent.name}/{f.name}"] = pd.read_csv(f)
    return out


def available_sources() -> dict[str, bool]:
    return {k: Path(v).exists() for k, v in RAW_FILES.items()}
