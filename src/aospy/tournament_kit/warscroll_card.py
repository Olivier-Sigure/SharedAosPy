"""Rendu « carte maison » d'un warscroll (`WarscrollData`), en remplacement de
la copie de page PDF du battletome — mise en forme validée sur une maquette
HTML (artefact partagé avec l'utilisateur) puis adaptée aux contraintes de
reportlab : bandeau de phase horizontal (pas de texte pivoté dans une
cellule à hauteur dynamique) et badges en texte coloré/gras (reportlab ne
peint pas de fond coloré à l'intérieur d'un `Paragraph`) plutôt qu'en
pastilles pleines — même organisation et même code couleur que la maquette,
juste une traduction honnête vers ce que le moteur de rendu sait faire.

Aucune traduction du texte de règle ni des noms (unité/aptitude/arme/mot-clé
CSV) — seuls les libellés qu'on invente nous-mêmes (Passif, Réaction,
Ma phase/Phase ennemi/Les 2 phases, noms de phase) sont en français, les
7 derniers vérifiés sur `data/Manuel du général/MdG26-27 Aptitudes.pdf`.
"""

from __future__ import annotations

import math
import re
from dataclasses import replace as _dc_replace
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Flowable, KeepTogether, Paragraph, Spacer, Table, TableStyle

from .translation.tactic_cards import SubTactic, TacticCard
from .translation.wahapedia_lookup import AbilityEntry, WarscrollData, WeaponEntry

#: police des noms de carte (unité/règle/tactique) — Cinzel Bold, la même que
#: la maquette HTML (`font-family:"Cinzel"`, chargée depuis Google Fonts,
#: `.card .head h2{font-weight:700}`) plutôt que le Helvetica-Bold générique
#: utilisé avant : un vrai display serif capitalisé, cohérent avec
#: l'esthétique "tome" du reste de la carte (bandeau nom/rôle sombre,
#: parchemin). Embarqué en TTF plutôt que référencé par un chemin système
#: (`scratch/build_pdf.py` pointait vers `C:/Windows/Fonts/...`, un chemin
#: Windows qui ne marche que sur une machine précise) : Cinzel est sous SIL
#: Open Font License, librement redistribuable, donc le fichier vit dans le
#: paquet (`assets/Cinzel-Bold.ttf`, embarqué via `package-data` dans
#: `pyproject.toml`) et se charge par chemin relatif à ce module, portable
#: partout. Enregistré une seule fois, au niveau module (pas dans une
#: fonction appelée par carte) ; repli silencieux sur Helvetica-Bold si le
#: fichier venait à manquer (ex. install sans les données du paquet) plutôt
#: que de faire planter toute la génération de PDF pour une police décorative.
CARD_TITLE_FONT = "Helvetica-Bold"
try:
    pdfmetrics.registerFont(TTFont("Cinzel-Bold", str(Path(__file__).parent / "assets" / "Cinzel-Bold.ttf")))
    CARD_TITLE_FONT = "Cinzel-Bold"
except Exception:
    pass

# -- Code couleur des phases : mêmes valeurs hex que la maquette HTML,
# échantillonnées au pixel sur le Manuel du général (cf. historique de
# conception) ; "any" (vert) est la 9e catégorie, hors des 8 bandeaux du
# livre, pour les réactions qui ne sont liées à aucune phase précise.
# "deploy" (Phase de Déploiement, avant le round 1 — pas l'une des 7 phases
# du cycle de round) échantillonné séparément sur le PDF « Armée de Renom »
# LRL fourni par l'utilisateur (bandeau noir de "Phase de Déploiement",
# proche mais pas identique au noir de "start") : une aptitude de
# déploiement (`ability_phase` Wahapedia vide côté `generic_core_abilities.json`/
# `season_rules.json`, ces règles n'étant pas dans le CSV Wahapedia)
# retombait sinon dans le bandeau vert "any", signalé par l'utilisateur.
_PHASE_COLORS: dict[str, tuple[str, str]] = {
    "deploy": ("#282d31", "#f2ecdb"),
    "round_start": ("#1f2d3d", "#eaf1f8"),
    "asterism": ("#2a2456", "#e8e6f5"),
    "start": ("#211e20", "#f2ecdb"),
    "hero": ("#a3862f", "#221a08"),
    "move": ("#7d7b86", "#1c1a22"),
    "shoot": ("#2c5964", "#eaf4f6"),
    "charge": ("#b8632f", "#241505"),
    "melee": ("#7c333c", "#fbeaec"),
    "end": ("#5f3f71", "#f4ecf9"),
    "any": ("#4f6b2e", "#eef2e2"),
}
_PHASE_LABELS: dict[str, str] = {
    "deploy": "Déploiement", "round_start": "Début de round", "asterism": "Astérisme",
    "start": "Début de tour", "hero": "Phase des héros",
    "move": "Phase de mouvement", "shoot": "Phase de tir", "charge": "Phase de charge", "melee": "Phase de mêlée",
    "end": "Fin de tour", "any": "N'importe quelle phase",
}
#: ordre canonique du tour (cf. AoS4) — "deploy" avant "round_start" avant
#: "start" : le déploiement précède le round 1, et « Début de Round »
#: (déclenchement unique, avant qu'aucun des deux joueurs n'ait pris son
#: tour — cf. `_classify_phase`) précède « Début de Tour » (déclenchement
#: propre à chaque tour, donc 2 fois par round) — 2 moments de règle
#: distincts que Wahapedia confond tous les deux sous `ability_phase`
#: = "Start of Turn". "any" toujours en dernier, catégorie hors séquence.
#: "asterism" (cf. `_classify_phase`) tout en tête, avant même "deploy" :
#: les 4 Astérismes Séraphons (mot-clé Wahapedia "Asterism") ont chacun
#: leur propre `ability_phase` réel (Phase des Héros/Mêlée/Charge/Réaction
#: défensive) mais sont choisis/activés ensemble via "Le Grand Dessein"/
#: "Faites Avancer le Grand Dessein" (bandeaux "deploy"/"round_start" qui
#: suivent) — les séparer par bandeau de phase réel les éparpillerait sur
#: toute la carte alors qu'ils forment un seul bloc de règle thématique.
#: Placé en tête plutôt qu'entre "deploy" et "round_start" : sur une carte
#: fusionnée (`fr-extended`), "deploy"/"round_start" portent aussi des
#: règles de saison/du Manuel du général sans rapport, volumineuses au
#: point de pousser un bandeau "asterism" intercalé sur la page suivante
#: — en tête, les 4 Astérismes (courts) restent sur la même page que "Le
#: Grand Dessein"/"Faites Avancer le Grand Dessein" qui les suivent
#: directement, quitte à repousser le contenu générique sans rapport.
#: Cas localisé à ce mot-clé (propre à Seraphon) : ne change rien pour
#: aucune autre aptitude/faction.
_PHASE_ORDER = [
    "asterism", "deploy", "round_start", "start", "hero", "move", "shoot", "charge", "melee", "end", "any",
]

#: reportlab ne peint pas de fond derrière un texte qui coule dans un
#: `Paragraph` (pas de vraie pastille comme dans la maquette HTML) — les
#: teintes doivent donc être nettement plus saturées que le corps de texte
#: (gris/noir) pour continuer à se voir comme des badges plutôt que du texte
#: normal, avec un léger cadrage `[ ]` en plus pour rester lisibles même en
#: N&B.
_BADGE_NEUTRAL = "#2e5c8a"   # timing : fréquence, condition, passif
_BADGE_GOLD = "#8a6d24"      # classification : mots-clés d'aptitude
_BADGE_STAT = "#1f6b78"      # stat d'arme mise en avant : portée
_BADGE_REACT = "#8c1f1f"     # alerte : réaction
_BADGE_SPELL = "#5b3a8f"     # sort — valeur d'incantation (points_type "Spell")
_BADGE_PRAYER = "#2e6b4f"    # prière — valeur de prière (points_type "Prayer")
_BADGE_COMMAND = "#7a4a1f"   # point de commandement — coût en PC (points_type "Command")
_BADGE_BLOOD = "#7a1620"     # dime de sang — coût en points de sang (points_type "Blood tithe", Blades of Khorne)
_BADGE_FACTION = "#6b2545"   # mot-clé d'aptitude propre à une seule faction (ex. Delusion, Tidal) — cf. `_keyword_pills`

#: mots-clés d'aptitude (`AbilityEntry.keywords`) propres à une seule faction —
#: posé une fois par `set_faction_specific_keywords` (appelé par
#: `pdf_builder.build_roster_pdf` juste après avoir chargé `WahapediaLookup`,
#: cf. `WahapediaLookup.faction_specific_keywords`) plutôt que passé en
#: paramètre à travers la dizaine de fonctions qui construisent le tableau
#: d'aptitudes (`_ability_row_flowables` -> ... -> `_append_ability_groups`) :
#: un seul jeu de données pour toute la génération d'un PDF, jamais rechargé
#: ni recalculé par carte. Normalisé en minuscules, comme le renvoie
#: `faction_specific_keywords`.
_FACTION_KEYWORDS: frozenset[str] = frozenset()


def set_faction_specific_keywords(keywords: frozenset[str]) -> None:
    """À appeler une fois par génération de PDF (cf. `pdf_builder.py`) avant
    tout rendu de carte — voir `_FACTION_KEYWORDS`."""
    global _FACTION_KEYWORDS
    _FACTION_KEYWORDS = keywords

_PHASE_FIELD_TO_KEY = {
    "deployment phase": "deploy",
    "start of turn": "start", "hero phase": "hero", "movement phase": "move",
    "shooting phase": "shoot", "charge phase": "charge", "combat phase": "melee",
    "end of turn": "end",
}

#: `_qualifier_label` ne couvre que les phases qualifiées "Your/Any/Enemy" —
#: une condition combinant fréquence + timing sans qualificatif (ex. les
#: Règles de Saison 2026-27, `season_rules.py`, ou "MURDER-WON TROPHIES" des
#: Blades of Khorne côté Wahapedia) retombait sinon sur le texte brut anglais
#: en majuscules (`condition.upper()`) faute de correspondance exacte —
#: ajoutée ici au fil des cas rencontrés plutôt que devinée à l'avance.
_PLAIN_CONDITION_FR = {
    "deployment phase": "PHASE DE DÉPLOIEMENT",
    "once per battle (army), deployment phase": "PHASE DE DÉPLOIEMENT",
    "once per turn (army), start of battle round": "DÉBUT DU ROUND DE BATAILLE",
    # ex. « Depict Rune » (Lumineth Realm-lords) et 8 autres aptitudes
    # partageant ce même condition verbatim — cf. `_ROUND_START_RE` pour la
    # reclassification de phase qui va avec (« Début de Round », pas
    # « Début de Tour »). Pas de pastille de fréquence séparée pour cette
    # condition (cf. `_FREQ_RE`) : « Once Per Battle Round » ne veut pas dire
    # « une fois pour toute la bataille » (comme « Once Per Battle » tout
    # court) mais « une fois par round », déjà entièrement porté par ce
    # libellé — une pastille fréquence à côté serait redondante, et
    # l'ancienne regex la rendait carrément fausse (elle affichait
    # « ×1 / BATAILLE », lu comme « une fois pour toute la partie »).
    "once per battle round (army), start of battle round": "1 / BATTLE ROUND",
}

_QUALIFIER_RE = re.compile(
    r"\b(Your|Any|Enemy)\b\s+(?:Hero Phase|Movement Phase|Shooting Phase|Charge Phase|Combat Phase|Turn|Battle Round)",
    re.IGNORECASE,
)
_QUALIFIER_FR = {"your": "Ma phase", "any": "Les 2 phases", "enemy": "Phase ennemi"}
#: `(?!\s+Round)` : « Once Per Battle Round » (une fois *par round*, peut se
#: redéclencher à chaque round) n'est pas « Once Per Battle » (une fois pour
#: toute la bataille) — sans cette garde, la regex matchait quand même sur
#: le seul mot « Battle » et affichait la pastille fréquence « ×1 / BATAILLE »,
#: fausse et contredite par le texte de condition affiché juste à côté (cf.
#: `_PLAIN_CONDITION_FR`/`_condition_pill`, qui porte déjà cette information
#: pour ce cas précis — pas de pastille fréquence dupliquée à côté).
_FREQ_RE = re.compile(r"Once Per (Turn|Battle)(?!\s+Round)(?:\s*\((Army)\))?", re.IGNORECASE)
#: Reclassifie en phase « Début de Round » (cf. `_classify_phase`) toute
#: aptitude dont le `condition` mentionne « Start of (the) (First) Battle
#: Round » — Wahapedia ne distingue pas ce moment (unique, avant qu'aucun des
#: 2 joueurs n'ait pris son tour) de « Start of Turn » (2 fois par round, une
#: fois par tour) dans son propre champ `ability_phase`, qui vaut "Start of
#: Turn" pour les deux. Volontairement plus étroit que « contient "battle
#: round" » : ne doit pas matcher une simple fréquence sans déclencheur de
#: timing (ex. « Once Per Battle Round, Your Hero Phase », un vrai
#: déclenchement en phase des héros, cf. `_classify_phase`).
_ROUND_START_RE = re.compile(r"\bstart of (?:the )?(?:first )?battle round\b", re.IGNORECASE)
_WIELDER_RATIO_RE = re.compile(
    r"(\d+/\d+)\s+models?\s+can\s+replace\s+(?:their|its)\s+[\w\s'’-]+?\s+with\s+an?\s+([\w\s'’-]+?)\.",
    re.IGNORECASE,
)
#: `WIZARD (N)`/`PRIEST (N)` — cf. `WahapediaLookup.find_warscroll`, qui
#: reconstitue ce format à partir de la colonne `parameter` de
#: `Warscrolls_keywords.csv`. Utilisé à la fois pour extraire le badge
#: d'en-tête (`_caster_badges`) et pour l'exclure de la liste de mots-clés en
#: bas de carte (`_visible_keywords`), afin de ne pas doublonner l'info.
_CASTER_KW_RE = re.compile(r"^(WIZARD|PRIEST)\s*\((\d+)\)$", re.IGNORECASE)


def _classify_phase(ability: AbilityEntry) -> str:
    """Détermine le bandeau de phase d'une aptitude. `ability_phase` (CSV
    Wahapedia, ou valeur posée à la main dans `season_rules.json`/
    `generic_core_abilities.json` — ces règles de coeur de jeu ne sont dans
    aucun CSV Wahapedia) mappe directement sur 8 des 9 catégories (7 phases
    du cycle de round + "Deployment Phase", qui précède le round 1 donc
    n'est pas l'une d'elles) ; `"Defensive reaction"` n'a pas d'équivalent
    dans le livre (le CSV ne distingue pas "aptitude toujours liée à une
    phase précise" de "réaction générique") et se reclasse à partir du
    texte : mention de `Fight ability`/`combat attack` -> Mêlée, `shooting
    attack` -> Tir, sinon -> vert (N'importe quelle phase). Pattern-matching
    sur un vocabulaire fixe, jamais un jugement au cas par cas ni une
    paraphrase du texte de règle lui-même — ce filtre textuel ne vaut que
    pour le texte anglais Wahapedia ; une aptitude hors CSV (JSON
    hand-curated, texte déjà en français — cf. `generic_core_abilities.py`/
    `season_rules.py`) doit porter son `ability_phase` déjà résolu à la main
    (même mini-vocabulaire anglais interne) plutôt que de compter sur ce
    repli, qui ne la reconnaîtrait jamais.

    Exception avant tout ça : `ability_phase == "Start of Turn"` avec un
    `condition` qui mentionne « Start of (the) (First) Battle Round »
    (`_ROUND_START_RE`) reclasse en « Début de Round » plutôt que « Début de
    Tour » — 2 moments de règle distincts (le round démarre une fois, avant
    qu'aucun tour n'ait commencé ; le tour démarre 2 fois par round) que
    Wahapedia confond tous les deux sous cette même valeur de champ, faute de
    catégorie dédiée dans son propre schéma.

    Même genre d'exception pour `ability_phase == "Start of Turn"` avec un
    `condition` qui mentionne « Deployment Phase » (ex. Skaven « THE LURKING
    VERMINTIDE » / « Le Raz-de-Vermine Rampant », et sa variante « Gnawfeast
    Clawpack » dont le `condition` est « Once Per Battle, Deployment Phase »)
    : reclasse en « Déploiement » — Wahapedia laisse là aussi `ability_phase`
    à sa valeur par défaut "Start of Turn" au lieu de "Deployment Phase" pour
    cette aptitude, alors que le placement en réserve qu'elle décrit se fait
    explicitement pendant le déploiement, pas au début d'un tour.

    Priorité absolue avant tout ce qui précède : le mot-clé Wahapedia
    "Asterism" (porté par les 4 Astérismes Séraphons, cf. `_PHASE_ORDER`)
    force le bandeau virtuel "asterism" quel que soit `ability_phase`."""
    if any(_keyword_key(kw) == "asterism" for kw in (ability.keywords or "").split(",") if kw.strip()):
        return "asterism"
    phase = (ability.ability_phase or "").strip().lower()
    if phase == "start of turn" and _ROUND_START_RE.search(ability.condition or ""):
        return "round_start"
    if phase == "start of turn" and "deployment phase" in (ability.condition or "").lower():
        return "deploy"
    if phase != "defensive reaction":
        return _PHASE_FIELD_TO_KEY.get(phase, "any")
    text = (ability.description or "").lower()
    if "fight ability" in text or "combat attack" in text:
        return "melee"
    if "shooting attack" in text:
        return "shoot"
    return "any"


#: ordre d'affichage des 4 catégories d'aptitude au sein d'un même bandeau de
#: phase — aptitudes normales d'abord, puis sorts/prières/manifestations,
#: dans cet ordre demandé par l'utilisateur.
_CATEGORY_ORDER = ["normal", "spell", "prayer", "manifestation"]
_CATEGORY_LABELS_FR = {"normal": "Aptitudes", "spell": "Sorts", "prayer": "Prières", "manifestation": "Manifestations"}
_CATEGORY_COLORS = {"normal": "#6b6555", "spell": _BADGE_SPELL, "prayer": _BADGE_PRAYER, "manifestation": _BADGE_STAT}


def _ability_category(ability: AbilityEntry) -> str:
    """Catégorie d'affichage d'une aptitude au sein de son bandeau de phase —
    `ability_category` (posé explicitement par `set_ability_category`, cf.
    plus bas) prime quand présent : le `points_type` d'une aptitude de
    convocation d'un domaine de manifestations vaut lui-même "Spell" ou
    "Prayer" côté Wahapedia (identique à un sort/une prière ordinaire), donc
    `points_type` seul ne peut jamais distinguer une manifestation d'un sort/
    d'une prière — seul l'appelant (`pdf_builder._resolve_rules`, qui sait de
    quel domaine chaque aptitude vient) peut trancher. En l'absence de ce
    marquage, `points_type` suffit à distinguer un sort/une prière d'une
    aptitude normale."""
    if ability.ability_category == "manifestation":
        return "manifestation"
    pts = (ability.points_type or "").strip()
    if pts == "Spell":
        return "spell"
    if pts == "Prayer":
        return "prayer"
    return "normal"


def set_ability_category(abilities: list[AbilityEntry], category: str) -> list[AbilityEntry]:
    """Marque explicitement la catégorie d'affichage de chaque aptitude — cf.
    `_ability_category` pour pourquoi c'est nécessaire (uniquement pour un
    domaine de manifestations, à ce jour)."""
    return [_dc_replace(ab, ability_category=category) for ab in abilities]


def _frequency_label(condition: str) -> str | None:
    m = _FREQ_RE.search(condition or "")
    if not m:
        return None
    label = "×1 / TOUR" if m.group(1).lower() == "turn" else "×1 / BATAILLE"
    if m.group(2):
        label += " (ARMÉE)"
    return label


def _qualifier_label(condition: str) -> str | None:
    m = _QUALIFIER_RE.search(condition or "")
    if not m:
        return None
    return _QUALIFIER_FR.get(m.group(1).lower())


#: Police/taille des badges pleins (fréquence, condition, mot-clé...),
#: partagée par `_pill_natural_width` pour mesurer un texte *avant* de
#: construire la pastille — `Table.wrap(0, 0)` avait été essayé pour ça, mais
#: `wrap` avec une largeur disponible nulle force un `Paragraph` à se
#: réenligner sur son mot le plus long (le seul moyen pour lui de tenir dans
#: 0pt de large), ce qui renvoyait une largeur "naturelle" bien plus petite
#: que la vraie largeur sur une ligne — le badge gardait alors `width=None`
#: (jugé à tort assez court pour `max_width`) mais se faisait quand même
#: réenligner au rendu final, cette fois contraint par la vraie largeur de
#: colonne disponible (ex. "MA PHASE" coupé en "MA PH"/"ASE"). Mesurer la
#: largeur d'une ligne non enroulée avec `stringWidth` directement (comme
#: `_min_rail_height` le fait déjà pour le bandeau de phase) évite le
#: problème : jamais de `wrap()` avant que la largeur réelle ne soit connue.
_PILL_FONT = "Helvetica"
_PILL_FONT_SIZE = 6.6
_PILL_H_PADDING = 10  # LEFTPADDING + RIGHTPADDING de `_pill` (5 + 5)
_PILL_RADIUS = 4  # rayon des coins arrondis d'une pastille (`ROUNDEDCORNERS`)
#: marge de sécurité ajoutée à `_pill_natural_width` : sans elle, la largeur
#: passée en `colWidths` au `Paragraph` interne (largeur - `_PILL_H_PADDING`)
#: retombe exactement sur `stringWidth`, et une simple erreur d'arrondi flottant
#: (`36.4066 - 10 == 26.406599999999997 < 26.4066`) suffit alors à faire
#: réenligner le texte sur 2 lignes ("FRAPPE" -> "FRAPP"/"E") alors qu'il tient
#: très exactement sur une — vu en le comparant à un rendu sans cette marge.
_PILL_WIDTH_SLACK = 0.75


def _pill_natural_width(text: str) -> float:
    return stringWidth(text, _PILL_FONT, _PILL_FONT_SIZE) + _PILL_H_PADDING + _PILL_WIDTH_SLACK


def _condition_pill(ability: AbilityEntry, max_width: float) -> tuple[Table, float] | None:
    """Le pendant `condition` (passif / réaction / qualificatif / brut) de
    `_freq_pill` — une seule pastille pleine, en pastille à liseré pour la
    réaction (elle reste la seule à porter *toujours* du texte de règle
    verbatim, donc potentiellement long — forcée à `max_width` pour se
    réenligner au lieu de déborder). Les autres badges (PASSIF, qualificatif,
    brut) se taillent d'abord sur leur propre contenu, comme les pastilles de
    mot-clé (`_keyword_pills`) — sans quoi le fond peint de la pastille
    s'étirait sur toute `max_width` même pour un texte court ("PASSIF").
    `max_width` ne sert de garde-fou (repli sur la même largeur forcée que la
    réaction) que si ce contenu se révèle malgré tout trop large une fois
    mesuré — un `condition` brut hors du vocabulaire couvert par
    `_PLAIN_CONDITION_FR` peut en théorie être long. La largeur renvoyée à
    côté de la pastille est celle réellement occupée (`max_width` si forcée,
    sinon la largeur naturelle) — c'est ce que `_pack_badges` utilise pour
    décider si la pastille suivante tient sur la même ligne."""
    condition = (ability.condition or "").strip()
    if not condition:
        return None
    if ability.is_reaction or "reaction:" in condition.lower():
        # le préfixe de fréquence précède parfois "Reaction:" dans le même
        # champ (ex. "Once Per Turn (Army), Reaction: ...") — la fréquence
        # est déjà extraite à part par `_freq_pill`, ne garder ici que le
        # déclencheur, tout ce qui précède "Reaction:" est jeté plutôt que
        # de le montrer en double.
        trigger = re.sub(r"^.*?reaction:\s*", "", condition, flags=re.IGNORECASE)
        trigger = _clean_text(trigger).strip()
        pill = _pill(f"<b>Réaction :</b> {trigger}", _BADGE_REACT, "#fbeaec", width=max_width, outline=True)
        return pill, max_width
    if condition.lower() == "passive":
        text = "PASSIF"
    else:
        qual = _qualifier_label(condition)
        text = qual.upper() if qual else _PLAIN_CONDITION_FR.get(condition.lower(), condition.upper())
    natural = _pill_natural_width(text)
    if natural > max_width:
        return _pill(text, _BADGE_NEUTRAL, "#eaf1f8", width=max_width), max_width
    return _pill(text, _BADGE_NEUTRAL, "#eaf1f8", width=None), natural


def _freq_pill(ability: AbilityEntry, max_width: float) -> tuple[Table, float] | None:
    freq = _frequency_label(ability.condition or "")
    if not freq:
        return None
    natural = _pill_natural_width(freq)
    if natural > max_width:
        return _pill(freq, _BADGE_NEUTRAL, "#eaf1f8", width=max_width), max_width
    return _pill(freq, _BADGE_NEUTRAL, "#eaf1f8", width=None), natural


#: Traduction du `points_type` d'une aptitude (Warscrolls_abilities.csv /
#: Faction_abilities.csv) vers le libellé de repli de sa pastille (utilisé
#: seulement quand l'aptitude ne porte aucune valeur numérique, cf.
#: `_cast_pill`) et vers la forme/couleur de son badge sinon — le
#: cercle/losange/hexagone de l'éditeur BattleScribe/Warhammer Age of
#: Sigmar: The App (cf. `_CastBadge`), qu'aucun badge ne portait encore ici
#: (perdu en repartant du prototype HTML, qui n'avait qu'une pastille
#: rectangulaire générique). `points` est la valeur d'incantation/de prière
#: ("7" -> "7+" à lancer) pour les deux premiers, un coût brut (en PC ou en
#: points de sang) pour "Command"/"Blood tithe" — jamais un seuil "+".
#: "Blood tithe" (points_type de Faction_abilities.csv, propre aux Blades of
#: Khorne) n'a pas encore de faction important son armée depuis Wahapedia,
#: mais la donnée existe déjà dans le CSV — le badge est câblé par
#: anticipation plutôt que laissé en `_BADGE_GOLD` générique.
_CAST_BADGE_LABELS = {"Spell": "SORT", "Prayer": "PRIÈRE", "Command": "PC", "Blood tithe": "DIME DE SANG"}
_CAST_BADGE_COLORS = {
    "Spell": _BADGE_SPELL, "Prayer": _BADGE_PRAYER, "Command": _BADGE_COMMAND, "Blood tithe": _BADGE_BLOOD,
}
_CAST_BADGE_SHAPES = {"Spell": "circle", "Prayer": "diamond", "Command": "hexagon", "Blood tithe": "hexagon"}
_CAST_BADGE_FG = {"Spell": "#f3eefa", "Prayer": "#e6f3ec", "Command": "#f7ecd6", "Blood tithe": "#f9e3e3"}


def _cast_pill(ability: AbilityEntry, max_width: float) -> tuple[Flowable, float] | None:
    pts_type = (ability.points_type or "").strip()
    if not pts_type:
        return None
    value = (ability.points or "").strip()
    bg = _CAST_BADGE_COLORS.get(pts_type, _BADGE_GOLD)
    fg = _CAST_BADGE_FG.get(pts_type, "#f7ecd6")
    if value:
        text = f"{value}+" if pts_type in ("Spell", "Prayer") else value
        shape = _CAST_BADGE_SHAPES.get(pts_type, "circle")
        badge = _CastBadge(shape, text, bg, fg)
        return badge, badge.size
    # aucune valeur à inscrire au centre d'un badge : un sigle ("PC") n'a pas
    # sa place dans une forme aussi petite, on retombe sur la pastille
    # rectangulaire générique avec le libellé complet.
    label = _CAST_BADGE_LABELS.get(pts_type, pts_type.upper())
    natural = _pill_natural_width(label)
    if natural > max_width:
        return _pill(label, bg, fg, width=max_width), max_width
    return _pill(label, bg, fg, width=None), natural


def _keyword_pills(ability: AbilityEntry) -> list[tuple[Table, float]]:
    if not ability.keywords:
        return []
    # "Deploy"/"Deployment" fait doublon avec la pastille de condition quand
    # celle-ci vaut déjà "Deployment Phase" (`_PLAIN_CONDITION_FR`) — ex.
    # Skaven « THE LURKING VERMINTIDE » affichait à la fois « DEPLOY » (brut,
    # non traduit, cf. absence d'équivalent à `_PLAIN_CONDITION_FR` ici) et
    # « PHASE DE DÉPLOIEMENT » côte à côte pour le même concept.
    is_deployment_condition = "deployment phase" in (ability.condition or "").lower()
    out = []
    for kw in ability.keywords.split(","):
        kw = kw.strip().upper()
        if not kw:
            continue
        if is_deployment_condition and kw.lower() in ("deploy", "deployment"):
            continue
        is_faction = kw.lower() in _FACTION_KEYWORDS
        bg = _BADGE_FACTION if is_faction else _BADGE_GOLD
        fg = "#f7e6ee" if is_faction else "#f7ecd6"
        out.append((_pill(kw, bg, fg), _pill_natural_width(kw)))
    return out


def _wielder_ratios(description: str) -> dict[str, str]:
    """`{nom d'arme (normalisé, minuscules) -> "N/M"}` à partir du texte
    libre de restriction du warscroll (ex. « 1/5 models can replace their
    Warhammer with a Grandhammer » -> {"grandhammer": "1/5"}). Même source
    que `engine/loadout.py` lit déjà côté moteur de combat."""
    text = re.sub(r"<[^>]+>", " ", description or "")
    out: dict[str, str] = {}
    for ratio, weapon in _WIELDER_RATIO_RE.findall(text):
        out[weapon.strip().lower()] = ratio
    return out


def _safe_paragraph(text: str, style: ParagraphStyle) -> Paragraph:
    """Comme `Paragraph(text, style)`, mais tolérant : `data/wahapedia/*.csv`
    est une donnée externe scrapée, parfois corrompue (ex. une balise HTML
    tronquée en plein milieu d'un champ, cf. `pdf_builder._safe_paragraph` —
    même pattern, dupliqué ici pour éviter un import circulaire avec
    `pdf_builder.py`) — on retombe sur le texte brut plutôt que de faire
    planter toute la génération pour une seule entrée abîmée."""
    try:
        return Paragraph(text, style)
    except Exception:
        stripped = re.sub(r"<[^>]*>", " ", text).replace("<", " ").replace(">", " ")
        return Paragraph(re.sub(r"\s+", " ", stripped).strip(), style)


def _clean_text(html: str) -> str:
    """Nettoyage minimal du HTML-ish Wahapedia pour `Paragraph` : `<a>`
    déballé, `<span class="kwb...">` -> `<b>`, listes -> puces, entités mal
    formées échappées. Même logique que `pdf_builder._clean_html` (pas
    dupliquée pour éviter toute divergence de rendu texte)."""
    from .pdf_builder import _clean_html
    return _clean_html(html)


# -- Styles --------------------------------------------------------------

#: fond de page du kit de tournoi (couvertures/cartes) — jaune pâle façon
#: parchemin, c'était le fond des cartes elles-mêmes avant que celles-ci ne
#: passent en blanc (cf. `_CARD_BG` ci-dessous) ; exporté (pas de préfixe
#: `_`) pour que `pdf_builder.py` en peigne le fond de chaque page.
PAGE_BG = colors.HexColor("#f8f2e3")
#: fond des cartes elles-mêmes — blanc plutôt que `PAGE_BG`, pour qu'une
#: carte se détache nettement du fond de page jaune pâle (demande explicite
#: de l'utilisateur : plus lisible que l'ancien parchemin sur parchemin).
_CARD_BG = colors.white
_STEEL_LINE = colors.HexColor("#c9bd9a")
_STEEL = colors.HexColor("#4a4536")
_INK = colors.HexColor("#14172a")

_NAME_STYLE = ParagraphStyle("wc_name", fontName="Helvetica", fontSize=9, leading=12, textColor=_INK)
_TEXT_STYLE = ParagraphStyle("wc_text", fontName="Helvetica", fontSize=8, leading=10.5, textColor=_STEEL, spaceBefore=1)
#: titres d'en-tête de carte — blancs sur le bandeau nuit (`#161a2b`) plutôt
#: que crème : demande explicite de l'utilisateur, plus lisible.
_HEAD_STYLE = ParagraphStyle("wc_head", fontName=CARD_TITLE_FONT, fontSize=13, leading=15, textColor=colors.white)
_ROLE_STYLE = ParagraphStyle("wc_role", fontName="Helvetica", fontSize=7, leading=9, textColor=colors.white)
_STAT_STYLE = ParagraphStyle("wc_stat", fontName="Helvetica", fontSize=6.5, leading=17, textColor=_STEEL, alignment=1)
_META_STYLE = ParagraphStyle("wc_meta", fontName="Helvetica", fontSize=7.5, leading=10, textColor=_STEEL)
_WHD_STYLE = ParagraphStyle("wc_whd", fontName="Helvetica", fontSize=6.5, leading=8, textColor=_STEEL, alignment=1)
_WNAME_STYLE = ParagraphStyle("wc_wname", fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=_INK)
_WTAG_STYLE = ParagraphStyle("wc_wtag", fontName="Helvetica-Oblique", fontSize=6.5, leading=8, textColor=_STEEL)
_WVAL_STYLE = ParagraphStyle("wc_wval", fontName="Helvetica", fontSize=7.5, leading=9, textColor=_INK, alignment=1)
_KW_STYLE = ParagraphStyle("wc_kw", fontName="Helvetica", fontSize=6, leading=8, textColor=_STEEL)
_PROV_STYLE = ParagraphStyle("wc_prov", fontName="Helvetica-Oblique", fontSize=6, leading=8, textColor=_STEEL, alignment=2)


def _pill(text: str, bg_hex: str, fg_hex: str, width: float | None = None, outline: bool = False) -> Table:
    """Une vraie pastille pleine — une mini-`Table` à une cellule avec un
    fond peint (`Paragraph` seul ne peint jamais de fond derrière son texte,
    même en HTML-ish reportlab) : c'est le même principe que `_phase_band`
    utilisait déjà pour son bandeau, appliqué à chaque badge individuel
    plutôt qu'à un texte coloré entre crochets. `width=None` laisse la
    pastille se tailler sur son contenu (badges courts : fréquence,
    qualificatif, mot-clé) ; un `width` fixe force le retour à la ligne
    (la réaction, seule à porter une phrase complète et potentiellement
    longue). `outline=True` — la réaction seule — garde un fond transparent
    et un liseré coloré plutôt qu'un aplat, pour rester l'exception qui
    attire l'œil comme une alerte plutôt qu'une classification de plus.

    `width` est toujours résolu à une valeur explicite avant de bâtir la
    `Table` (jamais `colWidths=[None]`) : un `Paragraph` compte comme un
    contenu "à largeur variable" pour reportlab, donc une colonne laissée
    `None` ne se taille pas sur son texte mais s'étire pour occuper toute la
    largeur disponible dans la cellule englobante (`_ability_row_flowables`
    empile plusieurs pastilles dans une même cellule alignée à droite) — la
    pastille perdait alors sa largeur naturelle et s'étalait sur toute la
    colonne, ce qui rendait l'alignement à droite invisible (toutes bord à
    bord) plutôt que de faire ressortir chaque pastille par sa propre
    largeur."""
    if width is None:
        width = _pill_natural_width(text)
    style = ParagraphStyle(
        f"wc_pill_{bg_hex}_{outline}", fontName="Helvetica", fontSize=6.6, leading=8.4,
        textColor=colors.HexColor(bg_hex if outline else fg_hex),
    )
    inner = _safe_paragraph(text, style)
    t = Table([[inner]], colWidths=[width])
    cell_style = [
        ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("ROUNDEDCORNERS", [_PILL_RADIUS] * 4),
    ]
    if outline:
        cell_style.append(("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor(bg_hex)))
    else:
        cell_style.append(("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(bg_hex)))
    t.setStyle(TableStyle(cell_style))
    return t


#: espace laissé entre deux pastilles d'une même ligne par `_pill_row`
#: (`RIGHTPADDING` ci-dessous) — repris tel quel par `_pack_badges` pour que
#: son budget de largeur par ligne corresponde exactement à ce que la ligne
#: assemblée occupera réellement.
_PILL_GAP = 4

#: espace vertical ajouté entre deux lignes de badges empilées par
#: `_pack_badges` (via `spaceBefore`, respecté par Platypus même quand le
#: contenu d'une cellule est une simple liste de Flowables plutôt qu'un
#: Frame — cf. le commentaire sur `_CastBadge.spaceBefore`) — un peu d'air
#: pour que les pastilles ne se touchent pas verticalement.
_BADGE_ROW_GAP = 2


def _pack_badges(items: list[tuple[Flowable, float]], max_width: float) -> list[Table]:
    """Empile des pastilles de badge de toute nature (sort/fréquence/
    condition/mot-clé) sur autant de lignes que nécessaire, plusieurs
    pastilles par ligne quand leur largeur cumulée tient dans `max_width` —
    remplace l'ancien traitement à deux vitesses (fréquence/condition
    empilées une par ligne dans la colonne de droite, mots-clés sur une
    ligne séparée pleine largeur en dessous) par une seule grille commune,
    pour que par ex. « MA PHASE » (condition) et « TRAITS DE BATAILLE »
    (mot-clé/origine) puissent partager la même ligne au lieu de toujours
    s'empiler chacune sur la sienne. Glouton, dans l'ordre reçu — jamais de
    réordonnancement, seulement des retours à la ligne."""
    rows: list[list[tuple[Flowable, float]]] = []
    row_widths: list[float] = []
    for fl, w in items:
        if rows and row_widths[-1] + _PILL_GAP + w <= max_width:
            rows[-1].append((fl, w))
            row_widths[-1] += _PILL_GAP + w
        else:
            rows.append([(fl, w)])
            row_widths.append(w)
    packed = [row for row in (_pill_row(r) for r in rows) if row is not None]
    for row in packed[1:]:
        row.spaceBefore = _BADGE_ROW_GAP
    return packed


def _pill_row(pills: list[tuple[Flowable, float]]) -> Table | None:
    """Plusieurs pastilles côte à côte (mots-clés d'aptitude, fréquence...) —
    une ligne à N colonnes, chacune taillée sur son contenu."""
    if not pills:
        return None
    # `colWidths` doit être donné explicitement (largeur déjà connue de
    # chaque pastille, cf. `_pill_natural_width`/`_CastBadge.size`) plutôt que
    # laissé à `None` ("auto") : reportlab ne sait calculer une largeur de
    # colonne "auto" qu'en interrogeant `Flowable._fixedWidth` de son contenu,
    # qui vaut 0 par défaut pour *toute* pastille (ce sont elles-mêmes des
    # `Table`/`Flowable` imbriquées) — jugée "non calculable rapidement",
    # reportlab bascule alors sur `_calcPreliminaryWidths`, qui étire la
    # colonne pour occuper toute la largeur disponible au lieu de la tailler
    # sur son contenu. Conséquence concrète : une fois cette ligne replacée
    # dans la cellule `cond_col` de `_ability_row_flowables`, sa largeur
    # mesurée valait `cond_col` pour *toutes* les lignes quel que soit leur
    # contenu réel, rendant l'alignement à droite (`ALIGN "RIGHT"` sur cette
    # cellule) indiscernable d'un alignement à gauche — repéré en comparant
    # les rects mesurés de plusieurs pastilles empilées (bords gauches
    # identiques, jamais les bords droits). Des `colWidths` explicites
    # évitent ce chemin de code entièrement.
    widths = [w + (_PILL_GAP if i < len(pills) - 1 else 0) for i, (_, w) in enumerate(pills)]
    t = Table([[fl for fl, _ in pills]], colWidths=widths)
    t.setStyle(TableStyle([
        # le petit espace entre 2 pastilles voisines est réservé dans `widths`
        # ci-dessus (colonnes 0..avant-dernière) puis rendu visible ici via
        # RIGHTPADDING sur ces mêmes colonnes — jamais sur la dernière, dont
        # le bord droit doit rester exactement au bord de la ligne (repère de
        # l'alignement à droite de `_ability_row_flowables`).
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-2, -1), _PILL_GAP),
        ("RIGHTPADDING", (-1, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (0, 0), (-1, -1), "LEFT"),
    ]))
    return t


class _CastBadge(Flowable):
    """Badge géométrique (cercle/losange/hexagone), valeur inscrite au
    centre — reprend le code visuel de l'éditeur BattleScribe/Warhammer Age
    of Sigmar: The App pour un coût de Sort/Prière/Point de Commandement/
    Dime de Sang (une forme par type, cf. `_CAST_BADGE_SHAPES`), plutôt que
    la pastille rectangulaire générique de `_pill` utilisée ici avant —
    celle-ci ne distinguait ces types que par leur couleur et un préfixe
    textuel ("SORT 5+"), quand l'original les distingue d'abord par leur
    silhouette. `_cast_pill` retombe sur `_pill` (silhouette rectangulaire)
    quand l'aptitude ne porte aucune valeur numérique à inscrire au centre —
    un simple sigle ("PC") n'a pas sa place dans une forme aussi petite."""

    def __init__(self, shape: str, text: str, bg_hex: str, fg_hex: str, size: float = 14):
        super().__init__()
        self.shape = shape
        self.text = text
        self.bg = colors.HexColor(bg_hex)
        self.fg = colors.HexColor(fg_hex)
        self.size = size
        self.spaceBefore = 2  # même respiration que le `TOPPADDING` des pastilles voisines dans la pile

    def wrap(self, availWidth, availHeight):
        return (self.size, self.size)

    def _path(self, cx: float, cy: float, r: float):
        p = self.canv.beginPath()
        if self.shape == "circle":
            p.circle(cx, cy, r)
        elif self.shape == "diamond":
            p.moveTo(cx, cy + r)
            p.lineTo(cx + r, cy)
            p.lineTo(cx, cy - r)
            p.lineTo(cx - r, cy)
            p.close()
        else:  # hexagone à sommet plat (2 côtés horizontaux) — le jeton PC de l'éditeur
            for i in range(6):
                angle = math.radians(60 * i)
                x, y = cx + r * math.cos(angle), cy + r * math.sin(angle)
                (p.moveTo if i == 0 else p.lineTo)(x, y)
            p.close()
        return p

    def draw(self):
        c = self.canv
        cx = cy = self.size / 2.0
        r = self.size / 2.0 - 0.4  # laisse la place au liseré sans le faire déborder du cadre alloué
        c.setFillColor(self.bg)
        c.setStrokeColor(_STEEL_LINE)
        c.setLineWidth(0.6)
        c.drawPath(self._path(cx, cy, r), fill=1, stroke=1)
        c.setFillColor(self.fg)
        c.setFont("Helvetica-Bold", 7.2)
        c.drawCentredString(cx, cy - 2.6, self.text)


#: taille du badge Sorcier/Prêtre en en-tête — plus grand que le badge de
#: coût d'une aptitude (`_CastBadge` par défaut, 14pt) : il n'est plus
#: accolé à un texte de règle qui porte lui-même l'info, il doit se
#: distinguer tout seul près du nom de l'unité, comme sur l'éditeur
#: BattleScribe/l'App.
_CASTER_BADGE_SIZE = 16


def _caster_badges(keywords: list[str]) -> list[_CastBadge]:
    """Badges géométriques Sorcier/Prêtre (même silhouette que `_CastBadge`,
    cercle violet pour un sort/un sorcier, losange vert pour une prière/un
    prêtre) construits à partir des mots-clés `WIZARD (N)`/`PRIEST (N)` du
    warscroll — le niveau de magie/de prière de l'unité, reconstitué par
    `WahapediaLookup.find_warscroll` à partir de la colonne `parameter` de
    Warscrolls_keywords.csv. Affichés dans l'en-tête de carte plutôt que dans
    la liste de mots-clés en bas (cf. `_visible_keywords`) : un joueur
    cherche ce niveau au même endroit que sur l'éditeur BattleScribe/l'App,
    près du nom de l'unité, pas noyé dans une liste de mots-clés."""
    badges = []
    for kw in keywords:
        m = _CASTER_KW_RE.match(kw.strip())
        if not m:
            continue
        kind, level = m.group(1).upper(), m.group(2)
        if kind == "WIZARD":
            badges.append(_CastBadge("circle", level, _BADGE_SPELL, _CAST_BADGE_FG["Spell"], size=_CASTER_BADGE_SIZE))
        else:
            badges.append(_CastBadge("diamond", level, _BADGE_PRAYER, _CAST_BADGE_FG["Prayer"], size=_CASTER_BADGE_SIZE))
    return badges


def _visible_keywords(keywords: list[str]) -> list[str]:
    """`keywords` moins `WIZARD (N)`/`PRIEST (N)` — ceux-ci rejoignent le
    badge d'en-tête (`_caster_badges`) plutôt que la liste de mots-clés en
    bas de carte, pour ne pas doublonner l'information."""
    return [kw for kw in keywords if not _CASTER_KW_RE.match(kw.strip())]


def _caster_badge_row(badges: list[_CastBadge]) -> tuple[Table, float]:
    """Aligne 1+ badges Sorcier/Prêtre côte à côte (une unité peut, en
    théorie, être à la fois Sorcier et Prêtre) avec un petit espace entre eux
    — même schéma `(flowable, largeur occupée)` que le reste du fichier
    utilise pour composer des lignes de badges (cf. `_pack_badges`)."""
    gap = 3
    cells: list = []
    col_widths: list[float] = []
    for i, b in enumerate(badges):
        if i:
            cells.append(Spacer(gap, 0))
            col_widths.append(gap)
        cells.append(b)
        col_widths.append(b.size)
    t = Table([cells], colWidths=col_widths)
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return t, sum(col_widths)


class _PhaseRail(Flowable):
    """Bandeau de phase vertical, texte pivoté — le rendu que la maquette
    HTML utilisait et que la première passe avait abandonné (bandeau
    horizontal) faute d'un moyen simple de connaître, par avance, la
    hauteur qu'un `Flowable` occupera une fois posé. En réalité rien
    n'empêche de la calculer nous-même : le corps du groupe (les lignes
    d'aptitude) est construit et mesuré via son propre `.wrap()` *avant*
    d'instancier ce bandeau (cf. `_append_ability_groups`), avec cette
    hauteur déjà connue passée ici en dur plutôt que redemandée à
    `wrap()` — ce `Flowable` n'a donc plus qu'à dessiner un rectangle
    plein et un texte pivoté à 90° dans un espace dont la taille est fixée
    d'avance, ce que `canvas.rotate()` fait très bien."""

    def __init__(self, label: str, bg_hex: str, fg_hex: str, height: float, width: float = 5.2 * mm):
        super().__init__()
        self.label = label
        self.bg = colors.HexColor(bg_hex)
        self.fg = colors.HexColor(fg_hex)
        self.width = width
        self.height = height

    def wrap(self, availWidth, availHeight):
        return (self.width, self.height)

    def draw(self):
        c = self.canv
        c.setFillColor(self.bg)
        c.rect(0, 0, self.width, self.height, fill=1, stroke=0)
        c.saveState()
        c.setFillColor(self.fg)
        c.translate(self.width / 2.0, self.height / 2.0)
        c.rotate(90)
        c.setFont("Helvetica-Bold", 6.6)
        c.drawCentredString(0, -2.3, self.label)
        c.restoreState()


def _rail_label_min_height(label: str) -> float:
    """Largeur réelle (mesurée, pas devinée) de `label` à la police/taille du
    bandeau, plus une marge — un bandeau pivoté à 90° (`_PhaseRail`, gros
    bandeau de phase comme sous-bandeau de catégorie) a besoin d'au moins
    cette hauteur pour ne pas se faire couper."""
    return stringWidth(label, "Helvetica-Bold", 6.6) + 8


def _min_rail_height(phase_key: str) -> float:
    return _rail_label_min_height(_PHASE_LABELS[phase_key].upper())


_NOTE_STYLE = ParagraphStyle("wc_note", fontName="Helvetica-Oblique", fontSize=6.5, leading=8.5, textColor=_STEEL)


_RAIL_WIDTH = 5.2 * mm

#: sous-bandeau de catégorie (Aptitudes/Sorts/Prières/Manifestations, cf.
#: `_ability_group_body`) — même principe que `_PhaseRail`/`_RAIL_WIDTH` mais
#: plus étroit, pour se lire comme une subdivision du grand bandeau de phase
#: plutôt qu'un bandeau de même rang.
_CATEGORY_RAIL_WIDTH = 4.2 * mm

#: (fond, texte) de chaque sous-bandeau de catégorie — mêmes couleurs que
#: leurs pastilles (`_CATEGORY_COLORS`/`_CAST_BADGE_FG`) pour rester
#: reconnaissable d'un coup d'œil (le violet d'un sort, le vert d'une
#: prière...), avec un texte clair choisi pour le contraste plutôt que
#: réutilisé tel quel.
_CATEGORY_RAIL_COLORS: dict[str, tuple[str, str]] = {
    "normal": ("#6b6555", "#f5f2ea"),
    "spell": (_BADGE_SPELL, _CAST_BADGE_FG["Spell"]),
    "prayer": (_BADGE_PRAYER, _CAST_BADGE_FG["Prayer"]),
    "manifestation": (_BADGE_STAT, "#e8f5f7"),
}


def _ability_row_flowables(ab: AbilityEntry, name_col: float, cond_col: float, first: bool) -> list[tuple[list, tuple]]:
    """Les 2 lignes d'une aptitude (nom+badges, texte), chacune comme
    `(cellules_de_ligne, style_supplémentaire_ou_None)` — `_ability_group_body`
    les assemble en lignes de la sous-table du groupe, en gardant le
    numérotage d'index à sa charge."""
    entries: list[tuple[list, tuple | None]] = []

    name_cell: list = [_safe_paragraph(f"<b>{ab.name}</b>", _NAME_STYLE)]

    # logo sort/prière/point de commandement, fréquence ("×1 / TOUR"),
    # condition (passif/qualificatif/réaction) et mots-clés (dont le badge
    # d'origine, cf. `tag_ability_origin`) rejoignent tous la même grille de
    # droite — une seule pastille par nature de badge n'existe pas : elles
    # sont toutes packées ensemble par `_pack_badges`, plusieurs par ligne
    # quand leur largeur le permet, plutôt que les badges "condition"
    # empilés un par ligne dans la colonne de droite et les mots-clés sur
    # une ligne séparée pleine largeur en dessous (deux traitements
    # différents qui ne s'alignaient jamais entre eux). Le logo avait
    # d'abord été mis à côté du nom (même traitement que la portée d'une
    # arme) mais, contrairement à un nom d'arme (toujours court), un nom
    # d'aptitude peut être long ("EXCOMMUNICATION!", "DERANGED
    # TRANSFORMATION") — sur une carte de règles à 2 colonnes
    # (`render_rule_card`), la colonne de nom rétrécie ne laissait alors
    # plus assez de place aux deux sur une ligne, et reportlab réenlignait
    # le badge en 2-3 lignes ("PRIÈRE 4+" -> "PRI"/"ÈRE"/"4+"). La colonne
    # de droite a une largeur fixe indépendante du nom, jamais ce conflit.
    badge_items: list[tuple[Flowable, float]] = []
    cast_pill = _cast_pill(ab, cond_col)
    if cast_pill is not None:
        badge_items.append(cast_pill)
    freq = _freq_pill(ab, cond_col)
    if freq is not None:
        badge_items.append(freq)
    cond_pill = _condition_pill(ab, cond_col)
    if cond_pill is not None:
        badge_items.append(cond_pill)
    badge_items.extend(_keyword_pills(ab))
    badge_cell: list = _pack_badges(badge_items, cond_col)
    # une seule colonne pour la table extérieure (cf. `_ability_group_body`)
    # : nom et badges de droite restent 2 colonnes côte à côte, mais
    # imbriqués dans une mini-table qui, elle, tient toute seule dans cette
    # cellule.
    name_cond = Table([[name_cell, badge_cell if badge_cell else ""]], colWidths=[name_col, cond_col])
    name_cond.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"), ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    entries.append(([name_cond], "top" if first else "top-rule"))

    entries.append(([_safe_paragraph(_clean_text(ab.description), _TEXT_STYLE)], "text"))
    return entries


def _ability_rows_body(abilities: list[AbilityEntry], width: float) -> Table:
    """Empile les lignes (nom+badges, texte) de chaque aptitude de
    `abilities`, sans aucun repère de catégorie — le corps brut qu'utilise
    directement `_ability_group_body` pour un groupe à une seule catégorie
    (l'écrasante majorité des cartes), et que cette même fonction réutilise
    une fois par grappe de catégorie pour un groupe qui en mélange plusieurs
    (cf. `_ability_group_body`)."""
    # les cellules de cette table portent 8pt de marge de chaque côté (style
    # ci-dessous) : le contenu de chaque ligne — notamment la mini-table
    # nom+condition, dont la largeur est fixée d'avance — doit se caler sur
    # `width` *moins* cette marge, sans quoi elle déborde du cadre de la
    # carte (elle-même dimensionnée exactement à `width`).
    content_width = width - 16
    name_col = content_width * 0.56
    cond_col = content_width - name_col
    rows: list[list] = []
    styles: list[tuple] = [
        ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]
    for i, ab in enumerate(abilities):
        for cells, kind in _ability_row_flowables(ab, name_col, cond_col, first=(i == 0)):
            rows.append(cells)
            r = len(rows) - 1
            if kind == "top" or kind == "top-rule":
                styles += [("TOPPADDING", (0, r), (-1, r), 5), ("BOTTOMPADDING", (0, r), (-1, r), 1)]
                if kind == "top-rule":
                    styles.append(("LINEABOVE", (0, r), (-1, r), 0.4, _STEEL_LINE))
            else:  # text
                styles += [("TOPPADDING", (0, r), (-1, r), 2), ("BOTTOMPADDING", (0, r), (-1, r), 6)]
    body = Table(rows, colWidths=[width])
    # une seule colonne pour la table extérieure : la 1re ligne (nom+condition)
    # a en réalité 2 "colonnes" logiques (nom, condition) mais elles sont déjà
    # fusionnées dans une cellule de liste + un flowable pilule, donc `rows`
    # reste à 1 colonne partout — SPAN inutile.
    body.setStyle(TableStyle(styles))
    return body


def _category_cluster_row(category: str, abilities: list[AbilityEntry], width: float) -> Table:
    """Une grappe d'aptitudes de même catégorie, accolée à son propre
    sous-bandeau vertical (même principe que `_PhaseRail`, mais plus étroit
    et coloré par catégorie plutôt que par phase) — remplace l'ancien
    intitulé de catégorie posé en ligne au-dessus de la grappe (« APTITUDES »/
    « SORTS »/« PRIÈRES » en petit texte), qui ne se lisait pas comme
    appartenant au même bloc que le nom+les badges de la 1re aptitude."""
    body_width = width - _CATEGORY_RAIL_WIDTH
    body = _ability_rows_body(abilities, body_width)
    _, body_height = body.wrap(body_width, 0xFFFF)
    rail_height = max(body_height, _rail_label_min_height(_CATEGORY_LABELS_FR.get(category, category).upper()))
    bg, fg = _CATEGORY_RAIL_COLORS.get(category, _CATEGORY_RAIL_COLORS["normal"])
    rail = _PhaseRail(_CATEGORY_LABELS_FR.get(category, category).upper(), bg, fg, rail_height, width=_CATEGORY_RAIL_WIDTH)
    row = Table([[rail, body]], colWidths=[_CATEGORY_RAIL_WIDTH, body_width])
    row.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return row


def _category_clusters(group: list[AbilityEntry]) -> list[tuple[str, list[AbilityEntry]]]:
    """Découpe `group` en grappes consécutives de même catégorie (`(catégorie,
    aptitudes)`) — partagé par `_ability_group_body` (pour poser un
    sous-bandeau par grappe) et `_chunk_group` (pour ne jamais couper une
    grappe entre deux pages/tronçons, cf. `_chunk_group`). `group` est supposé
    déjà trié par catégorie (cf. `_append_ability_groups`), jamais réordonné
    ici."""
    clusters: list[tuple[str, list[AbilityEntry]]] = []
    for ab in group:
        category = _ability_category(ab)
        if clusters and clusters[-1][0] == category:
            clusters[-1][1].append(ab)
        else:
            clusters.append((category, [ab]))
    return clusters


def _ability_group_body(group: list[AbilityEntry], width: float, show_category_headers: bool = False) -> Table:
    """La sous-table d'un groupe de phase (tout sauf le bandeau de phase
    lui-même) — isolée dans sa propre `Table` pour pouvoir mesurer sa hauteur
    réelle avant de construire le bandeau vertical à sa gauche, cf.
    `_append_ability_groups`. `show_category_headers` (calculé une fois pour
    tout le groupe de phase, avant tronçonnage/mise en colonnes, cf.
    `_append_ability_groups`) découpe le groupe en grappes consécutives de
    même catégorie (`_category_clusters`), chacune accolée à son propre
    sous-bandeau (cf. `_category_cluster_row`) — seulement utile quand le
    groupe mélange effectivement plusieurs catégories (ex. un sort et un
    trait de bataille tous deux en phase des héros)."""
    if not show_category_headers:
        return _ability_rows_body(group, width)
    clusters = _category_clusters(group)
    rows: list[list] = []
    styles: list[tuple] = [
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0), ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]
    for i, (category, abilities) in enumerate(clusters):
        rows.append([_category_cluster_row(category, abilities, width)])
        # pas de TOPPADDING ici : ce padding pousserait vers le bas la ligne
        # entière (sous-bandeau de catégorie inclus, pas seulement le texte),
        # ouvrant un blanc visible entre deux sous-bandeaux de couleurs
        # différentes (ex. le gris "APTITUDES" et le violet "SORTS") — ils
        # doivent au contraire se toucher, seul le `LINEABOVE` marque la
        # frontière entre grappes.
        if i > 0:
            styles.append(("LINEABOVE", (0, i), (-1, i), 0.4, _STEEL_LINE))
    body = Table(rows, colWidths=[width])
    body.setStyle(TableStyle(styles))
    return body


#: hauteur maximale d'un seul groupe de phase (bandeau + corps) — une seule
#: ligne de la table extérieure de la carte, donc une seule ligne du PDF
#: final : reportlab ne sait pas la couper à un saut de page. Un groupe
#: normal (une carte d'unité, une seule catégorie de règle) ne l'atteint
#: jamais ; seule une carte de règles *fusionnées* (plusieurs catégories
#: réunies dans la même phase, cf. `pdf_builder._resolve_rules`) le peut —
#: `_chunk_group` le fractionne alors en plusieurs segments qui reprennent
#: chacun le même bandeau (couleur + nom de phase), l'un sous l'autre,
#: plutôt que de tenter une seule ligne trop grande pour tenir sur une page.
#: Marge sous la hauteur utile d'une page A4 portrait avec les marges de
#: `pdf_builder._build_rule_cards_pdf`/`_build_warscroll_cards_pdf` (~11mm).
_MAX_GROUP_HEIGHT = 240 * mm

#: hauteur utile d'une page A4 portrait avec les marges de
#: `pdf_builder._build_warscroll_cards_pdf` (~5.5mm de chaque côté), moins la
#: marge de sécurité empirique entre `A4[1] - 2*marge` et la hauteur de cadre
#: réellement disponible que reportlab rapporte dans une `LayoutError` (le
#: padding interne par défaut d'un `Frame`, ~6pt de chaque côté). Sert de
#: seuil pour `build_warscroll_cards_flow` : une carte pairée à demi-largeur
#: (`_UNIT_CARD_WIDTH`) dont une aptitude est exceptionnellement longue (ex.
#: Skaven's Lord Skreech Verminking, "Le Rat aux Treize Têtes") peut dépasser
#: une page entière et faire échouer tout le PDF avec un
#: `reportlab.platypus.doctemplate.LayoutError` — jamais le cas en dessous de
#: ce seuil.
_MAX_CARD_HEIGHT = A4[1] - 2 * (5.5 * mm) - 20


def _chunk_group(
    group: list[AbilityEntry], body_width: float, show_category_headers: bool = False,
) -> list[list[AbilityEntry]]:
    """Découpe `group` en tronçons dont le corps assemblé (cf.
    `_ability_group_body`) tient sous `_MAX_GROUP_HEIGHT` — jamais une
    aptitude coupée en deux, seulement la frontière entre deux aptitudes
    consécutives. Une aptitude seule plus haute que la limite (texte de
    règle exceptionnellement long) reste seule dans son propre tronçon,
    trop grande malgré tout plutôt que tronquée. `show_category_headers` doit
    être le même que celui passé au rendu final (cf. `_append_ability_groups`)
    pour que la hauteur mesurée ici — qui doit rester un majorant sûr sous
    `_MAX_GROUP_HEIGHT` — ne sous-estime pas les intitulés de catégorie
    effectivement rendus.

    Quand `show_category_headers` est vrai, la coupe se fait au niveau de la
    grappe de catégorie (`_category_clusters`), pas de l'aptitude individuelle
    — une grappe (ex. les 3 aptitudes "Sorts" d'un même bandeau de phase) ne
    peut donc jamais se retrouver scindée en deux tronçons. Sans cette
    contrainte, une coupe pouvait tomber entre deux aptitudes de la *même*
    catégorie : chaque tronçon obtenait alors son propre sous-bandeau
    (`_category_cluster_row`), correctement dimensionné sur sa portion
    tronquée mais donc plus court que la grappe complète visible une fois les
    deux tronçons empilés sans saut de page entre eux (symptôme : le
    sous-bandeau "Sorts" ne couvrant pas toute la hauteur de ses 3 aptitudes)
    — et, si les deux tronçons tombaient de part et d'autre d'un saut de page,
    la grappe se retrouvait visuellement coupée en plein milieu. Une grappe
    entière plus haute que la limite (cas extrême, jamais vu en pratique tant
    les grappes restent petites) reste malgré tout seule dans son propre
    tronçon, comme une aptitude isolée trop longue — pas de repli plus fin sur
    un découpage par aptitude à l'intérieur de la grappe."""
    units = [abilities for _category, abilities in _category_clusters(group)] if show_category_headers else [[ab] for ab in group]
    chunks: list[list[AbilityEntry]] = []
    current: list[AbilityEntry] = []
    for unit in units:
        candidate = current + unit
        _, h = _ability_group_body(candidate, body_width, show_category_headers).wrap(body_width, 0xFFFF)
        if h > _MAX_GROUP_HEIGHT and current:
            chunks.append(current)
            current = list(unit)
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


#: Espace entre les deux colonnes d'un groupe de phase sur la carte de règles
#: combinée (cf. `_ability_group_body_columns`) — assez pour rester lisible
#: comme un vrai intervalle plutôt qu'un simple accolement des cadres.
_COLUMN_GAP = 4 * mm


def _split_group_columns(group: list[AbilityEntry], col_width: float, n_cols: int) -> list[list[AbilityEntry]]:
    """Répartit `group` (dans l'ordre, jamais réordonné) en `n_cols` colonnes
    équilibrées par hauteur rendue à `col_width` — pas par nombre
    d'aptitudes, une aptitude au texte long ne doit pas peser autant qu'une
    courte. Choisit, pour chaque frontière entre 2 colonnes, l'index qui
    rapproche le plus la hauteur cumulée de sa part du total (`i/n_cols`) —
    pas un seuil glouton "colonne courante pleine, passe à la suivante" :
    celui-ci pouvait faire déborder toutes les aptitudes dans la première
    colonne dès que la dernière pesait à elle seule plus que la moitié du
    total (ex. 2 aptitudes, la 2e nettement plus longue que la 1re : la
    hauteur cumulée après la 1re restait sous la cible, donc la 2e
    rejoignait quand même la colonne 1 au lieu de basculer en colonne 2).
    Jamais plus de colonnes que d'aptitudes ; un groupe à une seule aptitude
    reste seul en colonne 1, les suivantes vides."""
    columns: list[list[AbilityEntry]] = [[] for _ in range(n_cols)]
    if not group:
        return columns
    # jamais plus de colonnes "actives" que d'aptitudes — les colonnes en
    # trop restent vides (`columns` garde `n_cols` éléments, la forme que
    # `_ability_group_body_columns` attend pour zipper avec `col_widths`).
    active_cols = max(1, min(n_cols, len(group)))
    if active_cols <= 1:
        columns[0] = list(group)
        return columns
    # mesurée sans intitulé de catégorie (même si le groupe en affichera) :
    # cette hauteur ne sert qu'à équilibrer les colonnes par proportion, pas
    # de garde-fou à respecter au pt près comme `_chunk_group` — l'écart
    # (quelques pt par frontière de catégorie, répartis sur tout le groupe)
    # est négligeable pour cet usage.
    heights = [_ability_group_body([ab], col_width).wrap(col_width, 0xFFFF)[1] for ab in group]
    cumulative = [0.0]
    for h in heights:
        cumulative.append(cumulative[-1] + h)
    total = cumulative[-1]
    n = len(group)
    boundaries = [0]
    for i in range(1, active_cols):
        target = total * i / active_cols
        lo = boundaries[-1] + 1  # au moins 1 aptitude dans la colonne précédente
        hi = n - (active_cols - i)  # au moins 1 aptitude par colonne restante
        best_idx = min(range(lo, hi + 1), key=lambda idx: abs(cumulative[idx] - target))
        boundaries.append(best_idx)
    boundaries.append(n)
    for i in range(active_cols):
        columns[i] = group[boundaries[i]:boundaries[i + 1]]
    return columns


def _ability_text_chunks(text: str) -> list[str]:
    """Découpe `text` (déjà passé par `_clean_text`) en blocs au niveau de ses
    `<br/>` de premier niveau — jamais à l'intérieur d'une liste `<ul>...
    </ul>` (profondeur suivie), pour ne jamais couper une balise en 2. Sert
    de points de coupe sûrs à `_split_long_ability_columns` pour répartir une
    aptitude trop longue sur plusieurs colonnes."""
    depth = 0
    chunks: list[str] = []
    buf: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        if text.startswith("<ul>", i):
            depth += 1
            buf.append("<ul>")
            i += 4
        elif text.startswith("</ul>", i):
            depth -= 1
            buf.append("</ul>")
            i += 5
        elif depth == 0 and text.startswith("<br/>", i):
            piece = "".join(buf).strip()
            if piece:
                chunks.append(piece)
            buf = []
            i += 5
        else:
            buf.append(text[i])
            i += 1
    tail = "".join(buf).strip()
    if tail:
        chunks.append(tail)
    return chunks


#: Au-delà de ce volume de texte (caractères de la description, une seule
#: aptitude), une aptitude seule dans son bandeau de phase bénéficie d'une
#: mise en page à colonnes dédiée (`_split_long_ability_columns`) plutôt que
#: de tomber en repli pleine-largeur (`_ability_group_body_columns`) —
#: demande explicite de l'utilisateur : une aptitude au texte long doit
#: rester à sa place chronologique normale (pas de section/page dédiée) mais
#: profiter des mêmes colonnes que le reste de la carte. Calibré sur
#: `data/faction_rules_fr.json` : l'aptitude la plus longue observée
#: (« Inscription de Rune », Lumineth Realm-lords, ~3470 caractères) le
#: dépasse largement, la suivante (« Éruption de Fureur », règle de saison
#: partagée par plusieurs factions, ~1281 caractères) reste confortablement
#: en-dessous.
_LONG_ABILITY_THRESHOLD = 2000


def _split_long_ability_columns(ab: AbilityEntry, body_width: float, n_cols: int) -> Table | None:
    """Répartit le corps d'une seule aptitude longue sur `n_cols` colonnes
    côte à côte — nom+badges en tête de la 1re colonne seulement, texte
    scindé au niveau de ses coupures `<br/>` de premier niveau
    (`_ability_text_chunks`), équilibré par hauteur rendue comme
    `_split_group_columns` mais entre morceaux d'une même aptitude plutôt
    qu'entre aptitudes voisines. `None` si le texte n'a pas assez de
    coupures de premier niveau pour remplir `n_cols` colonnes — l'appelant
    retombe alors sur le rendu pleine-largeur habituel plutôt que de risquer
    une colonne vide ou coupée au mauvais endroit."""
    text = _clean_text(ab.description)
    chunks = _ability_text_chunks(text)
    if len(chunks) < n_cols:
        return None
    col_width = (body_width - _COLUMN_GAP * (n_cols - 1)) / n_cols
    content_width = col_width - 16
    heights = [_safe_paragraph(c, _TEXT_STYLE).wrap(content_width, 0xFFFF)[1] for c in chunks]
    cumulative = [0.0]
    for h in heights:
        cumulative.append(cumulative[-1] + h)
    total = cumulative[-1]
    n = len(chunks)
    boundaries = [0]
    for i in range(1, n_cols):
        target = total * i / n_cols
        lo = boundaries[-1] + 1
        hi = n - (n_cols - i)
        best_idx = min(range(lo, hi + 1), key=lambda idx: abs(cumulative[idx] - target))
        boundaries.append(best_idx)
    boundaries.append(n)

    name_col = content_width * 0.56
    cond_col = content_width - name_col
    header_cells, _kind = _ability_row_flowables(ab, name_col, cond_col, first=True)[0]

    cells: list = []
    col_widths: list[float] = []
    for i in range(n_cols):
        seg_text = "<br/><br/>".join(chunks[boundaries[i]:boundaries[i + 1]])
        seg_rows: list[list] = []
        seg_styles: list[tuple] = [
            ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]
        if i == 0:
            seg_rows.append(header_cells)
            seg_styles += [("TOPPADDING", (0, 0), (-1, 0), 5), ("BOTTOMPADDING", (0, 0), (-1, 0), 1)]
            text_row = 1
        else:
            text_row = 0
        seg_rows.append([_safe_paragraph(seg_text, _TEXT_STYLE)])
        seg_styles += [
            ("TOPPADDING", (0, text_row), (-1, text_row), 2 if i == 0 else 5),
            ("BOTTOMPADDING", (0, text_row), (-1, text_row), 6),
        ]
        seg_table = Table(seg_rows, colWidths=[col_width])
        seg_table.setStyle(TableStyle(seg_styles))
        cells.append(seg_table)
        col_widths.append(col_width)
        if i < n_cols - 1:
            cells.append(Spacer(_COLUMN_GAP, 0))
            col_widths.append(_COLUMN_GAP)
    t = Table([cells], colWidths=col_widths)
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return t


def _ability_group_body_columns(
    chunk: list[AbilityEntry], body_width: float, n_cols: int, show_category_headers: bool = False,
) -> Table:
    """Comme `_ability_group_body`, mais réparti sur `n_cols` colonnes côte à
    côte plutôt qu'empilé dans une seule — la carte de règles fusionnée
    (`render_rule_card`) peut réunir jusqu'à une dizaine d'aptitudes dans le
    même bandeau de phase (ex. tous les Traits Héroïques d'une faction) ;
    les étaler sur 2 colonnes exploite la largeur, plus généreuse que celle
    d'une carte d'unité, au lieu d'une longue colonne unique. `n_cols=1`
    retombe exactement sur `_ability_group_body`. `show_category_headers` est
    propagé tel quel à chaque colonne plutôt que recalculé par colonne : une
    catégorie qui déborde d'une colonne à l'autre doit répéter son intitulé
    en haut de la colonne suivante, comme un en-tête de tableau qui se répète
    à chaque page/colonne, pour rester lisible sans remonter à la colonne
    précédente. Réduit d'abord `n_cols` au nombre d'aptitudes du tronçon
    (`_split_group_columns` ne remplit de toute façon jamais plus de colonnes
    « actives » que ça) : sans ça, un tronçon plus court que `n_cols` (ex. un
    unique trait de bataille, particulièrement long) restait confiné dans une
    seule colonne à *moitié* de `body_width`, la ou les colonnes voisines
    restant vides — un gâchis de largeur qui aggrave le texte long au lieu de
    l'aider. Une exception : une aptitude dont le texte dépasse
    `_LONG_ABILITY_THRESHOLD` n'entre jamais dans ce partage par aptitude
    entière (que ce tronçon en compte une seule ou plusieurs) — déléguée à
    `_ability_group_body_columns_mixed`, elle obtient sa propre bande pleine
    largeur répartie sur ses colonnes (`_split_long_ability_columns`,
    nom+badges dans la 1re colonne, texte réparti sur les suivantes) plutôt
    que de monopoliser toute une colonne face à une aptitude courte voisine
    qui, elle, n'a rien à gagner à être étalée."""
    if n_cols > 1 and any(_is_long_ability(ab) for ab in chunk):
        return _ability_group_body_columns_mixed(chunk, body_width, n_cols, show_category_headers)
    n_cols = max(1, min(n_cols, len(chunk))) if chunk else n_cols
    if n_cols <= 1:
        return _ability_group_body(chunk, body_width, show_category_headers)
    col_width = (body_width - _COLUMN_GAP * (n_cols - 1)) / n_cols
    columns = _split_group_columns(chunk, col_width, n_cols)
    cells: list = []
    col_widths: list[float] = []
    for i, col in enumerate(columns):
        cells.append(_ability_group_body(col, col_width, show_category_headers) if col else Spacer(col_width, 0))
        col_widths.append(col_width)
        if i < n_cols - 1:
            cells.append(Spacer(_COLUMN_GAP, 0))
            col_widths.append(_COLUMN_GAP)
    t = Table([cells], colWidths=col_widths)
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return t


def _is_long_ability(ab: AbilityEntry) -> bool:
    return len(_clean_text(ab.description)) > _LONG_ABILITY_THRESHOLD


def _ability_group_body_columns_mixed(
    chunk: list[AbilityEntry], body_width: float, n_cols: int, show_category_headers: bool,
) -> Table:
    """Repli de `_ability_group_body_columns` pour un tronçon qui mélange au
    moins une aptitude longue (cf. `_LONG_ABILITY_THRESHOLD`) avec d'autres
    aptitudes — découpe `chunk` en tronçons consécutifs (une aptitude longue
    toujours seule dans le sien, plusieurs aptitudes courtes regroupées dans
    le leur), empilés dans l'ordre d'origine plutôt que réordonnés. Un
    tronçon "longue" est rendu par `_split_long_ability_columns` (ses
    propres colonnes) ; un tronçon "courtes" repasse par
    `_ability_group_body_columns` (jamais d'aptitude longue dedans, donc
    jamais de récursion vers cette fonction) pour garder le même partage par
    hauteur qu'un bandeau sans aptitude longue. Sans ce découpage,
    `_split_group_columns` traiterait la longue comme une aptitude entière
    parmi d'autres et lui donnerait une colonne entière pour elle seule, face
    à une aptitude courte livrée à elle-même dans l'autre — la longue reste
    cramponnée à la largeur d'une seule colonne au lieu de profiter des deux
    (demande explicite de l'utilisateur)."""
    runs: list[list[AbilityEntry]] = []
    for ab in chunk:
        if _is_long_ability(ab) or not runs or _is_long_ability(runs[-1][0]):
            runs.append([ab])
        else:
            runs[-1].append(ab)

    rows: list[list] = []
    styles: list[tuple] = [
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]
    for i, run in enumerate(runs):
        if len(run) == 1 and _is_long_ability(run[0]):
            body = _split_long_ability_columns(run[0], body_width, n_cols)
            if body is None:
                body = _ability_group_body(run, body_width, show_category_headers)
        else:
            body = _ability_group_body_columns(run, body_width, n_cols, show_category_headers)
        rows.append([body])
        if i > 0:
            styles.append(("LINEABOVE", (0, i), (-1, i), 0.4, _STEEL_LINE))
    t = Table(rows, colWidths=[body_width])
    t.setStyle(TableStyle(styles))
    return t


def _append_ability_groups(
    rows: list[list], styles: list[tuple], abilities: list[AbilityEntry], width: float, columns: int = 1,
) -> None:
    """Ajoute au corps de carte (unité ou règle) un groupe par bandeau de
    phase, dans l'ordre canonique du tour — partagé par `render_warscroll_card`
    et `render_rule_card` pour ne garder qu'une seule implémentation du
    tableau d'aptitudes. Bandeau vertical (`_PhaseRail`) à gauche du groupe,
    sa hauteur mesurée sur le corps du groupe avant de le construire.
    `columns` (>1 seulement pour `render_rule_card`, cf.
    `_ability_group_body_columns`) répartit chaque groupe de phase sur
    plusieurs colonnes côte à côte plutôt qu'une seule colonne empilée.

    Au sein d'un même bandeau de phase, les aptitudes sont triées par
    catégorie (`_CATEGORY_ORDER` : normales, sorts, prières, manifestations —
    tri stable, jamais réordonnées à l'intérieur d'une même catégorie) plutôt
    que laissées dans l'ordre de `abilities` — sans quoi, ex., un sort et un
    trait de bataille qui se déclenchent tous deux en phase des héros
    resteraient entremêlés dans cette phase plutôt que regroupés par type. Un
    intitulé de catégorie (cf. `_category_header`) n'est affiché que si la
    phase mélange effectivement plusieurs catégories — une carte d'unité sans
    sort/prière, l'écrasante majorité des cas, ne montre donc jamais
    "Aptitudes" en tête de sa phase des héros."""
    grouped: dict[str, list[AbilityEntry]] = {}
    for ab in abilities:
        grouped.setdefault(_classify_phase(ab), []).append(ab)

    body_width = width - _RAIL_WIDTH
    for key in _PHASE_ORDER:
        group = grouped.get(key)
        if not group:
            continue
        group = sorted(group, key=lambda ab: _CATEGORY_ORDER.index(_ability_category(ab)))
        show_headers = len({_ability_category(ab) for ab in group}) > 1
        bg, fg = _PHASE_COLORS[key]
        # le découpage page-safe (`_chunk_group`) reste mesuré à 1 colonne :
        # un tronçon qui tient à 1 colonne tient nécessairement à plusieurs
        # (chaque colonne en reçoit moins et devient donc moins haute), donc
        # jamais moins sûr, seulement plus conservateur dans de rares cas.
        chunks = _chunk_group(group, body_width, show_headers)
        for chunk_i, chunk in enumerate(chunks):
            body = _ability_group_body_columns(chunk, body_width, columns, show_headers)
            _, body_height = body.wrap(body_width, 0xFFFF)
            # un groupe très court (une seule aptitude sans texte long) peut
            # être plus bas que ce qu'il faut pour loger le nom de la phase
            # pivoté à 90° — sans plancher, le texte déborde du bandeau et se
            # fait recouvrir par la ligne suivante. `_min_rail_height` mesure
            # la largeur réelle du libellé le plus long à cette police/taille
            # plutôt que de deviner une marge.
            rail_height = max(body_height, _min_rail_height(key))
            rail = _PhaseRail(_PHASE_LABELS[key].upper(), bg, fg, height=rail_height, width=_RAIL_WIDTH)

            group_row = Table([[rail, body]], colWidths=[_RAIL_WIDTH, body_width])
            group_row.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]))
            # Un tronçon de phase (déjà garanti tenir sous `_MAX_GROUP_HEIGHT`,
            # donc sous une page pleine, cf. `_chunk_group`) est une ligne à
            # part entière de la table extérieure (`rows`) : `Table.split()`
            # ne coupe jamais une ligne en deux, seulement entre deux lignes —
            # ce tronçon ne peut donc déjà pas se retrouver coupé au milieu de
            # ses aptitudes à un saut de page, il part entier sur la page
            # suivante s'il ne rentre pas dans l'espace restant (`KeepTogether`
            # a été essayé ici pour le rendre plus explicite, mais échoue :
            # imbriqué dans une cellule de `Table`, `KeepTogether.wrap()`
            # renvoie une hauteur sentinelle énorme que la table extérieure
            # interprète comme une ligne à dimensionner en conséquence —
            # `reportlab.platypus.doctemplate.LayoutError` dès qu'un tronçon
            # atterrit en page 2+. `KeepTogether` ne fonctionne qu'au niveau
            # du flux de document (`story`), jamais imbriqué dans une cellule).
            rows.append([group_row])
            r = len(rows) - 1
            styles += [
                ("LEFTPADDING", (0, r), (-1, r), 0), ("RIGHTPADDING", (0, r), (-1, r), 0),
                ("TOPPADDING", (0, r), (-1, r), 0), ("BOTTOMPADDING", (0, r), (-1, r), 0),
            ]
            if chunk_i == len(chunks) - 1:
                styles.append(("LINEBELOW", (0, r), (-1, r), 0.6, _STEEL_LINE))


def _keyword_key(kw: str) -> str:
    # ignore la casse et un simple "s" de pluriel — une aptitude "Ensorcelled
    # Banners" (StD) porte déjà "Ensorcelled Banner" (singulier) dans son
    # propre `keywords` Wahapedia ; sans ce rapprochement, l'étiquetage
    # d'origine ajoutait un second badge quasi identique à côté du premier.
    return kw.strip().lower().rstrip("s")


def tag_ability_origin(abilities: list[AbilityEntry], origin_label: str) -> list[AbilityEntry]:
    """Ajoute `origin_label` (« Traits de Bataille », « Formation »...) au
    champ `keywords` de chaque aptitude — il en ressort comme un badge doré
    de plus à côté des mots-clés d'aptitude déjà présents, cf. `_name_line`/
    `_ability_row_flowables`. Un badge de carte aurait disparu si les
    aptitudes de plusieurs catégories se retrouvent réunies sur une seule
    carte (cf. `render_rule_card`) ou rejoignent la carte d'un héros ; un
    badge d'aptitude, lui, survit au déplacement. N'ajoute rien si un
    mot-clé quasi identique (cf. `_keyword_key`) figure déjà — une aptitude
    dont Wahapedia porte déjà le nom de catégorie en mot-clé ne doit pas
    aussi le recevoir en badge d'origine, sous peine de deux badges
    redondants côte à côte."""
    target = _keyword_key(origin_label)
    result = []
    for ab in abilities:
        existing = [kw.strip() for kw in ab.keywords.split(",") if kw.strip()] if ab.keywords else []
        if any(_keyword_key(kw) == target for kw in existing):
            result.append(ab)
            continue
        result.append(_dc_replace(ab, keywords=(ab.keywords + "," + origin_label) if ab.keywords else origin_label))
    return result


#: en-deçà de ce volume de texte cumulé (caractères des descriptions, tous
#: bandeaux de phase confondus), une carte de règles fusionnée tient
#: confortablement sur une seule colonne — l'étaler sur 2 colonnes n'aidait
#: alors qu'à rétrécir chaque bandeau sans rien gagner en compacité (ex. une
#: Armée de Renom sans Formation propre, ou une faction dont seuls 2-3
#: Traits de Bataille courts sont couverts). Au-delà, la carte réunit assez
#: de contenu (Traits de Bataille + Formation + Traits Héroïques/Artefacts +
#: domaines...) pour qu'un bandeau de phase chargé (ex. tous les Traits
#: Héroïques) bénéficie vraiment des 2 colonnes — cas de figure le plus
#: courant en pratique, une faction pleinement curée dépassant largement ce
#: seuil (généralement >15000 caractères).
_RULE_CARD_TWO_COLUMN_THRESHOLD = 2000


def _rule_card_columns(abilities: list[AbilityEntry]) -> int:
    total_chars = sum(len(_clean_text(ab.description)) for ab in abilities)
    return 2 if total_chars > _RULE_CARD_TWO_COLUMN_THRESHOLD else 1


def render_rule_card(title: str, abilities: list[AbilityEntry], width: float = 88 * mm, subtitle: str | None = None) -> Flowable | None:
    """Carte de règle — même grammaire visuelle que `render_warscroll_card`
    mais sans bandeau de stats ni armes, ces cartes ne sont pas des unités.
    `abilities` est déjà étiqueté par catégorie (`tag_ability_origin`) côté
    appelant, avant d'être éventuellement fusionné avec d'autres catégories
    sur une seule carte triée par phase (cf. `pdf_builder._resolve_rules`) —
    ce n'est plus la responsabilité de cette fonction de le faire.  `None`
    si `abilities` est vide (rien à afficher)."""
    if not abilities:
        return None
    rows: list[list] = []
    styles: list[tuple] = []

    header_cell = [Paragraph(title, _HEAD_STYLE)]
    if subtitle:
        header_cell.append(Paragraph(subtitle, _ROLE_STYLE))
    rows.append([header_cell])
    styles.append(("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#161a2b")))
    styles.append(("TOPPADDING", (0, 0), (-1, 0), 5))
    styles.append(("BOTTOMPADDING", (0, 0), (-1, 0), 5))
    styles.append(("LEFTPADDING", (0, 0), (-1, 0), 8))

    # jusqu'à 2 colonnes par bandeau de phase (cf. `_rule_card_columns`) :
    # cette carte réunit plusieurs catégories (Traits de Bataille,
    # Formation, Traits Héroïques...) triées ensemble par phase, donc un
    # bandeau peut compter beaucoup d'aptitudes — sa largeur (130mm, contre
    # 88mm pour une carte d'unité) s'y prête mieux qu'une longue colonne
    # unique, mais seulement si le contenu total le justifie.
    _append_ability_groups(rows, styles, abilities, width, columns=_rule_card_columns(abilities))

    card = Table(rows, colWidths=[width])
    card.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.8, _STEEL_LINE),
        ("BACKGROUND", (0, 0), (-1, -1), _CARD_BG),
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        *styles,
    ]))
    return card


#: Marge de la cellule qui contient le tableau d'armes — utilisée à la fois
#: pour dimensionner `col_widths` (cf. `content_width` ci-dessous) et pour
#: poser le style de padding de cette cellule, afin que les deux ne puissent
#: pas diverger de nouveau.
_WEAPON_ROW_LEFT_PAD = 8
_WEAPON_ROW_RIGHT_PAD = 6


def render_warscroll_card(ws: WarscrollData, width: float = 88 * mm, regiment_note: str | None = None) -> Flowable:
    """Construit la carte d'une unité en un seul `Flowable` composite (table
    imbriquée) : bandeau nom/rôle, stats, armes, aptitudes groupées par
    bandeau de phase (ordre canonique du tour), mots-clés. Verbatim anglais,
    aucune page de battletome copiée."""
    rows: list[list] = []
    styles: list[tuple] = []

    # Pas de sous-titre de rôle ("INFANTRY", "INFANTRY HERO"...) sous le nom :
    # `ws.role` ne fait que redire un mot-clé déjà affiché dans la liste de
    # mots-clés en pied de carte (`ws.keywords` porte toujours "Infantry"/
    # "Hero" séparément, cf. Wahapedia) — un vrai nom français y prendrait sa
    # place plus tard (cf. la maquette HTML), mais aucune source de données
    # fiable n'existe encore pour ça.
    name_role_cell: list = [Paragraph(ws.name, _HEAD_STYLE)]

    # badge Sorcier/Prêtre en haut à droite de l'en-tête (cf.
    # `_caster_badges`) : seulement construit un en-tête à 2 colonnes quand
    # l'unité en porte un, pour ne rien changer à la mise en page de
    # l'écrasante majorité des unités (aucun niveau de magie/de prière).
    caster_badges = _caster_badges(ws.keywords)
    if caster_badges:
        badge_flow, badge_w = _caster_badge_row(caster_badges)
        name_col_w = width - 8 - 8 - badge_w - 6  # 8+8 = LEFTPADDING/RIGHTPADDING posés plus bas sur cette ligne
        header_inner = Table([[name_role_cell, badge_flow]], colWidths=[name_col_w, badge_w + 6])
        header_inner.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (1, 0), (1, 0), "RIGHT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        header_cell = [header_inner]
    else:
        header_cell = name_role_cell
    rows.append([header_cell])
    styles.append(("BACKGROUND", (0, len(rows) - 1), (-1, len(rows) - 1), colors.HexColor("#161a2b")))
    styles.append(("TOPPADDING", (0, len(rows) - 1), (-1, len(rows) - 1), 5))
    styles.append(("BOTTOMPADDING", (0, len(rows) - 1), (-1, len(rows) - 1), 5))
    styles.append(("LEFTPADDING", (0, len(rows) - 1), (-1, len(rows) - 1), 8))
    styles.append(("RIGHTPADDING", (0, len(rows) - 1), (-1, len(rows) - 1), 8))

    stat_labels = ["MV", "CT", "SV", "WD", "HP"]
    stat_values = [ws.move or "—", ws.control or "—", ws.save or "—", ws.ward or "—", ws.health or "—"]
    stat_cells = [
        Paragraph(f'{k}<br/><font size=12 color="#14172a"><b>{v}</b></font>', _STAT_STYLE)
        for k, v in zip(stat_labels, stat_values)
    ]
    stat_table = Table([stat_cells], colWidths=[width / 5] * 5)
    stat_table.setStyle(TableStyle([
        ("LINEAFTER", (0, 0), (-2, 0), 0.4, _STEEL_LINE),
        ("LINEBEFORE", (2, 0), (2, 0), 1, _STEEL),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    rows.append([stat_table])
    styles.append(("LINEBELOW", (0, len(rows) - 1), (-1, len(rows) - 1), 0.6, _STEEL_LINE))

    meta_left = f"{ws.unit_size} model" + ("s" if ws.unit_size not in ("1", "") else "") if ws.unit_size else ""
    # une manifestation/un sort vivant n'a pas de coût en points (invoqué en
    # jeu, jamais acheté dans la liste) — `ws.points` y est vide.
    meta_right = f"{ws.points} pts" if ws.points else "Invoquée"
    meta_table = Table([[Paragraph(meta_left, _META_STYLE), Paragraph(meta_right, ParagraphStyle("wc_metar", parent=_META_STYLE, alignment=2))]], colWidths=[width / 2] * 2)
    meta_table.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8)]))
    rows.append([meta_table])
    styles.append(("LINEBELOW", (0, len(rows) - 1), (-1, len(rows) - 1), 0.6, _STEEL_LINE))

    if regiment_note:
        rows.append([Paragraph(regiment_note, _NOTE_STYLE)])
        styles.append(("LEFTPADDING", (0, len(rows) - 1), (-1, len(rows) - 1), 8))
        styles.append(("TOPPADDING", (0, len(rows) - 1), (-1, len(rows) - 1), 2))
        styles.append(("BOTTOMPADDING", (0, len(rows) - 1), (-1, len(rows) - 1), 2))
        styles.append(("LINEBELOW", (0, len(rows) - 1), (-1, len(rows) - 1), 0.6, _STEEL_LINE))

    if ws.weapons:
        ratios = _wielder_ratios(ws.description)
        # une colonne Portée dédiée seulement si l'unité porte au moins une
        # arme de tir — sinon elle serait vide sur toute la carte (toutes
        # armes de mêlée) et ne ferait que grignoter la colonne Nom pour
        # rien. Une arme de mêlée sur une carte qui en a une la laisse vide
        # plutôt que d'y répéter un tiret.
        has_ranged = any(w.range for w in ws.weapons)
        whd = ["", "Portée", "Atk", "Hit", "Wnd", "Rnd", "Dmg"] if has_ranged else ["", "Atk", "Hit", "Wnd", "Rnd", "Dmg"]
        wrows = [[Paragraph(h, _WHD_STYLE) for h in whd]]
        stat_col_w = 9 * mm
        n_stat_cols = 6 if has_ranged else 5
        # `width` est la largeur pleine de la carte, mais cette table est
        # posée dans une cellule qui porte elle-même `_WEAPON_ROW_LEFT_PAD` +
        # `_WEAPON_ROW_RIGHT_PAD` de marge (cf. plus bas) — sans en tenir
        # compte ici, `colWidths` sommait à `width` plein alors que l'espace
        # réellement disponible dans la cellule est plus étroit, et une
        # valeur de dégât large ("D3+3") débordait du cadre de la carte
        # (repéré sur Terrorgheist's Fanged Maw, FEC). Même correction que
        # `_ability_group_body.content_width` applique déjà pour son propre
        # padding.
        content_width = width - _WEAPON_ROW_LEFT_PAD - _WEAPON_ROW_RIGHT_PAD
        col_widths = [content_width - n_stat_cols * stat_col_w] + [stat_col_w] * n_stat_cols
        # souligne chaque ligne d'arme dans la couleur de sa phase (même
        # palette que les bandeaux d'aptitude, `_PHASE_COLORS`) — mêlée en
        # rouge, tir en bleu — pour la distinguer au premier coup d'œil sans
        # avoir à lire la colonne Portée, et sépare visuellement les entrées
        # quand l'unité porte plusieurs profils d'arme.
        row_underlines: list[tuple[int, str]] = []
        for w in ws.weapons:
            name_para = _safe_paragraph(f"<b>{w.name}</b>", _WNAME_STYLE)
            ratio = ratios.get(w.name.strip().lower())
            ratio_pill = _pill(ratio, _BADGE_NEUTRAL, "#eaf1f8") if ratio else None
            if ratio_pill is not None:
                # ratio de porteurs à côté du nom, sur la même ligne
                # (colonnes auto-taillées, pas de `colWidths` fixe) — pas en
                # dessous, pour ne pas désaligner le nom par rapport aux
                # colonnes Atk/Hit/Wnd/Rnd/Dmg de la même ligne.
                name_line = Table([[name_para, ratio_pill]])
                name_line.setStyle(TableStyle([
                    ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (0, 0), 5),
                    ("RIGHTPADDING", (1, 0), (1, 0), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]))
                name_cell: list = [name_line]
            else:
                name_cell = [name_para]
            if w.abilities:
                name_cell.append(_safe_paragraph(_clean_text(w.abilities), _WTAG_STYLE))
            row = [name_cell]
            if has_ranged:
                row.append(Paragraph(w.range, _WVAL_STYLE) if w.range else Paragraph("", _WVAL_STYLE))
            row += [
                Paragraph(w.attacks, _WVAL_STYLE), Paragraph(w.hit, _WVAL_STYLE), Paragraph(w.wound, _WVAL_STYLE),
                Paragraph(w.rend, _WVAL_STYLE), Paragraph(w.damage, _WVAL_STYLE),
            ]
            wrows.append(row)
            underline_color = _PHASE_COLORS["shoot"][0] if w.range else _PHASE_COLORS["melee"][0]
            row_underlines.append((len(wrows) - 1, underline_color))
        weapons_table = Table(wrows, colWidths=col_widths)
        weapon_styles: list[tuple] = [
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("LEFTPADDING", (1, 0), (-1, -1), 1), ("RIGHTPADDING", (1, 0), (-1, -1), 1),
            ("LEFTPADDING", (0, 0), (0, -1), 0), ("RIGHTPADDING", (0, 0), (0, -1), 3),
        ]
        for row_i, color in row_underlines:
            weapon_styles.append(("LINEBELOW", (0, row_i), (-1, row_i), 1, colors.HexColor(color)))
        weapons_table.setStyle(TableStyle(weapon_styles))
        rows.append([weapons_table])
        styles.append(("LEFTPADDING", (0, len(rows) - 1), (-1, len(rows) - 1), _WEAPON_ROW_LEFT_PAD))
        styles.append(("RIGHTPADDING", (0, len(rows) - 1), (-1, len(rows) - 1), _WEAPON_ROW_RIGHT_PAD))
        styles.append(("LINEBELOW", (0, len(rows) - 1), (-1, len(rows) - 1), 0.6, _STEEL_LINE))

    _append_ability_groups(rows, styles, ws.abilities, width)

    visible_keywords = _visible_keywords(ws.keywords)
    if visible_keywords:
        kw_text = " · ".join(k.upper() for k in visible_keywords)
        kw_table = Table([[Paragraph(kw_text, _KW_STYLE), Paragraph("Wahapedia (EN)", _PROV_STYLE)]], colWidths=[width * 0.75, width * 0.25])
        kw_table.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
        rows.append([kw_table])

    card = Table(rows, colWidths=[width])
    card.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.8, _STEEL_LINE),
        ("BACKGROUND", (0, 0), (-1, -1), _CARD_BG),
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        *styles,
    ]))
    return card


def build_warscroll_cards_flow(
    warscrolls: list[WarscrollData], width: float = 88 * mm, gap: float = 5 * mm,
    regiment_notes: dict[str, str] | None = None,
) -> list:
    """`regiment_notes` (clé = `WarscrollData.name`) ajoute la petite note de
    provenance d'un Regiment of Renown à une seule unité membre — cf.
    `pdf_builder.py`."""
    regiment_notes = regiment_notes or {}
    full_width = width * 2 + gap
    cards: list[Flowable] = []
    solo: list[bool] = []
    for ws in warscrolls:
        note = regiment_notes.get(ws.name)
        card = render_warscroll_card(ws, width=width, regiment_note=note)
        _, height = card.wrap(width, 0xFFFF)
        oversized = height > _MAX_CARD_HEIGHT
        if oversized:
            # à demi-largeur (pairée), cette carte ne tiendrait sur aucune
            # page (cf. `_MAX_CARD_HEIGHT`) ; redessinée en pleine largeur,
            # le même texte s'enroule sur bien moins de lignes et repasse
            # sous la hauteur d'une page — posée seule sur sa ligne plutôt
            # que pairée, cf. `pack_cards_two_up`.
            card = render_warscroll_card(ws, width=full_width, regiment_note=note)
        cards.append(card)
        solo.append(oversized)
    return pack_cards_two_up(cards, width=width, gap=gap, solo=solo)


def pack_cards_two_up(
    cards: list[Flowable], width: float = 88 * mm, gap: float = 5 * mm, solo: list[bool] | None = None,
) -> list:
    """Empile des cartes (warscroll ou règle — n'importe quel `Flowable` de
    cette largeur `width`) 2 par ligne (pas de vraie mise en page « masonry »
    — reportlab ne le fait pas nativement — mais garde l'ordre d'entrée,
    plus utile pour un joueur qui parcourt sa liste dans l'ordre qu'un tri
    par hauteur pour minimiser le vide). `solo[i]` (par défaut toujours
    `False`) marque une carte déjà redessinée en pleine largeur (`width * 2 +
    gap`, cf. `build_warscroll_cards_flow`) qui doit occuper sa propre ligne
    plutôt qu'être pairée avec sa voisine."""
    solo = solo or [False] * len(cards)
    story: list = []
    i = 0
    while i < len(cards):
        if solo[i]:
            # carte déjà redessinée en pleine largeur : sa propre ligne,
            # jamais pairée avec la voisine (cf. `build_warscroll_cards_flow`).
            pair = cards[i:i + 1]
        else:
            # ne paire pas avec une voisine elle-même solo — cette dernière a
            # besoin de sa propre ligne, pas de partager celle-ci.
            pair = cards[i:i + 1] if solo[i + 1:i + 2] == [True] else cards[i:i + 2]
        if len(pair) == 2:
            # colonne d'écart dédiée plutôt qu'un padding sur la cellule de
            # la carte : chaque carte a sa propre largeur interne fixe
            # (`render_warscroll_card`'s `width`), un padding sur la cellule
            # qui la contient ne fait que forcer la table à s'élargir pour
            # continuer à loger cette largeur fixe — pas d'écart visible.
            row = Table([[pair[0], "", pair[1]]], colWidths=[width, gap, width], style=TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]))
        else:
            row = pair[0]
        if story:
            # espace *avant* chaque ligne sauf la première, pas après la
            # dernière : un `Spacer` de fin qui ne rentre plus dans l'espace
            # restant part seul sur une page neuve — page blanche en fin de
            # PDF, puisqu'un `Spacer` ne dessine rien.
            story.append(Spacer(1, gap))
        # `KeepTogether` : une paire de cartes ne doit pas se couper au
        # milieu d'une aptitude à un saut de page — si elle ne rentre pas
        # dans l'espace restant, elle part entière sur la page suivante
        # plutôt que de continuer la coupe au hasard (reportlab ne le fait
        # pas de lui-même sur une simple `Table`).
        story.append(KeepTogether([row]))
        i += len(pair)
    return story


# -- Cartes de tactique de bataille --------------------------------------
# Transcription manuelle, verbatim en français (`tactic_cards.py`) — même
# grammaire visuelle (pastilles pleines, pas de texte coloré entre crochets)
# que les cartes d'unité/de règle, adaptée : pas de bandeau de phase ici (une
# tactique se déclenche « à la fin de votre tour », pas liée à une phase
# précise du Manuel du général), 3 sous-tactiques (Échauffourée / Frappe /
# Domination) à la place, chacune avec sa propre pastille de type et sa
# pastille de points de victoire.

#: une couleur de pastille par type de sous-tactique — l'échelle de gravité
#: de la carte source (échauffourée -> frappe -> domination, en principe de
#: plus en plus difficile à déclencher) mappée sur l'échelle de sévérité déjà
#: en place pour les badges d'aptitude (neutre -> stat mise en avant ->
#: alerte), pas une nouvelle palette inventée pour l'occasion.
_TACTIC_KIND_COLORS: dict[str, tuple[str, str]] = {
    "Échauffourée": (_BADGE_NEUTRAL, "#eaf1f8"),
    "Frappe": (_BADGE_STAT, "#eaf4f6"),
    "Domination": (_BADGE_REACT, "#fbeaec"),
}
#: pastille de points de victoire — un aplat doré plus riche que
#: `_BADGE_GOLD` (réservé aux mots-clés) : ce badge doit se repérer d'un
#: coup d'œil même sans lire le texte, comme la médaille dorée de la carte
#: source, pas se confondre avec une classification de plus.
_POINTS_GOLD = "#c9a227"
_POINTS_INK = "#2a2005"

_TACTIC_HEAD_STYLE = ParagraphStyle("tc_head", fontName=CARD_TITLE_FONT, fontSize=13, leading=15, textColor=colors.white)
_TACTIC_CARD_FLAVOR_STYLE = ParagraphStyle("tc_card_flavor", fontName="Helvetica-Oblique", fontSize=8.5, leading=11, textColor=_STEEL, alignment=1)
_TACTIC_SPECIAL_STYLE = ParagraphStyle("tc_special", fontName="Helvetica", fontSize=7.8, leading=10, textColor=_STEEL)
_TACTIC_NAME_STYLE = ParagraphStyle("tc_name", fontName="Helvetica-Bold", fontSize=9, leading=11, textColor=_INK)
_TACTIC_FLAVOR_STYLE = ParagraphStyle("tc_flavor", fontName="Helvetica-Oblique", fontSize=7.3, leading=9, textColor=_STEEL)
_TACTIC_COND_STYLE = ParagraphStyle("tc_cond", fontName="Helvetica", fontSize=7.8, leading=10, textColor=_STEEL)
_TACTIC_POINTS_STYLE = ParagraphStyle("tc_points", fontName="Helvetica-Bold", fontSize=13, leading=15, textColor=colors.HexColor(_POINTS_INK), alignment=1)
_TACTIC_POINTS_LABEL_STYLE = ParagraphStyle("tc_points_lbl", fontName="Helvetica-Bold", fontSize=5.4, leading=6.4, textColor=colors.HexColor(_POINTS_INK), alignment=1)


def _points_badge(points: int, width: float) -> Table:
    """Pastille « points de victoire » dédiée, plus grande que `_pill` — la
    valeur numérique doit rester lisible même isolée dans sa propre colonne,
    c'est le seul badge de la carte que le lecteur doit pouvoir repérer sans
    lire le texte qui l'entoure."""
    inner = Table(
        [[Paragraph(str(points), _TACTIC_POINTS_STYLE)], [Paragraph("PTS DE<br/>VICTOIRE", _TACTIC_POINTS_LABEL_STYLE)]],
        colWidths=[width],
    )
    inner.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    box = Table([[inner]], colWidths=[width])
    box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(_POINTS_GOLD)),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 2), ("RIGHTPADDING", (0, 0), (-1, -1), 2),
    ]))
    return box


def _sub_tactic_block(sub: SubTactic, width: float) -> Table:
    """Un encadré par sous-tactique (Échauffourée/Frappe/Domination) : nom +
    pastille de type à gauche, pastille de points de victoire à droite —
    même schéma « contenu + badge dans sa propre colonne » que les cartes
    d'unité/de règle, décliné à l'échelle de la carte entière plutôt que
    d'une seule aptitude."""
    kind_bg, kind_fg = _TACTIC_KIND_COLORS.get(sub.kind, (_BADGE_NEUTRAL, "#eaf1f8"))
    points_col = 22 * mm
    left_width = width - points_col
    # `block` (plus bas) peint 7+6pt de marge autour de sa colonne de gauche
    # — `left`, construite ici avec une largeur fixe, doit s'y caler *après*
    # déduction de cette marge, sans quoi son contenu (notamment la ligne
    # nom+condition) déborde dans la colonne de la pastille de points voisine
    # (même bug que `_ability_group_body` avait déjà rencontré, cf. son
    # commentaire — même cause, même correctif).
    left_content_width = left_width - 13
    kind_col = 26 * mm
    name_col = left_content_width - kind_col

    header = Table(
        [[_pill(sub.kind.upper(), kind_bg, kind_fg), _safe_paragraph(f"<b>{sub.name}</b>", _TACTIC_NAME_STYLE)]],
        colWidths=[kind_col, name_col],
    )
    header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    left = Table(
        [[header], [_safe_paragraph(sub.flavor, _TACTIC_FLAVOR_STYLE)], [_safe_paragraph(sub.condition, _TACTIC_COND_STYLE)]],
        colWidths=[left_content_width],
    )
    left.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (0, 0), 0), ("BOTTOMPADDING", (0, 0), (0, 0), 2),
        ("TOPPADDING", (0, 1), (0, 1), 1), ("BOTTOMPADDING", (0, 1), (0, 1), 2),
        ("TOPPADDING", (0, 2), (0, 2), 1), ("BOTTOMPADDING", (0, 2), (0, 2), 0),
    ]))

    block = Table([[left, _points_badge(sub.points, points_col - 4 * mm)]], colWidths=[left_width, points_col])
    block.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 0), (-1, -1), 0.7, _STEEL_LINE),
        ("LEFTPADDING", (0, 0), (0, -1), 7), ("RIGHTPADDING", (0, 0), (0, -1), 6),
        ("LEFTPADDING", (1, 0), (1, -1), 2), ("RIGHTPADDING", (1, 0), (1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return block


def render_tactic_card(card: TacticCard, width: float = 188 * mm) -> Flowable:
    """Carte de tactique de bataille — remplace la copie de page PDF
    (`Manuel du général/MdG26-27 Tactiques.pdf`) par un rendu « maison »
    verbatim (texte français transcrit à la main, `tactic_cards.py`). Plus
    large que les cartes d'unité/de règle (`width` par défaut = la largeur
    utile d'une page A4 portrait) : elle n'est jamais mise en paire, cf.
    `pdf_builder._build_tactic_cards_pdf` qui les empile simplement, assez
    compactes pour que les 2 tactiques citées par une liste tiennent
    normalement sur une seule page."""
    rows: list[list] = []
    styles: list[tuple] = []

    header_cell = [
        Paragraph(card.title_fr, _TACTIC_HEAD_STYLE),
        Paragraph(f"CARTE DE TACTIQUE {card.number} · {card.name_en}", _ROLE_STYLE),
    ]
    rows.append([header_cell])
    styles += [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#161a2b")),
        ("TOPPADDING", (0, 0), (-1, 0), 6), ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("LEFTPADDING", (0, 0), (-1, 0), 8),
    ]

    rows.append([_safe_paragraph(card.flavor, _TACTIC_CARD_FLAVOR_STYLE)])
    r = len(rows) - 1
    styles += [
        ("LEFTPADDING", (0, r), (-1, r), 10), ("RIGHTPADDING", (0, r), (-1, r), 10),
        ("TOPPADDING", (0, r), (-1, r), 4), ("BOTTOMPADDING", (0, r), (-1, r), 4),
        ("LINEBELOW", (0, r), (-1, r), 0.5, _STEEL_LINE),
    ]

    if card.special_rule:
        special_box = Table(
            [[_pill("RÈGLE SPÉCIALE", _BADGE_NEUTRAL, "#eaf1f8")], [_safe_paragraph(card.special_rule, _TACTIC_SPECIAL_STYLE)]],
            colWidths=[width - 16],
        )
        special_box.setStyle(TableStyle([
            ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (0, 0), 0), ("BOTTOMPADDING", (0, 0), (0, 0), 3),
            ("TOPPADDING", (0, 1), (0, 1), 0), ("BOTTOMPADDING", (0, 1), (0, 1), 0),
        ]))
        rows.append([special_box])
        r = len(rows) - 1
        styles += [
            ("LEFTPADDING", (0, r), (-1, r), 8), ("RIGHTPADDING", (0, r), (-1, r), 8),
            ("TOPPADDING", (0, r), (-1, r), 5), ("BOTTOMPADDING", (0, r), (-1, r), 5),
            ("LINEBELOW", (0, r), (-1, r), 0.5, _STEEL_LINE),
        ]

    for sub in card.sub_tactics:
        rows.append([_sub_tactic_block(sub, width - 16)])
        r = len(rows) - 1
        styles += [
            ("LEFTPADDING", (0, r), (-1, r), 8), ("RIGHTPADDING", (0, r), (-1, r), 8),
            ("TOPPADDING", (0, r), (-1, r), 4), ("BOTTOMPADDING", (0, r), (-1, r), 4),
        ]

    card_table = Table(rows, colWidths=[width])
    card_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.8, _STEEL_LINE),
        ("BACKGROUND", (0, 0), (-1, -1), _CARD_BG),
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        *styles,
    ]))
    return card_table
