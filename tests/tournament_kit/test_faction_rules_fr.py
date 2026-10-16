"""Tests : chargement et application des correctifs/additions vérbatim
français de `data/faction_rules_fr.json` (`faction_rules_fr.py`)."""

from __future__ import annotations

import json

from aospy.tournament_kit.translation.faction_rules_fr import (
    FactionRulesFr, apply_fr_overrides, get_faction_category_overrides, get_unit_ability_overrides,
    load_faction_rules_fr,
)
from aospy.tournament_kit.translation.wahapedia_lookup import AbilityEntry

_SAMPLE = {
    "factions": {
        "Slaves to Darkness": {
            "rules": {
                "battle_traits": [
                    {
                        "wahapedia_name": "DARK BLESSINGS",
                        "name": "Bénédictions Sombres",
                        "description": "<b>Texte français final.</b>",
                        "origin": "BT",
                        "provenance": {"bt_text": "texte brut", "errata_patch": None, "errata_source": None},
                    },
                    {
                        "name": "Rage d'Aqshy",
                        "description": "Aptitude propre à Scourge of Aqshy, absente de Wahapedia.",
                        "condition": "Passive",
                        "ability_phase": "",
                        "origin": "Aqshy",
                    },
                ],
                "formations": [
                    {"scope": "Despoilers", "wahapedia_name": "RUTHLESS RAIDERS", "name": "Pillards Impitoyables", "description": "...", "origin": "BT"},
                ],
            },
            "units": {
                "Chaos Lord on Karkadrak": {
                    "abilities": [
                        {"wahapedia_name": "TERROR OF THE DARK GODS", "name": "Terreur des Dieux Sombres", "description": "...", "origin": "FP"},
                    ],
                },
            },
        },
    },
}


def test_load_faction_rules_fr_missing_file_returns_empty(tmp_path):
    frf = load_faction_rules_fr(tmp_path / "does-not-exist.json")
    assert frf == FactionRulesFr()
    assert get_faction_category_overrides(frf, "Slaves to Darkness", "battle_traits") == []
    assert get_unit_ability_overrides(frf, "Slaves to Darkness", "Chaos Lord on Karkadrak") == []


def test_load_faction_rules_fr_reads_curated_factions(tmp_path):
    path = tmp_path / "faction_rules_fr.json"
    path.write_text(json.dumps(_SAMPLE), encoding="utf-8")
    frf = load_faction_rules_fr(path)
    assert "Slaves to Darkness" in frf.factions
    assert "Lumineth Realm-lords" not in frf.factions


def test_get_faction_category_overrides_flat_category_no_scope(tmp_path):
    frf = load_faction_rules_fr(_write(tmp_path))
    rows = get_faction_category_overrides(frf, "Slaves to Darkness", "battle_traits")
    assert [r["name"] for r in rows] == ["Bénédictions Sombres", "Rage d'Aqshy"]


def test_get_faction_category_overrides_filters_by_scope(tmp_path):
    frf = load_faction_rules_fr(_write(tmp_path))
    assert [r["name"] for r in get_faction_category_overrides(frf, "Slaves to Darkness", "formations", "Despoilers")] == ["Pillards Impitoyables"]
    assert get_faction_category_overrides(frf, "Slaves to Darkness", "formations", "Warhost of Duality") == []


def test_get_faction_category_overrides_unknown_faction_or_category(tmp_path):
    frf = load_faction_rules_fr(_write(tmp_path))
    assert get_faction_category_overrides(frf, "Nighthaunt", "battle_traits") == []
    assert get_faction_category_overrides(frf, "Slaves to Darkness", "spell_lores") == []


def test_get_unit_ability_overrides(tmp_path):
    frf = load_faction_rules_fr(_write(tmp_path))
    rows = get_unit_ability_overrides(frf, "Slaves to Darkness", "Chaos Lord on Karkadrak")
    assert [r["name"] for r in rows] == ["Terreur des Dieux Sombres"]
    assert get_unit_ability_overrides(frf, "Slaves to Darkness", "Not A Real Unit") == []


def test_apply_fr_overrides_patches_existing_entry_by_wahapedia_name():
    entries = [AbilityEntry(name="DARK BLESSINGS", description="original EN", legend="", condition="Passive", ability_phase="Hero Phase")]
    overrides = [{"wahapedia_name": "DARK BLESSINGS", "name": "Bénédictions Sombres", "description": "texte FR", "origin": "BT"}]
    result = apply_fr_overrides(entries, overrides)
    assert len(result) == 1
    patched = result[0]
    assert patched.name == "Bénédictions Sombres"
    assert patched.description == "texte FR"
    # champs hérités de l'entrée Wahapedia d'origine, jamais retranscrits :
    assert patched.condition == "Passive"
    assert patched.ability_phase == "Hero Phase"
    assert "BT" in patched.keywords


def test_apply_fr_overrides_adds_standalone_entry_without_wahapedia_match():
    overrides = [{"name": "Rage d'Aqshy", "description": "texte FR", "condition": "Passive", "ability_phase": "", "origin": "Aqshy"}]
    result = apply_fr_overrides([], overrides)
    assert len(result) == 1
    assert result[0].name == "Rage d'Aqshy"
    assert "Aqshy" in result[0].keywords


def test_apply_fr_overrides_no_overrides_returns_entries_unchanged():
    entries = [AbilityEntry(name="X", description="Y", legend="")]
    assert apply_fr_overrides(entries, []) is entries


def _write(tmp_path):
    path = tmp_path / "faction_rules_fr.json"
    path.write_text(json.dumps(_SAMPLE), encoding="utf-8")
    return path
