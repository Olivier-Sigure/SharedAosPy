"""Test d'intégration léger : assemblage du PDF avec une liste, l'index, le
battletome et le repli Wahapedia réels (nécessite l'extra [roster])."""

from __future__ import annotations

import pytest

pytest.importorskip("reportlab")
pytest.importorskip("pypdf")

from pypdf import PdfReader

from aospy.tournament_kit.pdf_builder import build_roster_pdf


def test_build_roster_pdf_produces_cover_plus_rules_plus_unique_unit_pages(tmp_path):
    out_path = tmp_path / "out.pdf"
    result = build_roster_pdf(
        "data/Proposition de listes/LRL L3 Avengers Wardens.txt",
        out_path=out_path,
    )

    assert result.output_path == out_path
    assert result.units_unmatched == []
    assert result.rules_unmatched == []
    assert result.wahapedia_used == []
    # Traits de Bataille / la Formation choisie (Warhost of Duality) / le
    # domaine de sorts choisi / le domaine de manifestations choisi sont des
    # cartes maison Wahapedia, pas des pages de battletome copiées (cf.
    # `_WAHAPEDIA_RULE_CATEGORIES` + le bloc dédié pour les 2 derniers) —
    # seules les cartes de tactique restent des pages French copiées. Traits
    # Héroïques/Artefacts de Pouvoir n'apparaissent plus en bloc générique :
    # cette liste choisit "Flawless Commander" (Vanari Lord Regent) et
    # "Phoenix Stone" (Hurakan Windmage), résolus par unité et rattachés à
    # leur carte plutôt que listés pour toute la faction (cf.
    # `WahapediaLookup.find_unit_enhancement`).
    assert result.rules_included == [
        "Règles de Saison 2026-27",
        "Traits de Bataille",
        "Formation — Warhost of Duality",
        "Domaine de Sorts — Lore of Hysh",
        "Domaine de Manifestations — Manifestations of Hysh",
        "Burning for Vengeance",
        "Flanking Firestorm",
        "Trait Héroïque : FLAWLESS COMMANDER → Vanari Lord Regent",
        "Artefact de Pouvoir : PHOENIX STONE → Hurakan Windmage",
    ]
    assert out_path.exists()

    reader = PdfReader(str(out_path))
    # 1 couverture + 2 pages pour la carte "Aptitudes" (règles de saison —
    # cf. `season_rules.py` — + traits de bataille + formation + domaines,
    # fusionnés et triés par phase en une seule carte dessinée, pas une page
    # copiée — cf. `_resolve_rules` ; « Inscription de Rune », Battle Trait
    # de début de round, reste dans son bandeau de phase normal malgré sa
    # longueur, répartie sur ses 2 colonnes plutôt que confinée à une seule —
    # cf. `warscroll_card._ability_group_body_columns_mixed` — vérifié
    # manuellement) + 1 page portant les 2 cartes de tactique citées
    # (dessinées elles aussi, cf. `tactic_cards.py` — elles tiennent toutes
    # les deux sur la même page) + N pages de cartes maison pour les profils
    # d'unité et les 3 manifestations invocables (2 par page) — vérifié
    # manuellement. La carte de règles occupe désormais toute la largeur
    # utile de la page (`_RULE_CARD_WIDTH`) et les cartes d'unité sont plus
    # larges (`_UNIT_CARD_WIDTH`) : moins de texte réenligné, donc des cartes
    # plus courtes et moins de pages qu'avant cet élargissement.
    assert len(reader.pages) == 9


def test_build_roster_pdf_resolves_generic_manifestation_lore_as_a_card(tmp_path):
    out_path = tmp_path / "out.pdf"
    result = build_roster_pdf(
        "data/Proposition de listes/LRL L3 Montagne monstre 2 .txt",
        out_path=out_path,
    )
    # "Twilit Sorceries" est un domaine de manifestations générique
    # (`EnS` dans Faction_abilities.csv) : sa carte de domaine (les 3
    # aptitudes "SUMMON ...") et la charte complète de chacune de ses 3
    # manifestations sont désormais toutes trois résolues via Wahapedia —
    # plus de repli sur le PDF français ("Manuel du général/sorts persistants
    # - manifestations.pdf") pour ce cas, rien signalé comme non trouvé.
    assert result.rules_unmatched == []
    assert result.wahapedia_used == []
    assert "Domaine de Manifestations — Twilit Sorceries" in result.rules_included
    assert out_path.exists()

    text = "".join(p.extract_text() for p in PdfReader(str(out_path)).pages)
    assert "Twilit Sorceries" in text
    assert "SUMMON" in text


def test_build_roster_pdf_falls_back_to_wahapedia_for_army_of_renown(tmp_path):
    out_path = tmp_path / "out.pdf"
    result = build_roster_pdf(
        "data/Proposition de listes/STD L3 First Prince 1980.txt",
        out_path=out_path,
    )
    # "Legion of the First Prince" est une armée de renom : ni ses unités ni
    # ses règles ne sont dans le battletome Slaves to Darkness de base, mais
    # data/wahapedia/ les a toutes (Warscrolls.csv sous le nom nu de l'unité,
    # Faction_abilities.csv sous le nom de l'armée de renom). Les profils
    # d'unité passent tous par Wahapedia désormais (carte maison, plus de
    # copie de page) : "Bloodletters" n'a donc plus rien de spécial à
    # signaler dans `wahapedia_used`, seules les règles d'armée de renom
    # (pas une unité) y restent.
    assert result.units_unmatched == []
    assert "Legion of the First Prince Bloodletters" in result.units_matched
    assert result.rules_unmatched == []
    assert "Legion of the First Prince — Army of Renown Rules (EN, Wahapedia)" in result.wahapedia_used
    # "Legion of the First Prince" remplace les traits de bataille / traits
    # héroïques / artefacts de Slaves to Darkness (mais pas ses formations,
    # qu'elle ne fournit pas elle-même) : la page du battletome de base ne
    # doit pas apparaître à côté de la version de remplacement (Wahapedia).
    assert "Traits de Bataille" not in result.rules_included
    assert "Traits Héroïques et Artefacts de Pouvoir" not in result.rules_included
    assert "Formations de Bataille" in result.rules_included
    assert out_path.exists()


def test_build_roster_pdf_falls_back_to_wahapedia_for_regiment_of_renown(tmp_path):
    out_path = tmp_path / "out.pdf"
    result = build_roster_pdf(
        "data/Proposition de listes/STD L3 Prince Warriors Launcher.txt",
        out_path=out_path,
    )
    # "The Exiled One" (Skarbrand) est un Regiment of Renown : absent du
    # battletome Slaves to Darkness (il appartient nativement à Blades of
    # Khorne), résolu via data/wahapedia/ (Warscrolls.csv role == "Regiment
    # of Renown" + le warscroll complet de Skarbrand, rendu en carte).
    assert "Skarbrand" not in result.units_unmatched
    assert "Skarbrand" in result.units_matched
    assert "Regiment of Renown : The Exiled One (EN, Wahapedia)" in result.wahapedia_used
    assert out_path.exists()

    # "The Exiled One" n'a qu'un seul membre (Skarbrand) : son aptitude
    # propre ("HATRED FOR ALL") doit rejoindre la carte de Skarbrand plutôt
    # que rester dans une section "Regiment of Renown" à part.
    text = "".join(p.extract_text() for p in PdfReader(str(out_path)).pages)
    # 1re occurrence = la couverture (liste des membres du Regiment of
    # Renown) ; la carte de Skarbrand elle-même est la 2e.
    cover_idx = text.find("Skarbrand")
    assert cover_idx != -1
    skarbrand_idx = text.find("Skarbrand", cover_idx + 1)
    assert skarbrand_idx != -1
    # une seule occurrence : plus de section "Regiment of Renown" séparée,
    # seulement la note de provenance rattachée à la carte de Skarbrand.
    assert text.count("Regiment of Renown — The Exiled One") == 1
    assert "Regiment of Renown — The Exiled One" in text[skarbrand_idx:skarbrand_idx + 400]
    assert "HATRED FOR ALL" in text[skarbrand_idx:]


def test_build_roster_pdf_reports_truly_unmatched_content_gracefully(tmp_path):
    """Rien de ce qui n'existe ni dans le battletome ni dans Wahapedia ne doit
    faire planter la génération — juste être signalé."""
    list_path = tmp_path / "fake.txt"
    list_path.write_text(
        "Fake - Test 2000/2000 pts\n\n"
        "Lumineth Realm-lords\n"
        "General's Handbook 2026-27\n"
        "Drops: 1\n"
        "Spell Lore - This Lore Does Not Exist Anywhere\n\n"
        "General's Regiment\n"
        "This Unit Does Not Exist Anywhere (250)\n"
        " • General\n\n"
        "Created with Warhammer Age of Sigmar: The App\n"
        "App: 1.37.0 | Data: 476\n",
        encoding="utf-8",
    )
    out_path = tmp_path / "out.pdf"
    result = build_roster_pdf(str(list_path), out_path=out_path)

    assert "This Unit Does Not Exist Anywhere" in result.units_unmatched
    assert "Domaine de sorts : This Lore Does Not Exist Anywhere" in result.rules_unmatched
    assert out_path.exists()
    assert len(PdfReader(str(out_path)).pages) >= 1


#: Répertoire Wahapedia inexistant — force `WahapediaLookup.available` à
#: `False` (`self._dir.exists()`) sans avoir à démonter les CSV réels, pour
#: forcer la résolution des règles sur le repli page French (`hybrid`) et
#: vérifier qu'`en`/`fr` le sautent bien (cf. `pdf_builder._resolve_rules`,
#: `allow_page_copy`).
_LRL_LIST = "data/Proposition de listes/LRL L3 Avengers Wardens.txt"


def test_build_roster_pdf_mode_hybrid_falls_back_to_french_page_copy_without_wahapedia(tmp_path):
    result = build_roster_pdf(
        _LRL_LIST, out_path=tmp_path / "out.pdf", wahapedia_dir=tmp_path / "no-such-wahapedia-dir", mode="hybrid",
    )
    assert result.rules_unmatched == []
    assert "Formations de Bataille" in result.rules_included
    assert "Traits Héroïques et Artefacts de Pouvoir" in result.rules_included


def test_build_roster_pdf_mode_en_skips_french_page_copy_fallback(tmp_path):
    result = build_roster_pdf(
        _LRL_LIST, out_path=tmp_path / "out.pdf", wahapedia_dir=tmp_path / "no-such-wahapedia-dir", mode="en",
    )
    assert "Formations de Bataille" not in result.rules_included
    assert "Traits Héroïques et Artefacts de Pouvoir" not in result.rules_included
    assert "Domaine de sorts : Lore of Hysh" in result.rules_unmatched
    assert "Domaine de manifestations : Manifestations of Hysh" in result.rules_unmatched


def test_build_roster_pdf_mode_fr_applies_verbatim_overrides_and_skips_page_copy(tmp_path):
    frf_path = tmp_path / "faction_rules_fr.json"
    frf_path.write_text(
        """{
            "factions": {
                "Lumineth Realm-lords": {
                    "rules": {
                        "battle_traits": [
                            {
                                "wahapedia_name": "DEPICT RUNE",
                                "name": "Vérité Française de Test",
                                "description": "<b>Texte vérifiant l'application du correctif.</b>",
                                "origin": "BT"
                            }
                        ]
                    },
                    "units": {}
                }
            }
        }""",
        encoding="utf-8",
    )
    out_path = tmp_path / "out.pdf"
    result = build_roster_pdf(_LRL_LIST, out_path=out_path, mode="fr", faction_rules_fr_path=frf_path)

    assert result.rules_unmatched == []
    # aucune copie de page French même pour une catégorie non curée (Traits
    # Héroïques/Artefacts de Pouvoir n'a pas d'entrée dans le JSON de test) :
    # `fr` dégrade vers Wahapedia (EN), jamais une page.
    text = "".join(p.extract_text() for p in PdfReader(str(out_path)).pages)
    assert "Vérité Française de Test" in text
    assert "Texte vérifiant l'application du correctif" in text


def test_build_roster_pdf_mode_fr_extended_includes_generic_abilities_card(tmp_path):
    generic_path = tmp_path / "generic_core_abilities.json"
    generic_path.write_text(
        """[
            {"name": "Aptitude Générique de Test", "description": "Texte de test.", "condition": "Passive", "ability_phase": ""}
        ]""",
        encoding="utf-8",
    )
    out_path = tmp_path / "out.pdf"
    result = build_roster_pdf(_LRL_LIST, out_path=out_path, mode="fr-extended", generic_core_abilities_path=generic_path)

    assert "Aptitudes Génériques — MdG26-27" in result.rules_included
    text = "".join(p.extract_text() for p in PdfReader(str(out_path)).pages)
    assert "Aptitude Générique de Test" in text


def test_build_roster_pdf_mode_fr_extended_without_curated_generic_abilities_behaves_like_fr(tmp_path):
    """Fichier de règles génériques absent/vide (peu importe la curation
    réelle de `data/generic_core_abilities.json`) : le mode étendu ne doit ni
    planter ni ajouter de carte."""
    generic_path = tmp_path / "generic_core_abilities.json"
    generic_path.write_text("[]", encoding="utf-8")
    result = build_roster_pdf(
        _LRL_LIST, out_path=tmp_path / "out.pdf", mode="fr-extended", generic_core_abilities_path=generic_path
    )
    assert "Aptitudes Génériques — MdG26-27" not in result.rules_included


_STD_FIRST_PRINCE_LIST = "data/Proposition de listes/STD L3 First Prince 1980.txt"

#: Les 9 aptitudes Wahapedia de l'Armée de Renom "Legion of the First
#: Prince" (`WahapediaLookup.find_renown_army_rules`) — la curation doit
#: couvrir les 9 pour que `_renown_army_pool` considère l'armée entièrement
#: traduite (cf. `test_build_roster_pdf_mode_fr_renown_army_full_coverage`).
_LEGION_OF_THE_FIRST_PRINCE_ABILITIES = [
    ("battle_traits", "FIRST-DAMNED PRINCE"),
    ("battle_traits", "DAEMONIC REINFORCEMENTS"),
    ("battle_traits", "STORM OF BLACKENED BLADES"),
    ("battle_traits", "BESTOW FAVOUR"),
    ("heroic_traits_artefacts", "DREAD MARSHAL"),
    ("heroic_traits_artefacts", "BLACK RITUAL DAGGER"),
    ("spell_lores", "DARK CANTRIP"),
    ("spell_lores", "SHROUD IN DARKNESS"),
    ("manifestation_lores", "SUMMON EIGHTFOLD DOOM-SIGIL"),
]


def _renown_army_frf_json(abilities: list[tuple[str, str]]) -> str:
    """Construit un `data/faction_rules_fr.json` de test avec, pour chaque
    `(catégorie, wahapedia_name)` de `abilities`, un correctif minimal sous
    `renown_armies."Legion of the First Prince"` — assez pour vérifier la
    plomberie (`_renown_army_pool`/`_resolve_rules`), pas un vérbatim réel."""
    import json as _json

    by_category: dict[str, list[dict]] = {}
    for category, wahapedia_name in abilities:
        by_category.setdefault(category, []).append({
            "wahapedia_name": wahapedia_name,
            "name": f"FR : {wahapedia_name}",
            "description": f"<b>Texte français de test pour {wahapedia_name}.</b>",
            "origin": "BT",
        })
    return _json.dumps({
        "factions": {
            "Slaves to Darkness": {
                "renown_armies": {"Legion of the First Prince": by_category},
            },
        },
    })


def test_build_roster_pdf_mode_fr_renown_army_full_coverage(tmp_path):
    """Les 9 aptitudes de l'Armée de Renom sont curées : elle doit rejoindre
    la carte de règles fusionnée en français et disparaître de l'annexe
    anglaise (contrairement au mode `hybrid`, cf.
    `test_build_roster_pdf_falls_back_to_wahapedia_for_army_of_renown`)."""
    frf_path = tmp_path / "faction_rules_fr.json"
    frf_path.write_text(_renown_army_frf_json(_LEGION_OF_THE_FIRST_PRINCE_ABILITIES), encoding="utf-8")
    out_path = tmp_path / "out.pdf"
    result = build_roster_pdf(_STD_FIRST_PRINCE_LIST, out_path=out_path, mode="fr", faction_rules_fr_path=frf_path)

    assert "Legion of the First Prince — Army of Renown Rules (EN, Wahapedia)" not in result.wahapedia_used
    assert "Armée de Renom — Legion of the First Prince" in result.rules_included
    text = "".join(p.extract_text() for p in PdfReader(str(out_path)).pages)
    assert "FR : FIRST-DAMNED PRINCE" in text
    assert "Texte français de test pour SUMMON EIGHTFOLD DOOM-SIGIL" in text


def test_build_roster_pdf_mode_fr_renown_army_partial_coverage_keeps_wahapedia_fallback(tmp_path):
    """Curation incomplète (1 aptitude sur 9) : l'Armée de Renom entière doit
    rester dans l'annexe anglaise plutôt que de mélanger français patché et
    anglais non patché sur la carte fusionnée sans le signaler."""
    frf_path = tmp_path / "faction_rules_fr.json"
    frf_path.write_text(_renown_army_frf_json(_LEGION_OF_THE_FIRST_PRINCE_ABILITIES[:1]), encoding="utf-8")
    out_path = tmp_path / "out.pdf"
    result = build_roster_pdf(_STD_FIRST_PRINCE_LIST, out_path=out_path, mode="fr", faction_rules_fr_path=frf_path)

    assert "Legion of the First Prince — Army of Renown Rules (EN, Wahapedia)" in result.wahapedia_used
    assert "Armée de Renom — Legion of the First Prince" not in result.rules_included


def test_build_roster_pdf_mode_hybrid_ignores_renown_army_curation(tmp_path):
    """Le vérbatim français ne doit jamais s'appliquer en `hybrid`/`en` —
    même garantie que `_fr_patch` pour les autres catégories."""
    frf_path = tmp_path / "faction_rules_fr.json"
    frf_path.write_text(_renown_army_frf_json(_LEGION_OF_THE_FIRST_PRINCE_ABILITIES), encoding="utf-8")
    result = build_roster_pdf(
        _STD_FIRST_PRINCE_LIST, out_path=tmp_path / "out.pdf", mode="hybrid", faction_rules_fr_path=frf_path,
    )
    assert "Legion of the First Prince — Army of Renown Rules (EN, Wahapedia)" in result.wahapedia_used
    assert "Armée de Renom — Legion of the First Prince" not in result.rules_included
