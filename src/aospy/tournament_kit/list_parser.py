"""Parse une liste d'armée exportée en texte brut par Warhammer Age of
Sigmar: The App (voir `data/Proposition de listes/*.txt`) en dataclasses.

Format ligne-à-ligne stable observé sur tous les exports : titre, faction,
allégeance optionnelle, en-tête (« General's Handbook », « Drops: N », lores —
« Spell Lore »/« Prayer Lore » selon que la faction lance des sorts ou des
prières, parfois les deux, plus « Manifestation Lore »),
« Battle Tactic Cards: ... », puis des sections « General's Regiment » /
« Regiment N » listant des lignes `Nom (points)` avec des sous-lignes
d'option ` • Option` rattachées à l'unité précédente, des sections optionnelles
« Regiments of Renown » (une ligne `Nom (points totaux)` suivie de ses unités
membres, sans points propres puisqu'inclus dans le prix du régiment) et
« Faction Terrain », et un pied de page « Created with... »/« App: ... »
ignoré.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

_UNIT_RE = re.compile(r"^(?P<name>.+?) \((?P<points>\d+)\)$")
#: Un Faction Terrain payant est exporté avec son coût inline (ex. « Shrine
#: of Dark Tribute (20 Points) »), contrairement à `_UNIT_RE` (juste des
#: chiffres, ex. « Morathi-Khaine (750) ») ou à un terrain gratuit (aucun
#: suffixe, ex. « Nexus Chaotica ») — nécessaire pour que le nom recherché
#: dans le battletome/Wahapedia corresponde au nom canonique de la charte.
_TERRAIN_POINTS_RE = re.compile(r"^(?P<name>.+?) \(\d+ Points\)$")
_OPTION_PREFIX = " • "
_REGIMENT_HEADER_RE = re.compile(r"^(General's Regiment|Regiment \d+)$")


@dataclass(frozen=True)
class UnitEntry:
    name: str
    points: int
    options: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Regiment:
    title: str
    units: list[UnitEntry]


@dataclass(frozen=True)
class RegimentOfRenown:
    name: str
    points: int
    units: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ParsedList:
    title: str
    faction: str
    allegiance: str | None
    drops: int | None
    spell_lore: str | None
    prayer_lore: str | None
    manifestation_lore: str | None
    battle_tactic_cards: list[str]
    regiments: list[Regiment]
    regiments_of_renown: list[RegimentOfRenown]
    faction_terrain: list[str]

    @property
    def base_faction(self) -> str:
        """Faction sans le suffixe d'armée de renom (ex. « Slaves to Darkness »
        pour « Slaves to Darkness | Legion of the First Prince ») — c'est ce
        nom qui indexe `data/warscroll_index.json`, la battletome de base
        restant la même pour une armée de renom."""
        return self.faction.split("|", 1)[0].strip()

    def unique_unit_names(self) -> list[str]:
        """Noms d'unité uniques (dédoublonne p. ex. les entrées Reinforced
        répétées), dans l'ordre d'apparition. Inclut le Faction Terrain et les
        unités membres des Regiments of Renown (le régiment lui-même n'a pas
        de profil d'unité propre — voir `regiments_of_renown`)."""
        seen: dict[str, None] = {}
        for regiment in self.regiments:
            for unit in regiment.units:
                seen.setdefault(unit.name, None)
        for ror in self.regiments_of_renown:
            for name in ror.units:
                seen.setdefault(name, None)
        for name in self.faction_terrain:
            m = _TERRAIN_POINTS_RE.match(name)
            seen.setdefault(m.group("name") if m else name, None)
        return list(seen)


def _next_nonblank(lines: list[str], start: int) -> int:
    i = start
    while i < len(lines) and lines[i].strip() == "":
        i += 1
    return i


def parse_list(text: str) -> ParsedList:
    lines = text.splitlines()

    idx = _next_nonblank(lines, 0)
    title = lines[idx].strip()
    idx = _next_nonblank(lines, idx + 1)
    faction = lines[idx].strip()
    idx += 1

    header_keywords = (
        "General's Handbook", "Drops:", "Spell Lore -", "Prayer Lore -", "Manifestation Lore -",
        "Battle Tactic Cards:",
    )
    allegiance = None
    if idx < len(lines) and lines[idx].strip() and not lines[idx].strip().startswith(header_keywords):
        allegiance = lines[idx].strip()
        idx += 1

    drops = None
    spell_lore = None
    prayer_lore = None
    manifestation_lore = None
    battle_tactic_cards: list[str] = []

    while idx < len(lines):
        stripped = lines[idx].strip()
        if stripped == "":
            idx += 1
            continue
        if stripped.startswith("General's Handbook"):
            idx += 1
            continue
        if stripped.startswith("Drops:"):
            drops = int(stripped.split(":", 1)[1].strip())
            idx += 1
            continue
        if stripped.startswith("Spell Lore -"):
            spell_lore = stripped.split("-", 1)[1].strip()
            idx += 1
            continue
        if stripped.startswith("Prayer Lore -"):
            # domaine de prières — même mécanique que le domaine de sorts,
            # pour les factions à Prêtres (ex. Flesh-eater Courts) plutôt
            # qu'à Sorciers ; une liste peut porter l'un, l'autre, les deux
            # ou aucun.
            prayer_lore = stripped.split("-", 1)[1].strip()
            idx += 1
            continue
        if stripped.startswith("Manifestation Lore -"):
            manifestation_lore = stripped.split("-", 1)[1].strip()
            idx += 1
            continue
        if stripped.startswith("Battle Tactic Cards:"):
            cards_raw = stripped.split(":", 1)[1].strip()
            battle_tactic_cards = [c.strip() for c in cards_raw.split(",") if c.strip()]
            idx += 1
            continue
        break

    regiments: list[Regiment] = []
    regiments_of_renown: list[RegimentOfRenown] = []
    faction_terrain: list[str] = []

    while idx < len(lines):
        raw = lines[idx]
        stripped = raw.strip()
        if stripped == "":
            idx += 1
            continue
        if stripped.startswith("Created with") or stripped.startswith("App:"):
            idx += 1
            continue
        if _REGIMENT_HEADER_RE.match(stripped):
            regiment_title = stripped
            idx += 1
            units: list[UnitEntry] = []
            while idx < len(lines) and lines[idx].strip() != "":
                entry_raw = lines[idx]
                entry_stripped = entry_raw.strip()
                if entry_raw.startswith(_OPTION_PREFIX):
                    if units:
                        units[-1].options.append(entry_stripped[1:].strip())
                else:
                    m = _UNIT_RE.match(entry_stripped)
                    if m:
                        units.append(UnitEntry(name=m.group("name"), points=int(m.group("points"))))
                idx += 1
            regiments.append(Regiment(title=regiment_title, units=units))
            continue
        if stripped == "Regiments of Renown":
            idx += 1
            while idx < len(lines) and lines[idx].strip() != "":
                entry_stripped = lines[idx].strip()
                m = _UNIT_RE.match(entry_stripped)
                if m:
                    regiments_of_renown.append(RegimentOfRenown(name=m.group("name"), points=int(m.group("points"))))
                elif regiments_of_renown:
                    regiments_of_renown[-1].units.append(entry_stripped)
                idx += 1
            continue
        if stripped == "Faction Terrain":
            idx += 1
            while idx < len(lines) and lines[idx].strip() != "":
                faction_terrain.append(lines[idx].strip())
                idx += 1
            continue
        idx += 1

    return ParsedList(
        title=title,
        faction=faction,
        allegiance=allegiance,
        drops=drops,
        spell_lore=spell_lore,
        prayer_lore=prayer_lore,
        manifestation_lore=manifestation_lore,
        battle_tactic_cards=battle_tactic_cards,
        regiments=regiments,
        regiments_of_renown=regiments_of_renown,
        faction_terrain=faction_terrain,
    )


def parse_list_file(path: str | Path) -> ParsedList:
    return parse_list(Path(path).read_text(encoding="utf-8"))
