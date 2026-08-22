"""Fiche III — Déroulement d'un tour : aide de jeu à garder sur la table."""
from __future__ import annotations

from reportlab.lib.units import mm

from lumineth_pdf_kit import build_document, CONTENT_W, GOLD, BLOOD_RED, QUARTZ, BLOOD_GREEN

W = CONTENT_W


def build():
    blocks = [
        ("section_here", "La manche en un coup d'œil"),
        ("lead", "Une manche = début de manche, puis un tour complet pour chaque joueur. "
                 "La colonne de droite est votre pense-bête Lumineth."),

        ("table", ["Étape", "Règle générale", "Réflexe Lumineth"], [
            ["<b>Début de<br/>manche</b>",
             "Jet de priorité (sauf manche 1) : le gagnant décide qui joue en premier. "
             "Chaque joueur reçoit 1 PC au début de son tour.",
             "<b>DEPICT RUNE — obligatoire.</b> Gravez la rune de la manche, désignez 2 unités par "
             "instance, notez l'initiale sur votre feuille."],
            ["<b>1. Héros</b>",
             "Sorts, prières, capacités de héros, commande <i>Rally</i>.",
             "Realmshield (Cathallar ou Lyrior) · Darkness of the Soul sur la menace du tour · "
             "Focused Fury si Lyrior va charger."],
            ["<b>2. Mouvement</b>",
             "Normal Move, Run (M + D6, plus de tir ni de charge), Retreat.",
             "Téléport des Riverblades · Sevireth se replace · vérifiez que Lyrior reste à 12\" des "
             "Dawnriders et Sevireth à 12\" des Windchargers."],
            ["<b>3. Tir</b>",
             "Impossible au corps à corps, sauf <i>Shoot in Combat</i>.",
             "Sentinels (Lofted Shots pour 24\" à -1) · Windchargers · Sevireth tire <b>puis</b> se "
             "déplace de D6\" + 2\" par Oreali."],
            ["<b>4. Charge</b>",
             "2D6\", à moins de 12\" d'un ennemi.",
             "Dawnriders uniquement (leur profil ne vaut que chargé). "
             "<b>Les Wardens ne chargent jamais.</b> Forward to Victory si la charge compte."],
            ["<b>5. Combat</b>",
             "Activation <b>alternée</b>, joueur actif d'abord. Chaque unité : pile-in puis attaques.",
             "<b>Strike as One :</b> activez 2 unités d'un coup. Searing Desert Winds de Sevireth "
             "avant ses attaques."],
            ["<b>6. Fin de tour</b>",
             "Capacités de fin de tour, puis décompte des objectifs.",
             "Comptez le contrôle : +5 par unité ciblée si Oreali et Alaithi sont gravées."],
        ], [24 * mm, 74 * mm, 80 * mm], {"bold_first": False}),

        ("box", "Les trois questions à se poser au début de chaque manche",
         "<b>1. Est-ce que je peux perdre la priorité ?</b> Si oui, je ne m'expose pas complètement : "
         "je garde Alaithi ou Realmshield en réserve.<br/>"
         "<b>2. Quelle rune me sert cette manche, et laquelle prépare la suivante ?</b> Une harmonie ne "
         "fonctionne que si l'autre rune est déjà gravée.<br/>"
         "<b>3. Où vais-je marquer ?</b> Les Lumineth gagnent au score, pas à l'échange de dégâts. "
         "S'il n'y a pas de point à prendre, il n'y a pas de raison d'avancer."),

        # ------------------------------------------------------------------
        ("section", "Le détail, phase par phase"),

        ("h2", "Début de manche"),
        ("ol", [
            "Jet de priorité (2 dés, un chacun ; à égalité, celui qui a joué en premier la manche "
            "précédente décide). Pas de jet à la manche 1.",
            "<b>Depict Rune</b> : choisissez la rune, désignez <b>2 unités amies par instance déjà "
            "gravée</b> de cette rune, notez l'initiale (V / A / Y / O / T).",
            "Vérifiez quelles harmonies s'activent : elles ne comptent que si l'autre rune est déjà sur "
            "la scripture.",
            "Le joueur actif reçoit 1 PC (2 s'il est en retard au score).",
        ]),

        ("h2", "Phase de héros"),
        ("ul", [
            "<b>Cathallar :</b> <i>Darkness of the Soul</i> — sur 3+, une unité ennemie à 18\" ne peut "
            "plus utiliser de commandement. Visez celle qui allait faire un contre-charge, un All-out "
            "Defence ou un Redeploy.",
            "<b>Realmshield</b> (Cathallar ou Lyrior) : Ward 5+ à toutes les unités Lumineth "
            "entièrement à 12\" du lanceur. Placez le lanceur pour couvrir le maximum d'unités.",
            "<b>Lyrior :</b> <i>Focused Fury</i> (2D6, +2 au contact) pour gagner STRIKE-FIRST.",
            "<b>Rally</b> si une unité hors combat a perdu des figurines.",
            "N'oubliez pas que votre adversaire agit aussi dans cette phase, après vous.",
        ]),

        ("h2", "Phase de mouvement"),
        ("ul", [
            "<b>Riverblades :</b> <i>Travel The Waterways</i> — retirez-les, replacez-les à 6\" d'un "
            "bord de table (n'importe où sur la table la manche où Ydriliqi est gravée), à plus de 9\" "
            "de tout ennemi.",
            "<b>Distances de sécurité :</b> une unité à plus de 12\" ne peut pas être chargée. Entre "
            "9\" et 12\", la charge est peu probable ; en dessous de 9\", elle est probable.",
            "<b>Ne courez pas</b> avec les Sentinels ni les Windchargers : courir interdit de tirer.",
            "Gardez les liaisons : Lyrior à 12\" des unités VANARI, Sevireth à 12\" des HURAKAN, le "
            "Cathallar à 12\" de ce que Realmshield doit couvrir.",
        ]),

        ("h2", "Phase de tir"),
        ("ul", [
            "<b>Sentinels :</b> 20 tirs à 18\". <i>Lofted Shots</i> monte à 24\" mais à -1 pour toucher "
            "— ne l'utilisez que si vous ne pouvez pas atteindre la cible autrement.",
            "<b>Windchargers :</b> 15 tirs, Anti-CAVALRY (+1 Rend), auto-blessure sur les 6.",
            "<b>Sevireth :</b> 4 tirs à Rend 3, puis <b>il se déplace</b> de D6\" + 2\" par instance "
            "d'Oreali. Tirez d'abord, bougez ensuite : c'est ce qui le rend impossible à coincer.",
            "<b>Light of Eltharion :</b> 3 tirs à Rend 2, utilisables même au corps à corps.",
        ]),

        ("h2", "Phase de charge"),
        ("ul", [
            "Seuls les Dawnriders et Lyrior gagnent vraiment à charger (<i>Charge (+1 Damage)</i> et "
            "+1 Rend).",
            "Avec Varinor gravée : +1 au jet de charge. Avec <i>Forward to Victory</i> : relance.",
            "<b>Les Wardens ne chargent jamais</b> : ils perdraient <i>Anticipated Strike</i> et leur "
            "Anti-charge.",
            "Attention : charger, c'est aussi offrir la première activation à l'adversaire s'il a "
            "STRIKE-FIRST.",
        ]),

        ("h2", "Phase de combat — la phase qui décide la partie"),
        ("ol", [
            "Le joueur actif active une unité, puis l'adversaire, en alternance.",
            "<b>Strike as One</b> (Warhost of Duality) : à votre tour de choisir, désignez <b>2 unités "
            "Lumineth</b> et résolvez-les l'une après l'autre. C'est votre meilleure carte : gardez-la "
            "pour le moment où deux unités peuvent tuer une cible avant qu'elle ne réplique.",
            "Avant les attaques de Sevireth : <i>Searing Desert Winds</i> — jusqu'à 3 unités ennemies "
            "à 6\", dégâts mortels et -1 à leurs blessures pour le tour.",
            "Quand vos Wardens sont pris pour cible : <b>All-out Defence</b>.",
            "Quand une de vos unités frappe la cible décisive : <b>All-out Attack</b>.",
        ]),

        ("h2", "Fin de tour et score"),
        ("ul", [
            "Résolvez les capacités de fin de tour.",
            "Comptez les objectifs : additionnez le Contrôle des figurines dans les 3\" du marqueur. "
            "Un objectif contrôlé le reste jusqu'à ce que l'adversaire prenne l'avantage.",
            "Vérifiez vos battle tactics : Affray, puis Strike, puis Domination — dans cet ordre.",
        ]),

        # ------------------------------------------------------------------
        ("section", "Mémo de table"),

        ("h2", "Les huit oublis les plus fréquents"),
        ("ol", [
            "<b>Oublier de graver la rune</b> au début de la manche. C'est obligatoire, et rétroactif "
            "nulle part.",
            "<b>Oublier de désigner les cibles</b> de la rune : 2 unités par instance, pas « toute "
            "l'armée ».",
            "<b>Faire charger les Wardens.</b> Ils perdent leur meilleure capacité défensive.",
            "<b>Déplacer Sevireth avant de tirer.</b> Son mouvement gratuit vient <i>après</i> le tir.",
            "<b>Oublier Strike as One</b> et n'activer qu'une unité à la fois.",
            "<b>Oublier Darkness of the Soul</b> : c'est une capacité gratuite, tous les tours.",
            "<b>Faire courir les Sentinels</b> : ils perdent leur tir, qui est leur seule raison d'être.",
            "<b>Oublier que les critiques des Wardens sont des dégâts mortels</b> : ils ne se "
            "sauvegardent pas, comptez-les à part.",
        ]),

        ("h2", "Seuils de runes à surveiller"),
        ("table", ["Condition", "Unité", "Gain"], [
            ["1 Varinor gravée", "Vanari Bladelords", "+1 de Rend aux Sunmetal Blades (par instance)."],
            ["1 Alaithi gravée", "Alarith Spirit / Avalenor", "+1 attaque au marteau (par instance)."],
            ["2 Alaithi gravées", "Alarith Stoneguard", "Sauvegarde 3+ au lieu de 4+."],
            ["2 Oreali gravées", "Hurakan Windchargers", "Portée des arcs 18\" au lieu de 12\"."],
            ["Ydriliqi gravée cette manche", "Ydrilan Riverblades", "Téléport n'importe où, pas "
                                                                    "seulement près d'un bord."],
            ["4 runes uniques", "Toute l'armée (Thalari)", "+4\" de Mouvement et critiques sur 5+."],
        ], [46 * mm, 48 * mm, 84 * mm]),

        ("h2", "Distances utiles"),
        ("table", ["Distance", "Ce qu'elle représente"], [
            ["1\"", "Portée d'une arme de mêlée : il faut être à 1\" pour attaquer."],
            ["3\"", "Zone de combat, et rayon pour contester un objectif."],
            ["9\"", "Distance minimale d'un déploiement en réserve ou d'un téléport. C'est aussi la "
                    "charge « moyenne » à ne pas offrir."],
            ["12\"", "Portée maximale d'une charge. Portée des auras de Lyrior, Sevireth, Realmshield, "
                     "Flawless Commander (version passive)."],
            ["18\"", "Portée de Darkness of the Soul, des sorts offensifs, du trait Flawless Commander "
                     "au déploiement, des arcs des Sentinels."],
        ], [22 * mm, 156 * mm]),

        ("note", "L'ordre d'action idéal, en une phrase",
         "Graver la rune, couper le commandement adverse, poser le Ward, déplacer les marqueurs de "
         "score, tirer avec ce qui tire, charger uniquement avec ce qui gagne à charger, puis activer "
         "deux unités d'un coup.", BLOOD_GREEN),
    ]

    return build_document(
        "03_Lumineth_deroulement_dun_tour.pdf",
        "Lumineth Realm-lords — Déroulement d'un tour",
        "Le Tour de Bataille",
        "Aide de jeu : la séquence complète, phase par phase, avec les réflexes Lumineth",
        [
            "<b>Cette fiche se garde sur la table.</b> Elle donne la séquence complète d'une manche "
            "d'Age of Sigmar, et pour chaque phase, ce que vous devez penser à faire avec cette liste "
            "Lumineth précise.",
            "La première page suffit une fois que vous avez pris l'habitude ; les suivantes détaillent "
            "chaque phase et listent les oublis les plus coûteux.",
        ],
        "LUMINETH REALM-LORDS  ·  DÉROULEMENT D'UN TOUR",
        blocks,
        cover_footer="Fiche III sur IV — Compendium Lumineth",
    )
