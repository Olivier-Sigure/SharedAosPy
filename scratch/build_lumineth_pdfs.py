"""Génère les quatre fiches PDF Lumineth Realm-lords (liste 2000 pts, règles,
déroulement d'un tour, stratégies).

    python scratch/build_lumineth_pdfs.py

Sorties dans ``scratch/output/``. Les données de règles et de points proviennent de
``data/wahapedia/*.csv`` (maj. 26/05/2026) ; les chiffres de rendement de
``scratch/per_unit_nocharge_floor66_TM.json``.
"""
from __future__ import annotations

from reportlab.lib.units import mm

from lumineth_pdf_kit import (
    build_document, CONTENT_W, GOLD, BLOOD_RED, BLOOD_GREEN, QUARTZ, NIGHT_BLUE,
)

W = CONTENT_W  # 178 mm

# ============================================================================
# 1. LA LISTE
# ============================================================================

def doc_liste():
    blocks = [
        ("section_here", "La liste — 2000 / 2000"),
        ("lead",
         "Quatre régiments, dix unités, quatre drops. Une phalange Vanari qui encaisse et "
         "qui marque, deux ailes rapides qui harcèlent, et un moteur runique construit pour "
         "monter en puissance jusqu'à la manche 4."),

        ("table", ["Régiment", "Unité", "Rôle", "Pts"], [
            ["<b>Régiment 1</b>", "<b>Scinari Cathallar</b> — Général", "Sorcier, coupe les commandements adverses", "130"],
            ["", "Vanari Auralan Wardens (20)", "Bloc central, enclume anti-charge", "240"],
            ["", "Ydrilan Riverblades (10)", "Se téléporte, vole les objectifs", "140"],
            ["<b>Régiment 2</b>", "<b>The Light of Eltharion</b>", "Duelliste : tue héros et monstres", "300"],
            ["", "Vanari Auralan Wardens (10)", "Écran et second point de contrôle", "120"],
            ["<b>Régiment 3</b>", "<b>Lyrior Uthralle</b>", "Moteur Varinor, relance les charges", "250"],
            ["", "Vanari Dawnriders (5)", "Marteau de cavalerie", "180"],
            ["", "Hurakan Windchargers (5)", "Tir mobile, chasse les petits", "160"],
            ["<b>Régiment 4</b>", "<b>Sevireth, Lord of the Seventh Wind</b>", "Insaisissable : tir Rend 3, M18\"", "340"],
            ["", "Vanari Auralan Sentinels (10)", "Tir de saturation à 24\"", "140"],
            ["", "<b>TOTAL</b>", "<b>Terrain : Shrine Luminor (gratuit)</b>", "<b>2000</b>"],
        ], [26 * mm, 58 * mm, 78 * mm, 16 * mm], {"align_right": (3,), "bold_first": False}),

        ("h2", "Les choix d'armée"),
        ("table", ["Choix", "Sélection", "Pourquoi"], [
            ["Formation de bataille", "<b>Warhost of Duality</b>",
             "<i>Strike as One</i> : quand on alterne les activations en phase de combat, "
             "on active 2 unités au lieu d'une. C'est la formation la plus jouée de la faction."],
            ["Trait héroïque", "<b>Flawless Commander</b><br/>(Facets of Brilliance)",
             "En phase de déploiement, jusqu'à 3 unités d'infanterie à 18\" font un mouvement normal. "
             "Sur 30 Wardens + 10 Sentinels, cela change la carte avant le premier tour."],
            ["Artefact", "<i>aucun</i>",
             "Trois héros sur quatre sont UNIQUE : interdits d'artefact. Voir l'encadré ci-dessous."],
            ["Lore de sorts", "<b>Lore of the Awakened Realms</b>",
             "Realmshield (Ward 5+ à 12\" du lanceur), Focused Erosion (-1 Rend adverse), "
             "Elemental Push (replacement de 5\")."],
            ["Lore de manifestations", "<b>Manifestations of Hysh</b>",
             "Sanctum of Amyntok en couverture, Rune of Petrification pour bloquer un couloir."],
        ], [30 * mm, 42 * mm, 106 * mm], {"bold_first": False}),

        ("box", "Le piège des améliorations",
         "Lyrior, Eltharion et Sevireth ont le mot-clé <b>UNIQUE</b> : ils ne peuvent recevoir "
         "ni trait héroïque ni artefact de pouvoir. Le Scinari Cathallar est le seul héros "
         "non-unique de la liste — il devient donc général pour débloquer le trait. L'artefact, "
         "lui, reste inutilisé.<br/><br/>"
         "<b>Si vous voulez le récupérer :</b> retirez les Sentinels (-140) et ajoutez un "
         "<b>Vanari Bannerblade</b> (+140). Il porte alors la Phoenix Stone (survit une fois sur 3+) "
         "et donne +1 en sauvegarde aux Vanari Infantry qui contestent le même objectif que lui."),

        ("h2", "Contraintes de régiment à connaître"),
        ("p", "Les options de régiment Lumineth sont étroites : un chef ne peut pas emmener n'importe "
              "quelle unité. C'est ce qui a dicté la répartition ci-dessus."),
        ("table", ["Chef", "Peut emmener"], [
            ["Scinari (Cathallar, Calligrave, Loreseeker, Enlightener)",
             "Vanari Auralan Wardens (autant qu'on veut), Vanari Bladelords, <b>0-1</b> Ydrilan Riverblades"],
            ["Vanari Lord Regent / Bannerblade", "N'importe quelle unité VANARI"],
            ["Sevireth", "N'importe quelle unité VANARI ou HURAKAN"],
            ["Avalenor", "N'importe quelle unité ALARITH ou VANARI"],
            ["Lyrior, Light of Eltharion, Teclis, Ellania &amp; Ellathor",
             "N'importe quelle unité LUMINETH REALM-LORDS — ce sont les seuls chefs « ouverts »"],
            ["Alarith Stonemage / Hurakan Windmage",
             "Unités de leur propre temple (ALARITH / HURAKAN), plus Wardens et 0-1 Riverblades"],
        ], [62 * mm, 116 * mm], {"bold_first": True}),

        ("note", "Un régiment, c'est quoi ?",
         "Un régiment = 1 héros + jusqu'à 3 autres unités. Vous déployez un régiment entier à la fois : "
         "moins vous avez de régiments, moins vous avez de « drops », et plus vous avez de chances de "
         "choisir qui commence. Ici : 4 régiments, donc 4 drops."),

        # ------------------------------------------------------------------
        ("section", "Le moteur runique"),
        ("lead",
         "Le nouveau battletome (février 2026) n'a plus qu'un seul trait de bataille : "
         "<b>Depict Rune</b>. Au début de chaque manche, vous gravez une rune sur votre "
         "« battle scripture »."),

        ("ul", [
            "La rune choisie <b>reste gravée pour le reste de la partie</b>.",
            "Mais son <b>effet</b> ne s'applique qu'à la manche où vous la gravez.",
            "Vous désignez <b>2 unités amies par instance</b> de cette rune déjà présente sur la scripture.",
            "Les effets « harmonie » ne se déclenchent que si l'autre rune est <b>déjà</b> gravée.",
        ]),

        ("table", ["Rune", "Effet de base (sur les cibles)", "Harmonies"], [
            ["<b>Varinor</b><br/>Rune de la Force",
             "+1 aux jets de course et de charge.",
             "<b>+ Ydriliqi :</b> +1 aux jets de blessure en mêlée.<br/>"
             "<b>+ Oreali :</b> peut tirer et/ou charger même après une retraite."],
            ["<b>Alaithi</b><br/>Rune de la Montagne",
             "Les cibles gagnent <b>WARD (5+)</b>.",
             "<b>+ Varinor :</b> armes de mêlée avec Anti-charge (+1 Rend).<br/>"
             "<b>+ Ydriliqi :</b> -1 aux jets de blessure ennemis contre les cibles."],
            ["<b>Ydriliqi</b><br/>Rune de la Rivière",
             "-2 aux jets de charge des unités ennemies à 12\" des cibles.",
             "<b>+ Alaithi :</b> ignore les modificateurs négatifs de touche et de blessure.<br/>"
             "<b>+ Oreali :</b> mouvement de 3\" pouvant traverser les zones de combat."],
            ["<b>Oreali</b><br/>Rune du Vent",
             "-1 aux jets de touche des attaques de mêlée ennemies visant les cibles.",
             "<b>+ Varinor :</b> +4\" de Mouvement.<br/>"
             "<b>+ Alaithi :</b> +5 au score de contrôle."],
            ["<b>Thalari</b><br/>Rune du Zénith",
             "+2 aux jets d'incantation des Lumineth. <i>(pas de cibles : effet d'armée)</i>",
             "<b>Avec 4 runes uniques ou plus :</b> +4\" de Mouvement et critiques sur 5+ "
             "non modifiés, pour toute l'armée."],
        ], [32 * mm, 62 * mm, 84 * mm], {"bold_first": False}),

        ("box", "Les trois amplificateurs de rune",
         "Trois héros donnent une <b>instance supplémentaire</b> d'une rune, mais uniquement pour les "
         "capacités inscrites sur les warscrolls des unités amies du bon temple à 12\" :<br/>"
         "<b>Lyrior</b> (Champion of the Lord Phoenix) : Varinor, pour les VANARI.<br/>"
         "<b>Sevireth</b> (Call of the Winds) : Oreali, pour les HURAKAN.<br/>"
         "<b>Avalenor</b> (Call of the Mountains) : Alaithi, pour les ALARITH.<br/><br/>"
         "C'est ce qui pousse la faction vers des listes mono-temple. Dans cette liste, Lyrior colle "
         "aux Dawnriders et Sevireth aux Windchargers : c'est la raison d'être des régiments 3 et 4."),

        ("h2", "Plan de gravure manche par manche"),
        ("table", ["Manche", "Rune", "Ce que vous obtenez"], [
            ["<b>1</b>", "<b>Varinor</b>",
             "+1 course et charge sur Dawnriders et Windchargers. Aucune harmonie encore : "
             "on achète du tempo et une charge de 9\" fiable si l'adversaire s'avance."],
            ["<b>2</b>", "<b>Ydriliqi</b>",
             "-2 aux charges ennemies autour du bloc de 20 Wardens, et +1 aux blessures grâce à Varinor. "
             "C'est aussi la manche où les Riverblades peuvent se poser <i>n'importe où</i> à plus de 9\" "
             "au lieu de 6\" d'un bord de table."],
            ["<b>3</b>", "<b>Alaithi</b>",
             "Ward (5+) sur les deux unités qui vont recevoir la charge, plus Anti-charge (+1 Rend) via "
             "Varinor et -1 aux blessures ennemies via Ydriliqi. La manche défensive de la partie."],
            ["<b>4</b>", "<b>Oreali</b>",
             "-1 pour toucher les cibles, +4\" de mouvement via Varinor, +5 en contrôle via Alaithi. "
             "Quatre runes uniques gravées : c'est le tour où l'on pousse sur les objectifs contestés."],
            ["<b>5</b>", "<b>Thalari</b>",
             "Cinquième rune unique : +4\" de mouvement et critiques sur 5+ pour toute l'armée. "
             "Sur les Wardens (Crit : Mortal) et les Sentinels (Crit : Auto-wound), le gain est énorme."],
        ], [16 * mm, 26 * mm, 136 * mm], {"bold_first": False}),

        ("note", "Variante « profondeur »",
         "Contre une armée qui vous surclasse au corps à corps, remplacez les manches 3 et 4 par un "
         "<b>double Alaithi</b> : la seconde gravure cible 4 unités au lieu de 2 et débloque les seuils "
         "« 2 instances ou plus » des warscrolls. Vous renoncez à Thalari, donc au pic de la manche 5.",
         BLOOD_RED),

        # ------------------------------------------------------------------
        ("section", "Ce qui rend cette armée différente"),
        ("note", "Deux activations d'un coup",
         "<i>Strike as One</i> (Warhost of Duality) permet de choisir 2 unités Lumineth au lieu d'une "
         "quand on alterne les activations en phase de combat. Eltharion + Wardens, ou Dawnriders + "
         "Windchargers : on tue la cible avant qu'elle ne frappe en retour. C'est la capacité la plus "
         "importante de la liste — construisez vos engagements autour d'elle.", QUARTZ),
        ("note", "La pique contre la charge",
         "Les Wardens annulent l'effet <i>Charge (+1 Damage)</i> des attaques ennemies s'ils n'ont pas "
         "chargé eux-mêmes (<i>Anticipated Strike</i>), et leurs piques ont Anti-charge (+1 Rend) et "
         "Crit (Mortal). <b>Ne les faites jamais charger : attendez.</b>", QUARTZ),
        ("note", "Deux lanceurs de sorts, pas plus",
         "Lyrior et le Cathallar. Le lore <i>Awakened Realms</i> donne Realmshield (Ward 5+ à 12\" du "
         "lanceur), Focused Erosion (-1 Rend adverse) et Elemental Push. Cela fait peu d'incantations : "
         "gardez le Cathallar au centre du bloc, il n'a pas besoin d'aller plus loin.", QUARTZ),
        ("note", "Le Cathallar coupe les commandements",
         "<i>Darkness of the Soul</i> : sur 3+, une unité ennemie à 18\" ne peut plus utiliser de "
         "commandement jusqu'à votre prochain tour. Visez le contre-charge, l'All-out Defence ou le "
         "Redeploy qui vous gênerait le plus. Zéro dégât, énorme impact.", QUARTZ),
        ("note", "Sevireth ne se laisse pas attraper",
         "M18\", Ward (5+), tir 15\" à Rend 3 utilisable au contact, et un mouvement de D6\" + 2\" par "
         "instance d'Oreali <i>après</i> avoir tiré. Il n'est pas là pour tenir un objectif : il "
         "ramasse les objectifs faibles et abat les héros de soutien.", QUARTZ),
        ("note", "Les Riverblades sont un outil de score",
         "Déploiement téléporté chaque tour (bord de table, ou n'importe où la manche où Ydriliqi est "
         "gravée), M7\", et un mouvement de 2D6\" en phase de combat qui traverse les figurines "
         "ennemies. Ce sont vos points de victoire, pas vos dégâts.", QUARTZ),
        ("note", "Le mouvement de déploiement",
         "<i>Flawless Commander</i> s'utilise en <b>phase de déploiement</b> : trois unités d'infanterie "
         "font un mouvement normal avant le premier tour. Le général peut mourir ensuite sans que vous "
         "ayez rien perdu — c'est pourquoi un Cathallar à 5 PV fait un général acceptable.", QUARTZ),

        # ------------------------------------------------------------------
        ("section", "Ce que disent les calculs"),
        ("lead",
         "Extrait des résultats AoSPy chargés (722 unités, tous duels attaquant × défenseur, sans "
         "charge, plancher de dégâts 66 %). Le <b>ROI</b> est le rapport points détruits / points "
         "investis ; le <b>percentile</b> situe l'unité face à toute la base de données."),

        ("table", ["Unité", "Pts", "ROI moyen", "Duels gagnants", "Perc.", "Dans la liste ?"], [
            ["The Light of Eltharion", "300", f"<font color='#2f6b32'><b>+13,9 %</b></font>", "83,7 %", "85e", "Oui — meilleure unité de la faction"],
            ["Hurakan Windchargers", "160", f"<font color='#2f6b32'><b>+8,6 %</b></font>", "60,1 %", "77e", "Oui"],
            ["Vanari Auralan Wardens", "120", f"<font color='#2f6b32'><b>+6,8 %</b></font>", "51,7 %", "74e", "Oui — 30 figurines"],
            ["Vanari Auralan Sentinels", "140", f"<font color='#2f6b32'><b>+6,8 %</b></font>", "55,5 %", "74e", "Oui"],
            ["Vanari Dawnriders", "180", f"<font color='#2f6b32'><b>+5,0 %</b></font>", "57,1 %", "69e", "Oui"],
            ["Ydrilan Riverblades", "140", "+0,3 %", "46,9 %", "62e", "Oui — pour le score"],
            ["Alarith Stoneguard", "130", f"<font color='#8c1f1f'>-3,7 %</font>", "43,6 %", "55e", "Non — hors thème Vanari"],
            ["Alarith Spirit of the Mountain", "340", f"<font color='#8c1f1f'>-4,7 %</font>", "43,9 %", "54e", "Non"],
            ["Avalenor, the Stoneheart King", "420", f"<font color='#8c1f1f'>-4,9 %</font>", "45,2 %", "54e", "Non — pivot d'une autre liste"],
            ["Archmage Teclis", "640", f"<font color='#8c1f1f'>-7,1 %</font>", "35,1 %", "51e", "Non — trop cher ici"],
            ["Sevireth", "340", f"<font color='#8c1f1f'>-7,5 %</font>", "43,3 %", "50e", "Oui — valeur hors combat"],
            ["Vanari Bladelords", "150", f"<font color='#8c1f1f'>-13,2 %</font>", "34,0 %", "45e", "Non — Wardens plus rentables"],
            ["Ellania &amp; Ellathor", "290", f"<font color='#8c1f1f'>-14,5 %</font>", "31,1 %", "43e", "Non"],
            ["Lyrior Uthralle", "250", f"<font color='#8c1f1f'>-15,9 %</font>", "32,2 %", "42e", "Oui — moteur Varinor"],
            ["Vanari Lord Regent on Lightcourser", "150", f"<font color='#8c1f1f'>-26,5 %</font>", "22,3 %", "32e", "Non"],
            ["Vanari Starshard Ballista", "120", f"<font color='#8c1f1f'>-31,4 %</font>", "17,8 %", "29e", "Non"],
            ["Scinari Loreseeker", "140", f"<font color='#8c1f1f'>-33,4 %</font>", "19,0 %", "28e", "Non"],
            ["Vanari Lord Regent", "110", f"<font color='#8c1f1f'>-49,0 %</font>", "9,2 %", "18e", "Non"],
            ["Vanari Bannerblade", "140", f"<font color='#8c1f1f'>-54,0 %</font>", "6,9 %", "14e", "Variante artefact"],
            ["Scinari Enlightener", "180", f"<font color='#8c1f1f'>-68,9 %</font>", "2,7 %", "7e", "Non"],
            ["Alarith Stonemage", "130", f"<font color='#8c1f1f'>-80,1 %</font>", "1,3 %", "4e", "Non"],
            ["Scinari Calligrave", "130", f"<font color='#8c1f1f'>-85,7 %</font>", "1,2 %", "2e", "Non"],
            ["Scinari Cathallar", "130", f"<font color='#8c1f1f'>-90,2 %</font>", "0,0 %", "1e", "Oui — valeur nulle en duel"],
        ], [52 * mm, 12 * mm, 22 * mm, 24 * mm, 14 * mm, 54 * mm], {"align_right": (1, 2, 3, 4)}),

        ("box", "Trois limites à garder en tête",
         "<b>1. Le modèle ne compte que les dégâts.</b> Wards, buffs, runes, sorts, mobilité, contrôle "
         "d'objectif : rien de tout cela n'entre dans le calcul. C'est pourquoi tous les héros de "
         "soutien Lumineth s'effondrent en bas de tableau — le Cathallar est dernier de la faction et "
         "reste un bon choix.<br/><br/>"
         "<b>2. Les points ont bougé.</b> Les résultats chargés utilisent l'ancienne grille ; Wahapedia "
         "(maj. 26/05/2026) est plus récent. Dawnriders -20, Windchargers -10, Sentinels -10, "
         "Riverblades -10, Sevireth -10, Lyrior -10 : toutes les unités retenues ont <i>baissé</i>, "
         "leur ROI réel est donc meilleur que la colonne ne l'indique.<br/><br/>"
         "<b>3. Lumineth est 20e sur 25.</b> En ROI médian brut, la faction est dans le dernier quart "
         "du jeu. Traduction : ne cherchez pas à gagner l'échange de dégâts. Gagnez par le placement, "
         "le ward et les objectifs."),

        ("h2", "Cohérence avec le méta"),
        ("p", "Les listes qui placent en tournoi depuis la sortie du tome recoupent ce classement : "
              "Lyrior + Light of Eltharion + Windchargers, ou Sevireth + Eltharion + Ellania avec "
              "Wardens et Dawnriders. <b>Warhost of Duality</b> est la formation la plus jouée ; "
              "<b>Pilgrims of Haixiah</b> (Power Through sans avoir chargé) est citée comme "
              "l'alternative la plus « méta » si vous partez sur les esprits Hurakan."),
        ("p", "Deux autres formations valent le détour selon la liste : <b>Scinari Council</b> "
              "(sorts UNLIMITED) si vous montez à quatre lanceurs, <b>Aelementor Guardians</b> si vous "
              "jouez Avalenor ou un Alarith Spirit of the Mountain."),

        ("h2", "Variantes de liste"),
        ("table", ["Si vous voulez...", "Changement", "Effet"], [
            ["Un artefact utilisable", "-Sentinels (140) / +Vanari Bannerblade (140)",
             "Phoenix Stone sur le Bannerblade ; +1 en sauvegarde aux Vanari Infantry sur son objectif. "
             "Vous perdez tout tir à longue portée."],
            ["Plus de magie", "-Riverblades (140) / +Scinari Calligrave (130) + 10 pts libres",
             "Le Calligrave <i>remplace</i> une rune gravée par une autre au début du tour : c'est le "
             "seul moyen de corriger un mauvais plan de gravure."],
            ["Un vrai marteau", "-Sentinels (140) -Riverblades (140) / +Dawnriders (180) + 100 pts",
             "Deux unités de Dawnriders dans le régiment de Lyrior, à relance de charge. "
             "Il reste 100 pts à replacer (Wardens supplémentaires impossibles : 120)."],
            ["Jouer les esprits", "Liste différente : Avalenor + Alarith Spirit of the Mountain",
             "Formation Aelementor Guardians, gravure Alaithi empilée. Autre archétype complet, "
             "moins bien noté en ROI brut mais bien plus résistant."],
        ], [34 * mm, 62 * mm, 82 * mm], {"bold_first": True}),
    ]

    return build_document(
        "01_Lumineth_liste_2000pts.pdf",
        "Lumineth Realm-lords — Liste 2000 pts",
        "Warhost of Duality",
        "Liste Lumineth Realm-lords 2000 points et fiche des particularités",
        [
            "<b>Ce document</b> contient la liste d'armée complète, les choix d'améliorations, "
            "le fonctionnement du moteur runique, le plan de gravure manche par manche, "
            "les particularités à connaître et le rendement chiffré des unités de la faction.",
            "<b>Sources :</b> export Wahapedia du dépôt (mise à jour du 26/05/2026) pour les règles "
            "et les coûts en points ; <i>scratch/per_unit_nocharge_floor66_TM.json</i> (AoSPy, "
            "722 unités) pour les duels ; presse spécialisée (Goonhammer, Frontline Gaming, "
            "Warhammer Community) pour les tendances de tournoi.",
            "<b>Les trois autres fiches de la série :</b> le manuel des règles pour débutant, "
            "la fiche de déroulement d'un tour, et la fiche de stratégies par adversaire et par "
            "scénario.",
        ],
        "LUMINETH REALM-LORDS  ·  LISTE 2000 PTS",
        blocks,
        cover_footer="Fiche I sur IV — Compendium Lumineth",
    )


def main():
    import lumineth_doc_regles, lumineth_doc_tour, lumineth_doc_strategies
    for path in (doc_liste(), lumineth_doc_regles.build(),
                 lumineth_doc_tour.build(), lumineth_doc_strategies.build()):
        print("écrit :", path)


if __name__ == "__main__":
    main()
