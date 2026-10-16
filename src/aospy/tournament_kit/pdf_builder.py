"""Assemble le PDF « kit de tournoi » : page de couverture (liste mise en
forme), puis les règles de faction pertinentes en carte maison (traits de
bataille, formation, traits héroïques/artefacts, domaines de sorts/
manifestations choisis — Wahapedia-first, repli page French par catégorie,
cf. `warscroll_card.py`) et les cartes de tactique de bataille citées, elles
aussi en carte maison verbatim français (`tactic_cards.py`, transcription
manuelle de `MdG26-27 Tactiques.pdf` — plus de copie de page pour aucune de
ces sections), puis les profils d'unité, en carte maison anglaise dessinée
par `warscroll_card.py` à partir de `data/wahapedia/*.csv` (jamais une page
de battletome copiée, cf. le module de ce fichier pour le détail). Un
domaine de manifestations générique (partagé entre
factions, absent du battletome) est résolu en français via
`data/Manuel du général/sorts persistants - manifestations.pdf`
(`warscroll_index.generic_manifestation_lores`) — règles de convocation
*et* charte de chaque manifestation invocable, pas seulement l'annonce du
sort. Enfin, si besoin, une annexe en anglais (repli Wahapedia,
`wahapedia_lookup.py`) pour tout ce qui n'existe dans *aucun* des PDF
fournis : règles d'armée de renom, Régiments de Renom, et tout domaine de
sorts/manifestations qui échapperait aussi au French. Aucun accès DB
requis.

Une Armée de Renom (ex. « Slaves to Darkness | Legion of the First Prince »)
*remplace* tout ou partie des traits de bataille / traits héroïques et
artefacts / domaine de sorts de la faction de base par ses propres règles
(cf. `_AOR_REPLACES`) — la page du battletome de base correspondante est
omise plutôt que dupliquée à côté de la version de remplacement (rendue à
part, en anglais via Wahapedia). Aucune armée de renom n'a en revanche ses
propres formations de bataille (constaté sur toutes les entrées du CSV) :
cette section-là reste toujours celle de la faction de base. Un Regiment of
Renown donne accès à des warscrolls normalement hors faction (résolus via
`WahapediaLookup.find_warscroll`, qui cherche dans toutes les factions) *et*
peut porter sa propre aptitude générique (`RegimentOfRenownData.abilities`) —
rendue dans l'annexe comme n'importe quel autre bloc d'aptitudes s'il compte
plusieurs unités membres, mais directement rattachée à la carte de l'unité
(`_render_warscroll(..., extra_abilities=...)`) quand le régiment n'en a
qu'une seule, pour ne pas dupliquer inutilement la structure.

Le paragraphe ci-dessus décrit le mode `hybrid` (défaut). `build_roster_pdf(...,
mode=...)` porte 3 autres variantes (`RosterMode`) : `en` (Wahapedia
uniquement, la copie de page French est sautée) et `fr`/`fr-extended`
(correctifs/additions vérbatim français de `data/faction_rules_fr.json`
appliqués sur le pool Wahapedia partout où ils existent, copie de page
également sautée — `fr-extended` ajoute les Aptitudes Génériques,
`data/generic_core_abilities.json`). Cf. le commentaire au-dessus de
`RosterMode` et le skill `faction-rules-fr` pour le détail.

Les Règles de Saison 2026-27 (`season_rules.py`, incluses dans tout PDF), les
Aptitudes Génériques (`fr-extended` seulement) et les règles de faction/
Armée de Renom résolues ci-dessus (`rule_ability_pool`) rejoignent toutes le
même bassin d'aptitudes puis une seule carte triée par bandeau de phase
(`build_roster_pdf`, badges d'origine « Saison »/« MdG »/faction pour rester
identifiables) — jamais 3 cartes séparées : un joueur qui consulte la carte
raisonne par phase du tour ("je suis en phase des héros, qu'ai-je le droit
de faire ?"), pas par type de règle."""

from __future__ import annotations

import re
from dataclasses import dataclass, field, replace as _dc_replace
from io import BytesIO
from pathlib import Path
from typing import Literal

from PIL import Image
from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from ..pdf_theme import GOLD, GOLD_DIM, NIGHT_BLUE, PARCHMENT, STEEL, today_str
from .list_parser import ParsedList, parse_list_file
from .translation.faction_rules_fr import (
    apply_fr_overrides, get_faction_category_overrides, get_regiment_of_renown_overrides,
    get_unit_ability_overrides, load_faction_rules_fr,
)
from .translation.generic_core_abilities import load_generic_core_abilities
from .translation.rules_resolution import (
    _BANNER_PLEDGED_GOD, _PLEDGE_OPTION_RE, RosterMode, _find_pledge_battle_trait, _resolve_rules,
)
from .translation.season_rules import load_season_rules
from .translation.tactic_cards import load_tactic_cards
from .translation.wahapedia_lookup import (
    AbilityEntry, RegimentOfRenownData, WahapediaLookup, WarscrollData, load_wahapedia,
)
from .translation.warscroll_index import battletome_path, generic_manifestation_lores_path, load_index
from .warscroll_card import (
    CARD_TITLE_FONT, PAGE_BG, build_warscroll_cards_flow, render_rule_card, render_tactic_card,
    set_faction_specific_keywords, tag_ability_origin,
)


#: Racine des PDF de roster générés sans `--out` explicite — un sous-dossier
#: par mode (`_DEFAULT_OUTPUT_SUBDIR`), pour ne plus mélanger les variantes
#: d'une même liste (ex. `LRL Teclis Vanari 2000.pdf` généré en `hybrid` puis
#: en `fr-extended`, qui s'écrasaient silencieusement l'un l'autre dans un
#: dossier plat) — demande explicite de l'utilisateur. Distincte de
#: `scratch/output/best_unit/` (rapports pantheon/duels/coût de `reports/`),
#: l'autre moitié du même rangement.
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parents[3] / "scratch" / "output" / "roster"

#: `hybrid` est le mode historique/par défaut de la CLI (`--mode`, cf.
#: `RosterMode` ci-dessus) mais le dossier se nomme « defaut » plutôt que
#: « hybrid » : le nom du mode est un détail d'implémentation (repli page
#: battletome + Wahapedia), « defaut » est ce que l'utilisateur reconnaît
#: comme « je n'ai pas précisé de mode ».
_DEFAULT_OUTPUT_SUBDIR: dict[RosterMode, str] = {
    "hybrid": "defaut",
    "en": "en",
    "fr": "fr",
    "fr-extended": "fr-extended",
}

#: Marge des pages « cartes » (règles/tactiques/warscrolls) — volontairement
#: plus fine que les 18mm de la couverture/annexe (texte suivi, a besoin de
#: respirer) : plus de surface utile pour les cartes elles-mêmes, l'objectif
#: qui a fait réduire cette marge de moitié (elle était à 11mm).
_CARD_PAGE_MARGIN = 5.5 * mm

#: Largeur utile d'une page A4 portrait avec `_CARD_PAGE_MARGIN` de chaque
#: côté — la marge n'a été réduite que pour dégager cette largeur-là aux
#: cartes elles-mêmes, donc toute carte qui reste seule sur sa ligne
#: (règles, tactique) doit s'y caler entièrement plutôt que de laisser un
#: vide à droite.
_CARD_PAGE_WIDTH = A4[0] - 2 * _CARD_PAGE_MARGIN

#: Largeur de la carte de règles fusionnée — occupe toute la largeur utile
#: (elle reste seule sur sa ligne, cf. `_build_rule_cards_pdf`) : sur 2
#: colonnes par bandeau de phase (`warscroll_card.render_rule_card`), une
#: carte à 130mm serrait ces colonnes bien plus qu'il n'était nécessaire —
#: la conserver à 130mm en avait fait un choix arbitraire) plutôt qu'un vrai
#: usage de la place disponible.
_RULE_CARD_WIDTH = _CARD_PAGE_WIDTH

#: Largeur des cartes de tactique de bataille — jamais mises en paire
#: (contrairement aux cartes de warscroll), juste empilées, assez compactes
#: pour que les 2 tactiques citées par une liste tiennent normalement sur
#: une seule page.
_TACTIC_CARD_WIDTH = _CARD_PAGE_WIDTH

#: Largeur d'une carte de profil d'unité — 2 par ligne (`pack_cards_two_up`),
#: donc calée sur la moitié de la largeur utile moins l'écart entre les 2
#: (même `gap` que `warscroll_card.build_warscroll_cards_flow`) plutôt qu'une
#: valeur fixe (88mm) choisie sans lien avec cette largeur — céder toute la
#: place disponible aux cartes plutôt que de laisser un vide à droite.
_UNIT_CARD_GAP = 5 * mm
_UNIT_CARD_WIDTH = (_CARD_PAGE_WIDTH - _UNIT_CARD_GAP) / 2

#: police du titre de la liste — Cinzel Bold, la même police "tome" que les
#: titres de carte (`warscroll_card.CARD_TITLE_FONT`) plutôt que
#: `OLD_ENGLISH_FONT` (Times-Bold) utilisé avant : demande explicite de
#: l'utilisateur, pour une cohérence visuelle titre de liste / titre de carte.
_TITLE = ParagraphStyle("kit_title", fontName=CARD_TITLE_FONT, fontSize=20, leading=24, textColor=NIGHT_BLUE, alignment=TA_LEFT, spaceAfter=2)
_META = ParagraphStyle("kit_meta", fontName="Times-Italic", fontSize=9.5, leading=13, textColor=STEEL, alignment=TA_LEFT, spaceAfter=10)
_REGIMENT = ParagraphStyle("kit_regiment", fontName="Times-Bold", fontSize=12, leading=15, textColor=GOLD_DIM, alignment=TA_LEFT, spaceBefore=10, spaceAfter=3)
_WARNING = ParagraphStyle("kit_warning", fontName="Times-Bold", fontSize=9.5, leading=13, textColor=STEEL, alignment=TA_LEFT, spaceBefore=14)
_EN_BANNER = ParagraphStyle("kit_en_banner", fontName="Times-Bold", fontSize=15, leading=19, textColor=colors.HexColor("#8c1f1f"), alignment=TA_LEFT, spaceAfter=2)
_EN_SUBBANNER = ParagraphStyle("kit_en_subbanner", fontName="Times-Italic", fontSize=9.5, leading=13, textColor=STEEL, alignment=TA_LEFT, spaceAfter=12)
_EN_SECTION = ParagraphStyle("kit_en_section", fontName="Times-Bold", fontSize=13, leading=17, textColor=NIGHT_BLUE, alignment=TA_LEFT, spaceBefore=12, spaceAfter=4)
_EN_SUBSECTION = ParagraphStyle("kit_en_subsection", fontName="Times-Bold", fontSize=10.5, leading=14, textColor=GOLD_DIM, alignment=TA_LEFT, spaceBefore=8, spaceAfter=3)
_EN_BODY = ParagraphStyle("kit_en_body", fontName="Times-Roman", fontSize=9, leading=12.5, textColor=NIGHT_BLUE, alignment=TA_LEFT, spaceAfter=6)
_EN_LEGEND = ParagraphStyle("kit_en_legend", fontName="Times-Italic", fontSize=8.5, leading=12, textColor=STEEL, alignment=TA_LEFT, spaceAfter=4)



#: Ordre d'apparition des cartes de profil dans le PDF (après les Héros,
#: toute base confondue, toujours en tête) — demande explicite de
#: l'utilisateur. Wahapedia combine base + rôle dans un seul champ `role`
#: (ex. `"Cavalry Hero"`, `"War Machine"`), d'où le test par sous-chaîne
#: plutôt qu'une correspondance exacte dans `_role_rank`.
_ROLE_ORDER = ("infantry", "cavalry", "beast", "monster", "war machine")


def _role_rank(role: str) -> int:
    """Rang de tri d'une carte de profil : Héros (0, toute base confondue)
    d'abord, puis `_ROLE_ORDER` dans l'ordre. Un rôle qui ne matche ni "hero"
    ni aucune entrée de `_ROLE_ORDER` (Faction Terrain, manifestation
    invocable...) reste en dernier plutôt que de forcer un classement
    arbitraire — `list.sort` étant stable, l'ordre relatif au sein d'un même
    rang reste celui de la liste (régiment du général, puis régiment 1, 2...)."""
    role_l = (role or "").lower()
    if "hero" in role_l:
        return 0
    for i, key in enumerate(_ROLE_ORDER, start=1):
        if key in role_l:
            return i
    return len(_ROLE_ORDER) + 1


@dataclass(frozen=True)
class RosterPdfResult:
    output_path: Path
    units_matched: list[str]
    units_unmatched: list[str]
    rules_included: list[str] = field(default_factory=list)
    rules_unmatched: list[str] = field(default_factory=list)
    wahapedia_used: list[str] = field(default_factory=list)


def _unit_row(name: str, points: int, options: list[str]) -> str:
    text = f"<b>{name}</b> — {points} pts"
    if options:
        text += "<br/><font size=8 color='#4a4536'>" + ", ".join(options) + "</font>"
    return text


def _clean_html(text: str) -> str:
    """Convertit le balisage HTML-ish de Wahapedia en balisage compris par
    `reportlab.platypus.Paragraph` (sous-ensemble XML). `<a>` est déballé
    (garde le texte, retire le lien), `<span class="kwb...">` devient `<b>`
    (c'est déjà la mise en forme visuelle voulue — mots-clés en gras),
    `<ul>/<li>` devient une liste à puces séparée par des retours à la ligne."""
    if not text:
        return ""
    # 2+ id de tooltip scrapés collés bout à bout, sans aucun texte entre eux
    # (ex. LRL, Traits de Bataille, "DEPICT RUNE" :
    # "...<br><br>$000002337$000002338$000002339$000002340$000002341<br>...") :
    # contrairement au cas juste en dessous (un seul id, wrapper autour d'un
    # texte réel déjà présent, ex. "%000010870<ky>FIGHT</ky>%" ou
    # "$000001419|As it twitches..." — l'id sert alors de simple séparateur/
    # marqueur), une *suite* d'ids sans rien entre eux référence du contenu
    # (ici, l'effet de chacune des 5 runes) que Wahapedia résout côté client
    # depuis une table de tooltips absente des 13 CSV téléchargés (aucun
    # fichier tooltip dans `scripts/refresh_wahapedia_data.py`) — un vrai
    # trou de données, pas du bruit. Le signaler plutôt que le faire
    # disparaître silencieusement (ce que faisait le strip générique
    # ci-dessous jusqu'à ce que ça masque l'essentiel du texte de cette
    # aptitude, signalé par l'utilisateur).
    text = re.sub(
        r"(?:[%$]\d+){2,}",
        " <i>[texte manquant dans l’export Wahapedia — voir le Manuel du général/l’App]</i> ",
        text,
    )
    # id de tooltip isolé : simple marqueur autour/avant du texte réel déjà
    # présent (ex. "%000010870<ky>FIGHT</ky>%", "$000001419|As it twitches...")
    # — jamais du texte de règle en lui-même, mais peut laisser une "|"
    # orpheline (séparateur du style "$id|texte") qu'il faut retirer avec lui.
    text = re.sub(r"[%$]\d+\|?", "", text).replace("%", "").replace("$", "")
    # au moins un champ connu est tronqué en plein milieu d'une balise
    # ouvrante (ex. Faction_abilities.csv, "SCHOLAR OF THE SIGILS" : `...<a
    # href="/aos4/fact` sans `>` de fermeture, coupé à la fin du champ ; FEC,
    # "A Splendid Pageant" : `...<span class="tooltip00335"
    # data-tooltip-content="#tooltip_conte` de même) — une balise ouvrante
    # sans son `>` de fermeture jusqu'à la fin de la chaîne ne peut être
    # qu'un artefact de troncature, jamais du texte de règle légitime, quel
    # que soit son nom (`<a`, `<span`...).
    text = re.sub(r"<[a-zA-Z][^>]*$", "", text)
    text = re.sub(r"<a[^>]*>", "", text)
    text = text.replace("</a>", "")
    text = re.sub(r"<span[^>]*>", "<b>", text)
    text = text.replace("</span>", "</b>")
    text = text.replace("<ul>", "").replace("</ul>", "")
    text = re.sub(r"<li>", "• ", text)
    text = text.replace("</li>", "<br/>")
    text = re.sub(r"<br\s*>", "<br/>", text)
    text = re.sub(r"&(?!amp;|lt;|gt;|quot;|#\d+;)", "&amp;", text)
    return text.strip()


def _strip_all_tags(text: str) -> str:
    """Retire tout balisage — y compris une balise tronquée en plein milieu
    (donnée source corrompue, sans `>` de fermeture jusqu'à la fin du champ),
    en supprimant aussi tout `<`/`>` résiduel isolé pour rester un texte brut
    valide (sans quoi reportlab tenterait encore de le parser comme du XML)."""
    text = re.sub(r"<[^>]*>", " ", text)
    text = text.replace("<", " ").replace(">", " ")
    return re.sub(r"\s+", " ", text).strip()


def _safe_paragraph(text: str, style: ParagraphStyle) -> Paragraph:
    """Comme `Paragraph(text, style)`, mais tolérant : `data/wahapedia/*.csv`
    est une donnée externe scrapée, parfois corrompue (ex. une balise HTML
    tronquée en plein milieu d'un champ) — plutôt que de faire planter toute
    la génération du PDF pour une seule entrée abîmée, on retombe sur le
    texte brut (tags retirés) pour cette entrée-là."""
    try:
        return Paragraph(text, style)
    except Exception:
        return Paragraph(_strip_all_tags(text), style)




#: texture pierre du fond de page — générée par
#: `scripts/generate_stone_texture.py` (procédurale plutôt que téléchargée :
#: même raisonnement que `Cinzel-Bold.ttf`/`warscroll_card.py`, pas de
#: licence à auditer). `ImageReader` construit une seule fois au niveau
#: module ; repli silencieux sur un aplat `PAGE_BG` (même teinte) si le
#: fichier venait à manquer (ex. install sans les données du paquet) — même
#: schéma que le repli police de `warscroll_card.py`.
_STONE_TEXTURE_PATH = Path(__file__).resolve().parent / "assets" / "stone_texture.jpg"
try:
    _STONE_TEXTURE = ImageReader(str(_STONE_TEXTURE_PATH))
except Exception:
    _STONE_TEXTURE = None


def _draw_page_bg(c, doc) -> None:
    """Peint le fond de chaque page du kit (couverture, cartes, annexe) :
    texture pierre pâle sur toute la page (`_STONE_TEXTURE`). Rien d'autre
    ici — le fond blanc qui porte le texte est désormais une case ajustée au
    contenu (`_wrap_in_sheet` pour la couverture/l'annexe, la carte
    elle-même pour les pages de cartes), jamais un grand rectangle peint sur
    toute la hauteur de la page indépendamment de ce que le contenu occupe
    réellement : cette dernière approche laissait un vide énorme sous un
    contenu court (ex. une petite liste sur la couverture) — signalé par
    l'utilisateur."""
    c.saveState()
    page_w, page_h = doc.pagesize
    if _STONE_TEXTURE is not None:
        c.drawImage(_STONE_TEXTURE, 0, 0, width=page_w, height=page_h, preserveAspectRatio=False)
    else:
        c.setFillColor(PAGE_BG)
        c.rect(0, 0, page_w, page_h, fill=1, stroke=0)
    c.restoreState()


#: marge intérieure (haut/bas/gauche/droite) de la case blanche que
#: `_wrap_in_sheet` bâtit autour du texte de couverture/d'annexe.
_SHEET_PADDING = 14


def _wrap_in_sheet(story: list, width: float) -> Table:
    """Enveloppe un `story` (liste de flowables déjà construits) dans une
    seule case à fond blanc/bordure dorée, ajustée exactement à la hauteur
    du contenu plutôt qu'un rectangle peint sur toute la page (cf.
    `_draw_page_bg`) : chaque élément de `story` devient sa propre ligne
    d'un `Table` à une colonne — un `Table` se scinde nativement entre pages
    quand son contenu dépasse une page (contrairement à un flowable unique
    imbriqué dans une seule cellule), donc reste valable même pour une
    longue annexe, pas seulement une couverture tenant sur une page."""
    rows = [[item] for item in story]
    n = len(rows)
    box = Table(rows, colWidths=[width])
    box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("BOX", (0, 0), (-1, -1), 0.8, GOLD_DIM),
        ("LEFTPADDING", (0, 0), (-1, -1), _SHEET_PADDING),
        ("RIGHTPADDING", (0, 0), (-1, -1), _SHEET_PADDING),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (0, 0), _SHEET_PADDING),
        ("BOTTOMPADDING", (0, n - 1), (0, n - 1), _SHEET_PADDING),
    ]))
    return box


def _build_cover_pdf(
    parsed: ParsedList, units_unmatched: list[str], rules_unmatched: list[str], wahapedia_used: list[str],
) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm, topMargin=18 * mm, bottomMargin=15 * mm,
        title=parsed.title,
    )
    #: largeur dispo pour le contenu une fois la case blanche (`_wrap_in_sheet`)
    #: posée autour, sa propre marge intérieure (`_SHEET_PADDING`) déduite des
    #: deux côtés — les tables imbriquées (lignes d'unité) doivent s'y caler,
    #: pas à `doc.width` (largeur du cadre de page, plus large que la case).
    content_width = doc.width - 2 * _SHEET_PADDING
    story = [Paragraph(parsed.title, _TITLE)]

    meta_lines = [parsed.faction]
    if parsed.allegiance:
        meta_lines.append(parsed.allegiance)
    if parsed.drops is not None:
        meta_lines.append(f"Drops : {parsed.drops}")
    if parsed.spell_lore:
        meta_lines.append(f"Domaine de sorts : {parsed.spell_lore}")
    if parsed.prayer_lore:
        meta_lines.append(f"Domaine de prières : {parsed.prayer_lore}")
    if parsed.manifestation_lore:
        meta_lines.append(f"Domaine de manifestations : {parsed.manifestation_lore}")
    story.append(Paragraph(" · ".join(meta_lines), _META))

    if parsed.battle_tactic_cards:
        story.append(Paragraph("<b>Battle Tactic Cards :</b> " + ", ".join(parsed.battle_tactic_cards), _META))

    style = ParagraphStyle("kit_cell", fontName="Times-Roman", fontSize=9.5, leading=13, textColor=NIGHT_BLUE)
    for regiment in parsed.regiments:
        story.append(Paragraph(regiment.title, _REGIMENT))
        rows = [[Paragraph(_unit_row(u.name, u.points, u.options), style)] for u in regiment.units]
        if rows:
            table = Table(rows, colWidths=[content_width])
            table.setStyle(TableStyle([
                ("BOX", (0, 0), (-1, -1), 0.6, GOLD),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, GOLD),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(table)

    if parsed.regiments_of_renown:
        story.append(Paragraph("Regiments of Renown", _REGIMENT))
        rows = [
            [Paragraph(_unit_row(ror.name, ror.points, ror.units), style)]
            for ror in parsed.regiments_of_renown
        ]
        table = Table(rows, colWidths=[content_width])
        table.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.6, GOLD),
            ("INNERGRID", (0, 0), (-1, -1), 0.4, GOLD),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(table)

    if parsed.faction_terrain:
        story.append(Paragraph("Faction Terrain", _REGIMENT))
        story.append(Paragraph(", ".join(parsed.faction_terrain), style))

    if units_unmatched:
        story.append(Paragraph(
            "⚠ Profil non trouvé (ni battletome, ni Wahapedia) pour : " + ", ".join(units_unmatched),
            _WARNING,
        ))
    if rules_unmatched:
        story.append(Paragraph(
            "⚠ Règle non trouvée (ni battletome, ni Wahapedia) pour : " + ", ".join(rules_unmatched),
            _WARNING,
        ))
    if wahapedia_used:
        story.append(Paragraph(
            "ℹ Complété en anglais via Wahapedia (voir annexe en fin de document) : " + ", ".join(wahapedia_used),
            ParagraphStyle("kit_info", fontName="Times-Italic", fontSize=8.5, leading=12, textColor=STEEL, spaceBefore=8),
        ))

    story.append(Spacer(1, 14))
    story.append(Paragraph(f"Généré le {today_str()} — aospy roster pdf", ParagraphStyle("kit_footer", fontName="Times-Italic", fontSize=8, textColor=STEEL)))

    doc.build([_wrap_in_sheet(story, doc.width)], onFirstPage=_draw_page_bg, onLaterPages=_draw_page_bg)
    return buf.getvalue()


#: Les pages copiées depuis les battletomes/Manuel du général sont des scans
#: aplatis (une seule image ~1865x2472 par page, cf. le traitement anti-copie
#: documenté dans CLAUDE.md) : `writer.add_page` les recopie telles quelles,
#: soit ~1 Mo/page rien qu'en JPEG déjà compressé — largement plus que
#: nécessaire pour une page de règles lue à l'écran ou imprimée en A4. On les
#: redimensionne/recompresse après coup (~150-250 Ko/page), ce qui a divisé
#: par 30-40 la taille des PDF de tournoi générés (plusieurs Mo -> quelques
#: centaines de Ko) sans perte de lisibilité perceptible.
_COPIED_PAGE_MAX_DIM = 1600
_COPIED_PAGE_JPEG_QUALITY = 65


def _compress_page_images(page) -> None:
    for img_file in page.images:
        pil_image = img_file.image
        scale = min(1.0, _COPIED_PAGE_MAX_DIM / max(pil_image.size))
        if scale >= 1.0:
            continue
        new_size = (round(pil_image.width * scale), round(pil_image.height * scale))
        resized = pil_image.convert("RGB").resize(new_size, Image.LANCZOS)
        img_file.replace(resized, quality=_COPIED_PAGE_JPEG_QUALITY)


def _append_pages(writer: PdfWriter, reader: PdfReader, seen_pages: set[int], sections: list[tuple[str, list[int]]]) -> None:
    for _label, pages in sections:
        for page_num in pages:
            if page_num in seen_pages:
                continue
            seen_pages.add(page_num)
            writer.add_page(reader.pages[page_num])
            _compress_page_images(writer.pages[-1])


def _render_ability_entries(story: list, entries: list[AbilityEntry]) -> None:
    for entry in entries:
        story.append(_safe_paragraph(entry.name, _EN_SUBSECTION))
        if entry.legend:
            story.append(_safe_paragraph(_clean_html(entry.legend), _EN_LEGEND))
        story.append(_safe_paragraph(_clean_html(entry.description), _EN_BODY))


def _build_wahapedia_appendix_pdf(
    wahapedia_lore_blocks: list[tuple[str, list[AbilityEntry]]],
    renown_army: tuple[str, dict[str, list[AbilityEntry]]] | None,
    regiments_of_renown: list[tuple[str, RegimentOfRenownData | None]],
) -> bytes | None:
    """Repli anglais pour ce qui n'a pas de carte/page dédiée : domaines de
    sorts/manifestations génériques, règles d'armée de renom, Regiments of
    Renown à plusieurs membres (un seul membre : son aptitude rejoint plutôt
    la carte de cette unité, cf. `build_roster_pdf`). Les profils d'unité
    eux-mêmes ne passent plus par ici — ils sont rendus en carte maison
    (`warscroll_card.py`), plus de page de battletome copiée ni de bloc de
    texte anglais pour un profil d'unité."""
    if not (wahapedia_lore_blocks or renown_army or regiments_of_renown):
        return None

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm, topMargin=18 * mm, bottomMargin=15 * mm,
        title="Annexe Wahapedia (EN)",
    )
    story: list = [
        Paragraph("ANNEXE — CONTENU WAHAPEDIA (ANGLAIS)", _EN_BANNER),
        Paragraph(
            "Ce qui suit n'existe dans aucun des PDF fournis (battletomes, Manuel du général) : "
            "domaines de sorts/manifestations génériques, règles d'armée de renom, Régiments de Renom. "
            "Repris tel quel depuis data/wahapedia/ (Wahapedia, en anglais) — non traduit pour éviter tout contresens sur des règles de jeu.",
            _EN_SUBBANNER,
        ),
    ]

    for label, entries in wahapedia_lore_blocks:
        story.append(Paragraph(label, _EN_SECTION))
        _render_ability_entries(story, entries)

    if renown_army is not None:
        renown_name, grouped = renown_army
        story.append(Paragraph(f"{renown_name} — Army of Renown Rules", _EN_SECTION))
        for category, entries in grouped.items():
            story.append(Paragraph(category, _EN_SUBSECTION))
            _render_ability_entries(story, entries)

    for ror_name, ror_data in regiments_of_renown:
        story.append(Paragraph(f"Regiment of Renown — {ror_name}", _EN_SECTION))
        if ror_data is None:
            story.append(Paragraph("⚠ Non trouvé dans Wahapedia non plus.", _WARNING))
            continue
        if ror_data.legend:
            story.append(_safe_paragraph(_clean_html(ror_data.legend), _EN_LEGEND))
        if ror_data.composition:
            story.append(_safe_paragraph("Composition : " + ", ".join(_clean_html(c) for c in ror_data.composition), _EN_BODY))
        _render_ability_entries(story, ror_data.abilities)

    doc.build([_wrap_in_sheet(story, doc.width)], onFirstPage=_draw_page_bg, onLaterPages=_draw_page_bg)
    return buf.getvalue()


def _build_rule_cards_pdf(cards: list) -> bytes | None:
    """Empile les cartes de règle (Traits de Bataille/Formation/Traits
    Héroïques/Artefacts) en pile simple, sans les grouper 2 par ligne comme
    les cartes de warscroll : leur longueur varie trop (1 aptitude pour une
    formation, 9 pour des traits héroïques) pour qu'un `KeepTogether` sur une
    paire reste pertinent — une carte trop longue pour une page tiendrait la
    carte voisine, plus courte, en otage sur la page précédente."""
    if not cards:
        return None
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=_CARD_PAGE_MARGIN, rightMargin=_CARD_PAGE_MARGIN, topMargin=_CARD_PAGE_MARGIN, bottomMargin=_CARD_PAGE_MARGIN,
        title="Règles de faction (cartes)",
    )
    story: list = []
    for card in cards:
        if story:
            # avant chaque carte sauf la première : un `Spacer` de fin qui ne
            # rentre plus dans l'espace restant part seul sur une page neuve
            # — page blanche en fin de PDF (cf. `pack_cards_two_up`).
            story.append(Spacer(1, 5 * mm))
        story.append(card)
    doc.build(story, onFirstPage=_draw_page_bg, onLaterPages=_draw_page_bg)
    return buf.getvalue()


def _build_tactic_cards_pdf(cards: list) -> bytes | None:
    """Empile les cartes de tactique de bataille citées, chacune protégée par
    `KeepTogether` pour ne jamais couper une carte en plein milieu d'une
    sous-tactique à un saut de page — mais sans forcer de saut entre deux
    cartes : assez compactes (`render_tactic_card`) pour que les 2 tactiques
    citées par une liste (le cas courant) s'empilent naturellement sur une
    seule page."""
    if not cards:
        return None
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=_CARD_PAGE_MARGIN, rightMargin=_CARD_PAGE_MARGIN, topMargin=_CARD_PAGE_MARGIN, bottomMargin=_CARD_PAGE_MARGIN,
        title="Cartes de tactique de bataille",
    )
    story: list = []
    for card in cards:
        if story:
            story.append(Spacer(1, 6 * mm))
        story.append(KeepTogether([card]))
    doc.build(story, onFirstPage=_draw_page_bg, onLaterPages=_draw_page_bg)
    return buf.getvalue()


def _build_warscroll_cards_pdf(warscrolls: list[WarscrollData], regiment_notes: dict[str, str]) -> bytes | None:
    if not warscrolls:
        return None
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=_CARD_PAGE_MARGIN, rightMargin=_CARD_PAGE_MARGIN, topMargin=_CARD_PAGE_MARGIN, bottomMargin=_CARD_PAGE_MARGIN,
        title="Profils d'unité (cartes)",
    )
    doc.build(build_warscroll_cards_flow(warscrolls, width=_UNIT_CARD_WIDTH, gap=_UNIT_CARD_GAP, regiment_notes=regiment_notes), onFirstPage=_draw_page_bg, onLaterPages=_draw_page_bg)
    return buf.getvalue()


def build_roster_pdf(
    list_path: str | Path,
    out_path: str | Path | None = None,
    index_path: str | Path | None = None,
    battletome_dir: str | Path | None = None,
    wahapedia_dir: str | Path | None = None,
    mode: RosterMode = "hybrid",
    faction_rules_fr_path: str | Path | None = None,
    generic_core_abilities_path: str | Path | None = None,
) -> RosterPdfResult:
    list_path = Path(list_path)
    parsed = parse_list_file(list_path)
    index = load_index(index_path) if index_path is not None else load_index()
    # Fichier vide (`{"factions": {}}`) tant qu'aucune faction n'est curée —
    # lecture à froid sans coût notable, inutile de la conditionner à `mode`
    # (`_fr_patch` ignore `frf` lui-même hors `fr`/`fr-extended`). Même
    # convention `*_path` optionnel que `index_path`, pour les tests.
    frf = load_faction_rules_fr(faction_rules_fr_path) if faction_rules_fr_path is not None else load_faction_rules_fr()
    faction_index = index.factions.get(parsed.base_faction)
    bt_path = (
        battletome_path(index, parsed.base_faction, battletome_dir)
        if battletome_dir is not None
        else battletome_path(index, parsed.base_faction)
    )
    wh = load_wahapedia(wahapedia_dir) if wahapedia_dir is not None else load_wahapedia()
    # une seule fois par PDF : cf. `warscroll_card._FACTION_KEYWORDS` pour
    # pourquoi ce n'est pas plutôt passé en paramètre à chaque appel de rendu.
    set_faction_specific_keywords(wh.faction_specific_keywords() if wh.available else frozenset())
    tactic_cards = load_tactic_cards()
    renown_prefix = parsed.faction.split("|", 1)[1].strip() if "|" in parsed.faction else None

    # Profils d'unité : rendus en carte maison (warscroll_card.py) à partir
    # de data/wahapedia/*.csv plutôt que copiés depuis le battletome — cf.
    # demande explicite de remplacer les pages PDF par les cartes pour les
    # unités. Wahapedia couvre la totalité du contenu AoS4 (bien plus large
    # que les 2 battletomes actuellement indexés en français), donc plus de
    # repli sur `find_pages`/copie de page pour une unité : introuvable ici
    # = réellement non trouvé, signalé comme tel plutôt que masqué par un
    # rendu différent.
    matched: list[str] = []
    unmatched_units: list[str] = []
    warscrolls_by_name: dict[str, WarscrollData] = {}
    wahapedia_used: list[str] = []
    for name in parsed.unique_unit_names():
        # `prefer_faction` : certaines unités d'armée de renom (ex.
        # "Bloodletters" pour "Legion of the First Prince") existent sous 2
        # lignes Wahapedia homonymes — la version de base (autre faction,
        # sans restriction) et une variante `parsed.base_faction`-only
        # ("This unit can only be taken in a <armée de renom> Army of
        # Renown", stats différentes) — sans indice de faction,
        # `find_warscroll` retombait sur la première ligne du CSV (la
        # version de base, erronée ici), signalé par l'utilisateur.
        ws = wh.find_warscroll(name, prefer_faction=parsed.base_faction) if wh.available else None
        if ws is None and wh.available and renown_prefix and name.startswith(renown_prefix):
            # les unités d'une armée de renom sont listées préfixées par son
            # nom (ex. "Legion of the First Prince Bloodletters") mais leur
            # warscroll Wahapedia est enregistré sous son nom nu ("Bloodletters").
            ws = wh.find_warscroll(name[len(renown_prefix):].strip(), prefer_faction=parsed.base_faction)
        if ws is not None:
            warscrolls_by_name[name] = ws
            matched.append(name)
        else:
            unmatched_units.append(name)

    # Aptitudes propres à chaque unité : correctifs/additions vérbatim
    # français (`data/faction_rules_fr.json`, cf. `faction_rules_fr.py`) —
    # uniquement en `fr`/`fr-extended` (`_fr_patch` renvoie `entries` tel
    # quel sinon), une unité non curée gardant ses aptitudes Wahapedia (EN)
    # inchangées.
    if mode in ("fr", "fr-extended"):
        for name, ws in list(warscrolls_by_name.items()):
            # Curé sous la faction PROPRE du warscroll résolu (`ws.faction_id`),
            # pas `parsed.base_faction` : une unité amenée par un Régiment de
            # Renom (ex. Skarbrand/Slaughterpriest/Bloodreavers/Skullreapers
            # via un Régiment Blades of Khorne cité par une liste Slaves to
            # Darkness) est curée sous sa faction d'origine, jamais sous celle
            # de la liste qui la cite — même raisonnement que la résolution du
            # Régiment de Renom lui-même ci-dessus. Repli sur `parsed.base_faction`
            # si `faction_id` n'est pas résolu (id manquant/inconnu), identique
            # au comportement précédent pour toute unité native de la liste.
            unit_faction = wh.faction_name(ws.faction_id) or parsed.base_faction
            overrides = get_unit_ability_overrides(frf, unit_faction, name)
            if overrides:
                warscrolls_by_name[name] = _dc_replace(ws, abilities=apply_fr_overrides(ws.abilities, overrides))

    # Armée de Renom : ses propres règles (Faction_abilities.csv, groupées
    # par catégorie) remplacent tout ou partie de celles de la faction de
    # base — calculé *avant* `_resolve_rules` pour pouvoir lui passer les
    # catégories à omettre côté battletome (cf. `_AOR_REPLACES`).
    renown_army: tuple[str, dict[str, list[AbilityEntry]]] | None = None
    renown_categories: frozenset[str] = frozenset()
    if renown_prefix and wh.available:
        grouped = wh.find_renown_army_rules(renown_prefix)
        if grouped:
            renown_army = (renown_prefix, grouped)
            renown_categories = frozenset(grouped)

    battletome_rules, generic_manifestation_sections, tactic_sections, wahapedia_lore_blocks, rules_unmatched, lore_wahapedia_used, rule_card_labels, rule_ability_pool, manifestation_warscrolls = _resolve_rules(
        parsed, faction_index, index, wh, tactic_cards, renown_categories, mode=mode, frf=frf,
        renown_army=renown_army, tactic_card_width=_TACTIC_CARD_WIDTH,
    )
    wahapedia_used.extend(lore_wahapedia_used)

    if renown_army is not None:
        renown_name = renown_army[0]
        if f"Armée de Renom — {renown_name}" in rule_card_labels:
            # curation vérbatim française complète (`_renown_army_pool`,
            # `fr`/`fr-extended` seulement) : déjà rendu sur la carte de
            # règles fusionnée par `_resolve_rules`, ne doit plus apparaître
            # dans l'annexe anglaise ni y être rattaché par l'appelant.
            renown_army = None
        else:
            wahapedia_used.append(f"{renown_name} — Army of Renown Rules (EN, Wahapedia)")
        if "Spell Lore" in renown_categories and any(u.startswith("Domaine de sorts") for u in rules_unmatched):
            rules_unmatched = [u for u in rules_unmatched if not u.startswith("Domaine de sorts")]

    # Un Régiment de Renom natif d'une faction (PDF officiel propre, cf.
    # `faction_rules_fr.py`) peut avoir ses aptitudes vérbatim françaises
    # (`get_regiment_of_renown_overrides`, `fr`/`fr-extended` seulement) —
    # appliquées ici, *avant* le partage single/grouped ci-dessous, pour que
    # les deux chemins (aptitude repliée sur une unité, ou pool fusionné)
    # héritent du texte déjà patché sans double logique. `regiment_curated`
    # retient quels régiments l'ont reçu, pour ne compter ni dans
    # `wahapedia_used` (pas un repli anglais) ni dans l'annexe Wahapedia.
    regiments_of_renown: list[tuple[str, RegimentOfRenownData | None]] = []
    regiment_curated: set[str] = set()
    for ror in parsed.regiments_of_renown:
        ror_data = wh.find_regiment_of_renown(ror.name) if wh.available else None
        if ror_data is not None:
            if mode in ("fr", "fr-extended"):
                # Curé sous la faction d'ORIGINE du Régiment de Renom
                # (`RegimentOfRenownData.faction_id`), pas `parsed.base_faction`
                # (la faction de la liste qui le cite) : plusieurs Régiments
                # (ex. Blades of Khorne "The Exiled One"/"The Red Revelation")
                # sont explicitement exclus de leur propre liste d'inclusion
                # (Wahapedia `Warscrolls_RoRfactions.csv`) — seules d'autres
                # factions Chaos peuvent les citer, donc `parsed.base_faction`
                # ne correspondrait jamais à la clé sous laquelle ce Régiment
                # est curé. Repli sur `parsed.base_faction` si la faction
                # d'origine n'est pas résolue (id manquant/inconnu).
                origin_faction = wh.faction_name(ror_data.faction_id) or parsed.base_faction
                overrides = get_regiment_of_renown_overrides(frf, origin_faction, ror_data.name)
                if overrides:
                    ror_data = _dc_replace(ror_data, abilities=apply_fr_overrides(ror_data.abilities, overrides))
                    regiment_curated.add(ror.name)
            if ror.name not in regiment_curated:
                wahapedia_used.append(f"Regiment of Renown : {ror.name} (EN, Wahapedia)")
        else:
            rules_unmatched.append(f"Regiment of Renown : {ror.name}")
        regiments_of_renown.append((ror.name, ror_data))

    # Un Regiment of Renown à une seule unité membre n'a rien de distinct de
    # cette unité pour le lecteur : son aptitude propre rejoint directement
    # sa carte (petite note de provenance + aptitude en plus) plutôt qu'une
    # section « Regiment of Renown » à part dans l'annexe. Un Régiment à
    # plusieurs membres curé en français (`regiment_curated`) rejoint le pool
    # d'aptitudes fusionné (`regiment_ability_pool`, badge d'origine dédié)
    # au lieu de l'annexe anglaise Wahapedia — seul un Régiment non curé (ou
    # curé mais résolu en mode `hybrid`/`en`) tombe encore dans
    # `grouped_regiments`.
    single_unit_ror_extras: dict[str, tuple[str, list[AbilityEntry]]] = {}
    grouped_regiments: list[tuple[str, RegimentOfRenownData | None]] = []
    regiment_ability_pool: list[AbilityEntry] = []
    for ror_name, ror_data in regiments_of_renown:
        member = _strip_all_tags(ror_data.composition[0]) if ror_data and len(ror_data.composition) == 1 else None
        if member is not None and member in warscrolls_by_name:
            single_unit_ror_extras[member] = (ror_name, ror_data.abilities)
        elif ror_name in regiment_curated:
            regiment_ability_pool.extend(tag_ability_origin(ror_data.abilities, f"Régiment de Renom : {ror_name}"))
        else:
            grouped_regiments.append((ror_name, ror_data))

    # Optimisations (Traits Héroïques/Artefacts de Pouvoir/Traits
    # Monstrueux/catégories saisonnières propres à la faction, ex. StD
    # "Brands of the Dark Gods"/"Ensorcelled Banners") : choisies une seule
    # fois pour toute la liste puis rattachées à une seule unité — jamais
    # montrées en bloc générique (cf. `_resolve_rules`, qui marque désormais
    # `heroic_traits_artefacts` couvert sans jamais l'ajouter au pool), une
    # optimisation non choisie n'apparaissant nulle part, comme une unité non
    # choisie. Résolues par correspondance de nom sur les options ` • ... `
    # de chaque unité (`WahapediaLookup.find_unit_enhancement`) et rattachées
    # à sa carte plus bas — même mécanisme que l'aptitude d'un Regiment of
    # Renown à une seule unité membre (`single_unit_ror_extras` ci-dessus).
    unit_enhancements: dict[str, list[AbilityEntry]] = {}
    enhancements_included: list[str] = []
    if wh.available:
        # Correctifs vérbatim français pour cette catégorie (pas de `scope` —
        # toutes les optimisations de la faction, comme côté Wahapedia) :
        # récupérés une seule fois, appliqués ci-dessous par nom sur chaque
        # optimisation trouvée (même mécanisme que `_fr_patch`, appliqué ici
        # à une entrée unique plutôt qu'un pool entier).
        heroic_overrides = (
            get_faction_category_overrides(frf, parsed.base_faction, "heroic_traits_artefacts")
            if mode in ("fr", "fr-extended") else []
        )
        # Cf. `_find_pledge_battle_trait` : unités StD qui commencent la
        # bataille déjà marquées (Prince Démon, porteur de Bannière
        # Ensorcelée) — la Trait de Bataille "Voué à <Dieu>" correspondante
        # leur est rattachée en plus, ci-dessous après la boucle.
        pledged_gods: dict[str, set[str]] = {}
        for regiment in parsed.regiments:
            for unit in regiment.units:
                if unit.name not in warscrolls_by_name:
                    continue
                for option in unit.options:
                    match = wh.find_unit_enhancement(parsed.base_faction, option)
                    if match is not None:
                        label, entry = match
                        entry_name = entry.name.strip().upper()
                        if heroic_overrides:
                            matching = [o for o in heroic_overrides if (o.get("wahapedia_name") or "").strip().upper() == entry_name]
                            if matching:
                                entry = apply_fr_overrides([entry], matching)[0]
                        unit_enhancements.setdefault(unit.name, []).extend(tag_ability_origin([entry], label))
                        enhancements_included.append(f"{label} : {entry.name} → {unit.name}")
                        god = _BANNER_PLEDGED_GOD.get(entry_name)
                        if god:
                            pledged_gods.setdefault(unit.name, set()).add(god)
                        continue
                    pledge_match = _PLEDGE_OPTION_RE.search(option)
                    if pledge_match:
                        pledged_gods.setdefault(unit.name, set()).add(pledge_match.group(1).upper())
        for unit_name, gods in pledged_gods.items():
            for god in sorted(gods):
                pledge_entry = _find_pledge_battle_trait(wh, frf, parsed.base_faction, mode, god)
                if pledge_entry is None:
                    continue
                unit_enhancements.setdefault(unit_name, []).extend(tag_ability_origin([pledge_entry], "Trait de Bataille"))
                enhancements_included.append(f"Trait de Bataille : {pledge_entry.name} → {unit_name}")

    warscrolls_for_cards: list[WarscrollData] = []
    regiment_notes: dict[str, str] = {}
    for name in matched:
        ws = warscrolls_by_name[name]
        extras = list(unit_enhancements.get(name, []))
        if name in single_unit_ror_extras:
            ror_name, ror_extras = single_unit_ror_extras[name]
            extras += ror_extras
            regiment_notes[ws.name] = f"Regiment of Renown — {ror_name}"
        if extras:
            ws = _dc_replace(ws, abilities=list(ws.abilities) + extras)
        warscrolls_for_cards.append(ws)
    # Ordre des cartes : Héros (toute base confondue) d'abord, puis
    # Infanterie/Cavalerie/Bêtes/Monstres/Machines de Guerre — demande
    # explicite de l'utilisateur ; tri stable, l'ordre relatif au sein d'un
    # même rang reste celui de la liste (régiment du général, puis régiment
    # 1, 2...). Cf. `_role_rank`.
    warscrolls_for_cards.sort(key=lambda ws: _role_rank(ws.role))
    # les manifestations invocables par le domaine choisi rejoignent la même
    # feuille de cartes, à la suite des unités de la liste — ce sont des
    # profils complets au même titre qu'une unité, juste optionnels/
    # invoqués en jeu plutôt que déployés d'entrée.
    warscrolls_for_cards.extend(manifestation_warscrolls)

    # Règles de Saison 2026-27 / Aptitudes Génériques / règles de faction
    # (`rule_ability_pool`, déjà résolu par `_resolve_rules`) rejoignent
    # toutes le *même* bassin puis une seule carte triée par bandeau de
    # phase — demande explicite de l'utilisateur : un joueur qui consulte
    # cette carte raisonne "je suis en phase des héros, qu'est-ce que j'ai le
    # droit de faire ?", pas par type de règle ; les séparer sur 3 cartes
    # (Saison / Générique / Faction, chacune déjà triée par phase en interne)
    # l'obligeait à vérifier 3 fois la même phase pour la même question.
    # `tag_ability_origin` pose un badge d'origine par source ("Saison"/
    # "MdG"/le nom de faction ou d'Armée de Renom) pour rester
    # identifiable malgré la fusion.
    #
    # Exception demandée par l'utilisateur pour Seraphon : "Le Grand
    # Dessein"/"Faites Avancer le Grand Dessein" choisissent/activent les 4
    # Astérismes (mot-clé Wahapedia "Asterism"), qui ont chacun leur propre
    # `ability_phase` réel et finissent donc éparpillés sur plusieurs pages
    # de la grande carte fusionnée (trop de contenu Saison/MdG partage les
    # mêmes bandeaux "Déploiement"/"Début de round" pour que les 6 tiennent
    # ensemble sur une page, même avec le bandeau virtuel "asterism" de
    # `warscroll_card._PHASE_ORDER`). Plutôt que de retravailler le tri
    # partagé par *toute* carte fusionnée (régression potentielle pour
    # n'importe quelle autre faction), ces 6 aptitudes ("Traits de Bataille")
    # rejoignent leur propre petite carte à part (cf. `rule_cards` plus bas)
    # — assez courte pour tenir sur une seule page sans jamais se disputer
    # l'espace avec le reste. Déclenché uniquement par la présence du
    # mot-clé "Asterism" (propre à Seraphon) : aucun effet pour aucune autre
    # faction/liste.
    battle_traits_entries = [
        ab for ab in rule_ability_pool
        if any(kw.strip().lower() == "traits de bataille" for kw in (ab.keywords or "").split(","))
    ]
    separate_battle_traits_card = None
    if battle_traits_entries and any("asterism" in (ab.keywords or "").lower() for ab in rule_ability_pool):
        rule_ability_pool = [ab for ab in rule_ability_pool if ab not in battle_traits_entries]
        separate_battle_traits_card = render_rule_card(
            "Traits de Bataille", battle_traits_entries, width=_RULE_CARD_WIDTH, subtitle=parsed.base_faction,
        )

    combined_pool = list(rule_ability_pool) + regiment_ability_pool
    season_entries = load_season_rules()
    if season_entries:
        combined_pool.extend(tag_ability_origin(season_entries, "Saison"))

    # Aptitudes Génériques (mode `fr-extended` uniquement) : superset complet
    # de `MdG26-27 Aptitudes.pdf`, pas seulement les 4 règles de saison — cf.
    # `generic_core_abilities.py`. Fichier vide tant que non curé (liste
    # vide, pas d'erreur) : le mode se comporte alors comme `fr` sans rien
    # ajouter au bassin.
    generic_entries: list[AbilityEntry] = []
    if mode == "fr-extended":
        generic_entries = (
            load_generic_core_abilities(generic_core_abilities_path)
            if generic_core_abilities_path is not None else load_generic_core_abilities()
        )
        if generic_entries:
            combined_pool.extend(tag_ability_origin(generic_entries, "MdG"))

    combined_rule_card = (
        render_rule_card("Aptitudes", combined_pool, width=_RULE_CARD_WIDTH, subtitle=parsed.base_faction)
        if combined_pool else None
    )

    rules_included = (
        (["Règles de Saison 2026-27"] if season_entries else [])
        + (["Aptitudes Génériques — MdG26-27"] if generic_entries else [])
        + rule_card_labels
        + [label for label, _pages in battletome_rules]
        + [label for label, _pages in generic_manifestation_sections]
        + [label for label, _flowable in tactic_sections]
        + [label for label, _entries in wahapedia_lore_blocks]
        + enhancements_included
        + ([f"{renown_army[0]} — Army of Renown Rules"] if renown_army else [])
        + [
            f"Régiment de Renom : {name} (FR)" if name in regiment_curated else f"Regiment of Renown : {name}"
            for name, data in regiments_of_renown if data is not None
        ]
    )

    writer = PdfWriter()
    for page in PdfReader(BytesIO(_build_cover_pdf(parsed, unmatched_units, rules_unmatched, wahapedia_used))).pages:
        writer.add_page(page)

    rule_cards: list = []
    if separate_battle_traits_card is not None:
        rule_cards.append(separate_battle_traits_card)
    if combined_rule_card is not None:
        rule_cards.append(combined_rule_card)
    rule_cards_bytes = _build_rule_cards_pdf(rule_cards)
    if rule_cards_bytes is not None:
        for page in PdfReader(BytesIO(rule_cards_bytes)).pages:
            writer.add_page(page)

    seen_battletome_pages: set[int] = set()
    if bt_path is not None and bt_path.exists():
        source_reader = PdfReader(str(bt_path))
        _append_pages(writer, source_reader, seen_battletome_pages, battletome_rules)

    gm_path = generic_manifestation_lores_path(index)
    if gm_path is not None and gm_path.exists() and generic_manifestation_sections:
        gm_reader = PdfReader(str(gm_path))
        _append_pages(writer, gm_reader, set(), generic_manifestation_sections)

    tactic_cards_bytes = _build_tactic_cards_pdf([flowable for _label, flowable in tactic_sections])
    if tactic_cards_bytes is not None:
        for page in PdfReader(BytesIO(tactic_cards_bytes)).pages:
            writer.add_page(page)

    cards_bytes = _build_warscroll_cards_pdf(warscrolls_for_cards, regiment_notes)
    if cards_bytes is not None:
        for page in PdfReader(BytesIO(cards_bytes)).pages:
            writer.add_page(page)

    appendix_bytes = _build_wahapedia_appendix_pdf(
        wahapedia_lore_blocks, renown_army, grouped_regiments,
    )
    if appendix_bytes is not None:
        for page in PdfReader(BytesIO(appendix_bytes)).pages:
            writer.add_page(page)

    # Chaque section (couverture, cartes de règle, cartes de tactique, cartes
    # de warscroll, annexe) est construite comme un mini-PDF `reportlab`
    # séparé (son propre `SimpleDocTemplate.build`), donc chacun réembarque
    # sa propre copie du fond `_STONE_TEXTURE` (~1,3 Mo) : `add_page` copie
    # ces pages telles quelles, sans dédoublonner un XObject par ailleurs
    # identique octet pour octet entre les pages. `compress_identical_objects`
    # fusionne ces objets par hash de contenu en un seul, partagé par toutes
    # les pages — le gain dominant, avant même la recompression des pages de
    # battletome copiées (`_compress_page_images`).
    writer.compress_identical_objects()

    if out_path is None:
        out_dir = DEFAULT_OUTPUT_DIR / _DEFAULT_OUTPUT_SUBDIR[mode]
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{list_path.stem}.pdf"
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "wb") as f:
        writer.write(f)

    return RosterPdfResult(
        output_path=out_path,
        units_matched=matched,
        units_unmatched=unmatched_units,
        rules_included=rules_included,
        rules_unmatched=rules_unmatched,
        wahapedia_used=wahapedia_used,
    )
