"""Chargement de `data/generic_core_abilities.json` — vérbatim français de
*toutes* les aptitudes génériques utilisables à chaque phase, transcrites
depuis `data/Manuel du général/MdG26-27 Aptitudes.pdf` (même PDF que
`season_rules.json`, qui n'en transcrit que la page 5 — les 4 règles de
saison, incluses dans tous les modes). Ce fichier-ci est le superset complet,
inclus uniquement en mode `fr-extended` (`pdf_builder.build_roster_pdf`).
Chargeur pur, pas de DB, relu à froid à chaque appel — même convention que
`season_rules.py`, à ceci près qu'il lit aussi `points_type`/`points` (les
"Ordres" du PDF coûtent des points de commandement, ce que les 4 règles de
saison ne font jamais) pour que le badge hexagonal "PC" de
`warscroll_card._cast_pill` s'affiche. Fichier absent ou `[]` -> liste vide,
jamais un plantage."""

from __future__ import annotations

import json
from pathlib import Path

from .wahapedia_lookup import AbilityEntry

DEFAULT_GENERIC_CORE_ABILITIES_FILE = Path("data") / "generic_core_abilities.json"


def load_generic_core_abilities(path: str | Path = DEFAULT_GENERIC_CORE_ABILITIES_FILE) -> list[AbilityEntry]:
    p = Path(path)
    if not p.exists():
        return []
    rows = json.loads(p.read_text(encoding="utf-8"))
    return [
        AbilityEntry(
            name=row["name"],
            description=row["description"],
            legend="",
            condition=row.get("condition", ""),
            keywords=row.get("keywords", ""),
            ability_phase=row.get("ability_phase", ""),
            points_type=row.get("points_type", ""),
            points=row.get("points", ""),
        )
        for row in rows
    ]
