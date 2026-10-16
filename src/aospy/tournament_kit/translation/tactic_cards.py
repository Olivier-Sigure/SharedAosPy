"""Chargement de `data/battle_tactic_cards.json` — transcription manuelle,
verbatim en français, des 6 cartes de tactique de bataille de la saison
2026-27 (`data/Manuel du général/MdG26-27 Tactiques.pdf`, sans couche de
texte comme tout le reste de ce PDF — relevé à la main page par page, même
convention que `warscroll_index.json`/`army_rules.json`). Chargeur pur, pas
de DB, relu à froid à chaque appel.

Ce texte reste en français (la carte source l'est) — contrairement aux
profils d'unité/règles de faction (Wahapedia, anglais), il n'y a pas de repli
possible : ces 6 cartes n'existent nulle part ailleurs que dans ce PDF."""

from __future__ import annotations

import json
import unicodedata
from dataclasses import dataclass
from pathlib import Path

DEFAULT_TACTIC_CARDS_FILE = Path("data") / "battle_tactic_cards.json"


@dataclass(frozen=True)
class SubTactic:
    kind: str  # "Échauffourée" / "Frappe" / "Domination"
    name: str
    flavor: str
    condition: str
    points: int


@dataclass(frozen=True)
class TacticCard:
    number: int
    name_en: str
    title_fr: str
    flavor: str
    special_rule: str | None
    sub_tactics: tuple[SubTactic, ...]


def _normalize(name: str) -> str:
    folded = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    return "".join(folded.lower().split())


def load_tactic_cards(path: str | Path = DEFAULT_TACTIC_CARDS_FILE) -> dict[str, TacticCard]:
    """`{nom anglais (tel qu'utilisé dans un export de liste) -> TacticCard}`.
    Fichier absent -> dict vide (une liste citant une carte tombe alors en
    `rules_unmatched`, jamais un plantage)."""
    p = Path(path)
    if not p.exists():
        return {}
    rows = json.loads(p.read_text(encoding="utf-8"))
    return {
        row["name_en"]: TacticCard(
            number=row["number"],
            name_en=row["name_en"],
            title_fr=row["title_fr"],
            flavor=row["flavor"],
            special_rule=row.get("special_rule"),
            sub_tactics=tuple(
                SubTactic(kind=s["kind"], name=s["name"], flavor=s["flavor"], condition=s["condition"], points=s["points"])
                for s in row["sub_tactics"]
            ),
        )
        for row in rows
    }


def find_tactic_card(cards: dict[str, TacticCard], name: str) -> TacticCard | None:
    """Correspondance exacte puis normalisée (accents/casse) — même
    tolérance que `warscroll_index._lookup_normalized` pour le nom tel que
    cité dans l'export de liste."""
    if name in cards:
        return cards[name]
    target = _normalize(name)
    for key, card in cards.items():
        if _normalize(key) == target:
            return card
    return None
