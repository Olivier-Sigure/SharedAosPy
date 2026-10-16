"""Tests : parsing d'une liste brute (export Warhammer Age of Sigmar: The App)
sur les fichiers réels de `data/Proposition de listes/` (format stable)."""

from __future__ import annotations

from aospy.tournament_kit.list_parser import RegimentOfRenown, parse_list, parse_list_file

_LISTS_DIR = "data/Proposition de listes"


def test_parses_regiments_options_and_terrain():
    pl = parse_list_file(f"{_LISTS_DIR}/LRL L3 Avengers Wardens.txt")

    assert pl.faction == "Lumineth Realm-lords"
    assert pl.base_faction == "Lumineth Realm-lords"
    assert pl.allegiance == "Warhost of Duality (20 Points)"
    assert pl.drops == 4
    assert pl.spell_lore == "Lore of Hysh"
    assert pl.manifestation_lore == "Manifestations of Hysh"
    assert pl.battle_tactic_cards == ["Burning for Vengeance", "Flanking Firestorm"]
    assert pl.faction_terrain == ["Shrine Luminor"]

    general_regiment = pl.regiments[0]
    assert general_regiment.title == "General's Regiment"
    first_unit = general_regiment.units[0]
    assert first_unit.name == "Ellania and Ellathor, Eclipsian Warsages"
    assert first_unit.points == 310
    assert first_unit.options == ["General"]

    reinforced = general_regiment.units[1]
    assert reinforced.name == "Vanari Auralan Wardens"
    assert reinforced.options == ["Reinforced"]


def test_unique_unit_names_dedupes_and_includes_terrain():
    pl = parse_list_file(f"{_LISTS_DIR}/LRL L3 Avengers Wardens.txt")
    names = pl.unique_unit_names()
    # "Vanari Auralan Wardens" apparaît deux fois dans la liste (deux unités
    # distinctes, même nom) -> un seul profil à chercher.
    assert names.count("Vanari Auralan Wardens") == 1
    assert "Shrine Luminor" in names


def test_option_with_embedded_point_cost_kept_as_single_option():
    pl = parse_list_file(f"{_LISTS_DIR}/STD L3 Cavalerie 2000.txt")
    daemon_prince = pl.regiments[1].units[0]
    assert daemon_prince.name == "Daemon Prince"
    assert "Radiance of Dark Glory - (20) Points" in daemon_prince.options


def test_zero_point_companion_units_are_parsed():
    pl = parse_list_file(f"{_LISTS_DIR}/STD L3 Cavalerie 2000.txt")
    last_regiment = pl.regiments[-1]
    names_points = [(u.name, u.points) for u in last_regiment.units]
    assert ("Singri Brand", 0) in names_points
    assert ("The Oathsworn Kin", 0) in names_points


def test_army_of_renown_splits_faction_from_base_faction():
    pl = parse_list_file(f"{_LISTS_DIR}/STD L3 First Prince 1980.txt")
    assert pl.faction == "Slaves to Darkness | Legion of the First Prince"
    assert pl.base_faction == "Slaves to Darkness"
    assert pl.allegiance == "Army of Renown"


def test_regiments_of_renown_parsed_with_member_units():
    pl = parse_list_file(f"{_LISTS_DIR}/STD L3 Prince Warriors Launcher.txt")
    assert pl.regiments_of_renown == [RegimentOfRenown(name="The Exiled One", points=390, units=["Skarbrand"])]
    assert "Skarbrand" in pl.unique_unit_names()


def test_parse_list_handles_missing_optional_lores():
    text = (
        "STD - Sample 2000/2000 pts\n\n"
        "Slaves to Darkness\n"
        "Despoilers\n"
        "General's Handbook 2026-27\n"
        "Drops: 1\n\n"
        "General's Regiment\n"
        "Daemon Prince (250)\n"
        " • General\n\n"
        "Created with Warhammer Age of Sigmar: The App\n"
        "App: 1.37.0 | Data: 476\n"
    )
    pl = parse_list(text)
    assert pl.spell_lore is None
    assert pl.manifestation_lore is None
    assert pl.battle_tactic_cards == []
    assert pl.regiments[0].units[0].name == "Daemon Prince"
