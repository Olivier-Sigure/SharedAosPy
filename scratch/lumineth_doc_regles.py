"""Fiche II — Les règles d'Age of Sigmar et des Lumineth, expliquées depuis zéro."""
from __future__ import annotations

from reportlab.lib.units import mm

from lumineth_pdf_kit import build_document, CONTENT_W, GOLD, BLOOD_RED, QUARTZ

W = CONTENT_W


def build():
    blocks = [
        ("section_here", "Comment on gagne une partie"),
        ("lead",
         "Age of Sigmar ne se gagne pas en tuant l'armée adverse. Il se gagne aux "
         "<b>points de victoire</b>. On peut perdre les trois quarts de son armée et gagner "
         "largement — c'est exactement le plan des Lumineth."),

        ("h2", "Les deux sources de points"),
        ("ul", [
            "<b>Les objectifs.</b> Des marqueurs posés sur la table selon le scénario. À la fin de "
            "chaque tour, vous marquez des points pour ceux que vous contrôlez.",
            "<b>Les battle tactics.</b> Deux cartes choisies pendant la composition d'armée. Chaque "
            "carte contient trois objectifs à réaliser dans l'ordre (Affray, puis Strike, puis "
            "Domination), 5 points de victoire chacun.",
        ]),
        ("p", "À la fin de la bataille, celui qui a au moins 5 points de victoire d'avance remporte "
              "une victoire majeure."),

        ("h2", "Contrôler un objectif"),
        ("p", "Une unité « conteste » un objectif si elle a une figurine dans les 3\" du marqueur. "
              "Chaque figurine apporte sa caractéristique de <b>Contrôle</b>. On additionne, camp par "
              "camp : le total le plus élevé contrôle l'objectif — et le garde jusqu'à ce qu'il le perde."),
        ("note", "Pourquoi c'est central pour vous",
         "Vos Wardens ont Contrôle 1 par figurine, mais vous en avez 30 : 30 points de contrôle "
         "répartis sur deux blocs. Sevireth a Contrôle 5 à lui tout seul. Et la rune Oreali harmonisée "
         "avec Alaithi donne <b>+5 au score de contrôle</b> des unités ciblées : c'est souvent ce qui "
         "renverse un objectif contesté, sans tuer personne.", QUARTZ),

        # ------------------------------------------------------------------
        ("section", "Lire un warscroll"),
        ("lead", "Chaque unité a une fiche (« warscroll ») avec des caractéristiques d'unité et une "
                 "ou plusieurs armes."),

        ("h2", "Les caractéristiques d'unité"),
        ("table", ["Sigle", "Nom", "Ce que ça veut dire"], [
            ["M", "Move (Mouvement)", "Distance en pouces parcourue avec un mouvement normal."],
            ["Sv", "Save (Sauvegarde)", "Score à obtenir sur un D6 pour annuler une blessure. "
                                        "3+ est bon, 6+ est mauvais."],
            ["C", "Control (Contrôle)", "Ce que chaque figurine apporte pour tenir un objectif."],
            ["W", "Health (Points de vie)", "Par figurine. Une figurine à 1 PV meurt à la première "
                                            "blessure non sauvée."],
            ["Ward", "Ward (Protection)", "Une seconde sauvegarde, après la première, que le Rend ne "
                                          "peut pas réduire. C'est la ressource défensive n°1 des Lumineth."],
        ], [16 * mm, 40 * mm, 122 * mm]),

        ("h2", "Les caractéristiques d'arme"),
        ("table", ["Sigle", "Nom", "Ce que ça veut dire"], [
            ["Rng", "Range (Portée)", "Vide = arme de mêlée. Sinon, la portée en pouces pour tirer."],
            ["A", "Attacks (Attaques)", "Nombre de dés lancés, <b>par figurine</b>."],
            ["Hit", "To hit (Touche)", "Score à faire pour toucher."],
            ["Wnd", "To wound (Blessure)", "Score à faire, après avoir touché, pour blesser."],
            ["Rnd", "Rend (Pénétration)", "Se soustrait à la sauvegarde adverse. Rend 2 transforme "
                                          "une sauvegarde 3+ en 5+."],
            ["Dmg", "Damage (Dégâts)", "Points de vie retirés par blessure non sauvée."],
        ], [16 * mm, 40 * mm, 122 * mm]),

        # ------------------------------------------------------------------
        ("section", "La séquence d'attaque, pas à pas"),
        ("lead", "C'est la mécanique que vous répéterez toute la partie. Elle se déroule toujours dans "
                 "cet ordre, et chaque étape peut faire échouer l'attaque."),
        ("ol", [
            "<b>Nombre de dés.</b> Figurines qui peuvent attaquer × Attaques de l'arme.",
            "<b>Jet de touche.</b> Un D6 par attaque, il faut la caractéristique Hit ou mieux.",
            "<b>Jet de blessure.</b> Un D6 par touche, il faut la caractéristique Wnd ou mieux.",
            "<b>Jet de sauvegarde.</b> C'est le <b>défenseur</b> qui lance, un D6 par blessure, avec sa "
            "Save <i>modifiée par le Rend</i>. Une réussite annule la blessure.",
            "<b>Jet de ward.</b> Si le défenseur a un Ward, il relance un D6 par blessure passée. Le "
            "Rend ne s'y applique <b>pas</b>.",
            "<b>Dégâts.</b> Chaque blessure survivante retire un nombre de PV égal à Dmg.",
        ]),
        ("note", "Exemple complet : 20 Wardens contre un guerrier en armure lourde",
         "20 figurines × 2 attaques = <b>40 dés</b>. Touche 3+ : environ 27 touches. Blessure 4+ : "
         "environ 13 blessures. La cible a Sv 3+ et vos piques ont Rend 0, donc elle sauve sur 3+ : il "
         "ne passe qu'environ 4 blessures à 1 dégât.<br/><br/>"
         "La même attaque avec le moteur runique : Varinor + Alaithi donnent <b>Anti-charge (+1 Rend)</b> "
         "si la cible a chargé — la sauvegarde passe à 4+, on double presque les dégâts. Et la "
         "<b>Crit (Mortal)</b> des piques transforme chaque 6 naturel au jet de touche (environ 6 dés "
         "sur 40) en dégât direct que ni la sauvegarde ni le Rend n'arrêtent. C'est là qu'est la vraie "
         "puissance des Wardens.", QUARTZ),

        ("h2", "Les critiques"),
        ("p", "Un <b>6 naturel</b> au jet de touche (avant tout modificateur) est un « critique ». Ce "
              "qu'il fait dépend du mot-clé inscrit sur l'arme :"),
        ("table", ["Mot-clé", "Effet du critique", "Où vous l'avez"], [
            ["Crit (Mortal)", "Inflige directement des <b>dégâts mortels</b> égaux à la caractéristique "
                              "Dmg. Ni sauvegarde, ni Rend — seul le Ward protège.",
             "Wardens, Dawnriders, Sevireth, Lyrior"],
            ["Crit (Auto-wound)", "La touche blesse automatiquement : on saute le jet de blessure.",
             "Sentinels, Windchargers"],
            ["Crit (2 Hits)", "La touche compte pour deux.", "Light of Eltharion (Fangsword)"],
        ], [30 * mm, 92 * mm, 56 * mm]),

        ("h2", "Les autres mots-clés d'arme"),
        ("table", ["Mot-clé", "Effet"], [
            ["Anti-X (+1 Rend)", "+1 de Rend contre les unités ayant le mot-clé X. Exemple : les arcs "
                                 "des Windchargers ont Anti-CAVALRY (+1 Rend)."],
            ["Charge (+1 Damage)", "+1 aux dégâts si l'unité a chargé <b>ce tour-ci</b>. En AoS 4, c'est "
                                   "la <b>seule</b> source de bonus de charge : il n'y a plus de bonus "
                                   "universel comme dans les éditions précédentes."],
            ["Anti-charge (+1 Rend)", "+1 de Rend contre une unité qui a chargé ce tour-ci."],
            ["Companion", "Arme de monture. Elle ignore les buffs amis qui modifient touche, blessure "
                          "ou caractéristiques — ne gaspillez pas un buff dessus."],
            ["Shoot in Combat", "L'arme de tir peut être utilisée même engagée au corps à corps."],
        ], [40 * mm, 138 * mm]),

        # ------------------------------------------------------------------
        ("section", "Le déroulement d'une manche"),
        ("lead", "Une partie dure 5 manches (« battle rounds »). Dans chaque manche, chaque joueur "
                 "joue un tour complet."),
        ("ol", [
            "<b>Début de manche.</b> Jet de priorité : le gagnant décide qui joue en premier "
            "(pas de jet à la manche 1, l'ordre découle du déploiement). C'est aussi ici que les "
            "Lumineth gravent leur rune.",
            "<b>Tour du premier joueur</b> : héros, mouvement, tir, charge, combat, fin de tour.",
            "<b>Tour du second joueur</b> : les mêmes six phases.",
            "<b>Score</b> : les points d'objectif se marquent à la fin de chaque tour.",
        ]),
        ("note", "Le « double tour »",
         "Comme la priorité est rejouée à chaque manche, votre adversaire peut finir la manche 2 puis "
         "commencer la manche 3 : deux tours d'affilée. C'est le plus grand danger du jeu. Avec des "
         "Lumineth, on s'en protège en gardant Alaithi (Ward 5+) et Realmshield disponibles, et en ne "
         "s'exposant jamais complètement au tour où l'on peut perdre la priorité.", BLOOD_RED),

        ("h2", "Les six phases d'un tour"),
        ("table", ["Phase", "Ce qui s'y passe"], [
            ["<b>1. Héros</b>", "Sorts, prières, capacités de héros, commande <i>Rally</i>. Le joueur "
                                "actif agit d'abord, puis son adversaire."],
            ["<b>2. Mouvement</b>", "Chaque unité peut faire un <i>Normal Move</i> (sa valeur de M), un "
                                    "<i>Run</i> (M + D6, mais plus de tir ni de charge), ou un "
                                    "<i>Retreat</i> (sortir du combat). On ne peut pas finir un "
                                    "mouvement normal dans la zone de combat d'un ennemi."],
            ["<b>3. Tir</b>", "Les unités avec une arme de tir attaquent. Être au corps à corps empêche "
                              "de tirer, sauf mot-clé <i>Shoot in Combat</i>."],
            ["<b>4. Charge</b>", "Jet de 2D6 pour une unité à moins de 12\" d'un ennemi ; si le résultat "
                                 "suffit à venir au contact, la charge réussit."],
            ["<b>5. Combat</b>", "Les joueurs <b>alternent</b> : le joueur actif active une unité, puis "
                                 "l'adversaire, et ainsi de suite. C'est le cœur tactique du jeu — et "
                                 "c'est exactement là qu'intervient votre formation."],
            ["<b>6. Fin de tour</b>", "Capacités de fin de tour, puis décompte des objectifs."],
        ], [26 * mm, 152 * mm]),

        # ------------------------------------------------------------------
        ("section", "Les commandes"),
        ("lead", "Vous gagnez <b>1 point de commandement (PC)</b> au début de chacun de vos tours "
                 "(plus 1 si vous êtes en retard au score). Chaque commande coûte 1 PC, et une même "
                 "unité ne peut recevoir qu'une commande par phase."),
        ("small", "Résumé en langage courant ; le texte exact se trouve dans le "
                  "<i>General's Handbook 2026-27</i>."),
        ("table", ["Commande", "Quand", "Effet"], [
            ["<b>All-out Attack</b>", "Réaction : une attaque vient d'être déclarée",
             "+1 aux jets de touche de cette unité."],
            ["<b>All-out Defence</b>", "Réaction : votre unité est prise pour cible",
             "+1 aux jets de sauvegarde de cette unité."],
            ["<b>At the Double</b>", "Phase de mouvement",
             "L'unité court automatiquement de 6\" au lieu de lancer le dé."],
            ["<b>Forward to Victory</b>", "Phase de charge", "Relance du jet de charge."],
            ["<b>Redeploy</b>", "Réaction : l'adversaire déclare un mouvement",
             "Une de vos unités hors combat se déplace de D6\". Sert à casser une charge."],
            ["<b>Covering Fire</b>", "Réaction, pendant le tour adverse",
             "Une de vos unités hors combat tire sur l'ennemi visible le plus proche, à -1 pour toucher."],
            ["<b>Power Through</b>", "Après avoir chargé",
             "Traverse une unité ennemie plus fragile en lui infligeant des dégâts mortels. La "
             "formation <i>Pilgrims of Haixiah</i> supprime la condition d'avoir chargé."],
            ["<b>Rally</b>", "Phase de héros, unité hors combat",
             "Jets de ralliement : chaque réussite permet de soigner ou de ramener une figurine."],
            ["<b>Magical Intervention</b>", "Phase de héros adverse",
             "Permet à un sorcier d'agir en dehors de son propre tour."],
        ], [34 * mm, 46 * mm, 98 * mm], {"bold_first": False}),
        ("note", "Vos deux commandes prioritaires",
         "<b>All-out Defence</b> sur les Wardens quand ils reçoivent la charge : combiné au Ward 5+ "
         "d'Alaithi, un bloc de 20 Wardens devient très difficile à déloger. <b>Redeploy</b> pour tirer "
         "une unité de D6\" hors d'une charge : les Lumineth gagnent en ne se faisant pas attraper.",
         QUARTZ),

        # ------------------------------------------------------------------
        ("section", "Les règles propres aux Lumineth"),
        ("h2", "Depict Rune — le seul trait de bataille"),
        ("p", "<b>Une fois par manche, au début de la manche, et c'est obligatoire.</b> Vous choisissez "
              "une des cinq runes et vous la gravez sur votre « battle scripture » — en pratique, une "
              "feuille de papier où vous notez les initiales : V, A, Y, O, T."),
        ("ul", [
            "La rune gravée <b>reste sur la scripture pour le reste de la partie</b>.",
            "Son <b>effet</b>, en revanche, ne dure que la manche où vous la gravez.",
            "Vous désignez <b>2 unités amies par instance</b> de cette rune déjà présente. Première "
            "gravure d'Alaithi : 2 cibles. Deuxième gravure d'Alaithi : 4 cibles.",
            "Les effets « harmonie » ne s'activent que si l'autre rune concernée est <b>déjà</b> gravée. "
            "D'où l'importance de l'ordre.",
            "Beaucoup de warscrolls lisent en permanence le nombre d'instances gravées : les Bladelords "
            "gagnent +1 Rend par Varinor, les Stoneguard passent en Sv 3+ à partir de 2 Alaithi, les "
            "Windchargers gagnent +6\" de portée à partir de 2 Oreali.",
        ]),
        ("table", ["Rune", "Effet de base (sur les cibles)", "Harmonies"], [
            ["<b>Varinor</b><br/>Force",
             "+1 aux jets de course et de charge.",
             "<b>+ Ydriliqi :</b> +1 aux jets de blessure en mêlée.<br/>"
             "<b>+ Oreali :</b> peut tirer et/ou charger même après une retraite."],
            ["<b>Alaithi</b><br/>Montagne",
             "Les cibles gagnent <b>WARD (5+)</b>.",
             "<b>+ Varinor :</b> armes de mêlée avec Anti-charge (+1 Rend).<br/>"
             "<b>+ Ydriliqi :</b> -1 aux jets de blessure ennemis contre les cibles."],
            ["<b>Ydriliqi</b><br/>Rivière",
             "-2 aux jets de charge des unités ennemies à 12\" des cibles.",
             "<b>+ Alaithi :</b> ignore les modificateurs négatifs de touche et de blessure.<br/>"
             "<b>+ Oreali :</b> mouvement de 3\" pouvant traverser les zones de combat."],
            ["<b>Oreali</b><br/>Vent",
             "-1 aux jets de touche des attaques de mêlée ennemies visant les cibles.",
             "<b>+ Varinor :</b> +4\" de Mouvement.<br/>"
             "<b>+ Alaithi :</b> +5 au score de contrôle."],
            ["<b>Thalari</b><br/>Zénith",
             "+2 aux jets d'incantation des Lumineth. <i>(effet d'armée, pas de cibles)</i>",
             "<b>Avec 4 runes uniques ou plus :</b> +4\" de Mouvement et critiques sur 5+ non modifiés, "
             "pour toute l'armée."],
        ], [26 * mm, 66 * mm, 86 * mm], {"bold_first": False}),
        ("note", "L'arbitrage à comprendre",
         "<b>Étaler</b> les cinq runes : vous cumulez les harmonies et vous déclenchez Thalari à la "
         "manche 5. <b>Empiler</b> la même rune : vous doublez le nombre de cibles et vous franchissez "
         "les seuils inscrits sur les warscrolls. Les listes mono-temple empilent ; les listes mixtes "
         "comme la vôtre étalent.", GOLD),
        ("p", "Trois héros donnent une <b>instance supplémentaire</b> d'une rune, uniquement pour les "
              "capacités inscrites sur les warscrolls des unités amies du bon temple à 12\" : "
              "<b>Lyrior</b> pour Varinor et les VANARI, <b>Sevireth</b> pour Oreali et les HURAKAN, "
              "<b>Avalenor</b> pour Alaithi et les ALARITH."),

        ("h2", "Les quatre formations de bataille"),
        ("table", ["Formation", "Capacité", "Pour qui"], [
            ["<b>Warhost of Duality</b>",
             "<i>Strike as One</i> : quand on alterne les activations en phase de combat, activez "
             "2 unités Lumineth au lieu d'une.",
             "Toute liste qui veut gagner un engagement précis. La plus jouée — et celle de votre liste."],
            ["<b>Pilgrims of Haixiah</b>",
             "<i>Trick of the Light</i> : les unités peuvent utiliser <i>Power Through</i> même sans "
             "avoir chargé.",
             "Les listes à esprits Hurakan, très mobiles."],
            ["<b>Scinari Council</b>",
             "<i>Arcane Focus</i> : les sorts des lores de Hysh et des Awakened Realms deviennent "
             "UNLIMITED, sans viser deux fois la même unité dans le tour.",
             "Les listes à quatre lanceurs ou plus."],
            ["<b>Aelementor Guardians</b>",
             "<i>Ancient Spirits</i> : une fois par tour, ignorez le premier dégât par phase sur chaque "
             "unité amie à 12\" d'un de vos monstres.",
             "Les listes Avalenor / Spirit of the Mountain."],
        ], [36 * mm, 82 * mm, 60 * mm], {"bold_first": False}),

        ("h2", "Traits héroïques — un seul, pour un général non-UNIQUE"),
        ("table", ["Groupe", "Trait", "Effet"], [
            ["Facets of Brilliance", "<b>Flawless Commander</b>",
             "<b>Phase de déploiement.</b> Jusqu'à 3 unités d'infanterie Lumineth visibles à 18\" font "
             "un mouvement normal. <i>C'est celui de votre liste.</i>"],
            ["Facets of Brilliance", "Acolyte of the Runes",
             "Début de manche : un héros ami à 12\" devient une cible supplémentaire de Depict Rune."],
            ["Facets of Brilliance", "Masterful Tactician",
             "Sur un Redeploy déclaré pour une unité à 12\", un résultat de 1 à 3 compte comme 4."],
            ["Aspects of Enlightenment", "Flawless Commander",
             "Passif : +2\" de Mouvement à l'infanterie Lumineth à 12\"."],
            ["Aspects of Enlightenment", "Martial Perfectionist",
             "Phase de combat : sur 3+, +1 aux blessures de l'infanterie Lumineth contre une unité "
             "ennemie déjà endommagée à 12\"."],
            ["Aspects of Enlightenment", "Aetherquartz Requisitioner",
             "Une fois par bataille : +3 à un jet d'incantation d'un sorcier au contact."],
        ], [40 * mm, 44 * mm, 94 * mm], {"bold_first": False}),

        ("h2", "Artefacts — Heirlooms of Hysh"),
        ("table", ["Artefact", "Effet"], [
            ["<b>Phoenix Stone</b>", "La première fois que l'unité serait détruite, sur 3+ elle survit, "
                                     "les dégâts restants sont annulés, et elle récupère D3 PV."],
            ["<b>Silver Wand</b>", "Un non-sorcier peut utiliser <i>Unbind</i> comme un WIZARD (1) ; un "
                                   "sorcier gagne +1 aux jets d'incantation."],
            ["<b>Waystone</b>", "Phase de mouvement : l'unité est retirée et redéployée entièrement dans "
                                "votre territoire, à plus de 9\" de tout ennemi."],
        ], [36 * mm, 142 * mm]),

        ("h2", "Les trois lores de sorts"),
        ("table", ["Lore", "Sort", "Effet"], [
            ["<b>Awakened Realms</b><br/><i>(choisi ici)</i>", "Realmshield",
             "Les unités Lumineth entièrement à 12\" du lanceur ont <b>WARD (5+)</b> jusqu'au début de "
             "votre prochain tour. Le meilleur sort défensif de la faction."],
            ["", "Focused Erosion", "-1 au Rend des armes d'une unité ennemie à 18\"."],
            ["", "Elemental Push", "Une unité amie se déplace de 5\", peut traverser les zones de combat "
                                   "mais ne peut pas finir au contact."],
            ["<b>Lore of Hysh</b>", "Beacon of Hysh",
             "Les attaques visant l'unité ciblée échouent sur un jet de touche naturel de 1 à 3."],
            ["", "Overwhelming Heat", "Mouvement de la cible divisé par deux, plus D3 dégâts mortels si "
                                      "le dé égale ou dépasse sa sauvegarde."],
            ["", "Piercing Refraction", "Un dé par figurine de la cible ; 1 dégât mortel par 5+."],
            ["<b>Prismatic<br/>Resonance</b>", "Beam of Hysh",
             "D3 dégâts mortels, +1 par lancement précédent du sort dans le tour (max +3). Se cumule "
             "entre plusieurs sorciers."],
            ["", "Unseen Force", "La cible ne peut plus courir ; si elle a déjà été ciblée dans la "
                                 "manche, -1 à ses jets de touche en mêlée."],
            ["", "Beacons of Protection", "Ignore le premier dégât par phase sur les unités non-MONSTER "
                                          "à 9\" d'un sorcier ami ; +3\" de portée par lancement "
                                          "supplémentaire."],
        ], [36 * mm, 34 * mm, 108 * mm], {"bold_first": False}),

        ("h2", "Le terrain de faction : Shrine Luminor (gratuit)"),
        ("ul", [
            "<b>Enter the Shrine</b> : un héros d'infanterie Lumineth à 3\" monte dessus et devient "
            "« Shrine Guardian ».",
            "Tant qu'il a un gardien, le sanctuaire <b>se déplace de 6\"</b> comme une unité et permet "
            "de relancer le jet d'incantation du gardien.",
            "<b>Exit the Shrine</b> : le gardien redescend en phase de mouvement, à 6\" du sanctuaire.",
        ]),

        ("section", "Vos warscrolls, un par un"),
        ("lead", "Profils issus de l'export Wahapedia du 26/05/2026. « A » = attaques par figurine."),
    ]

    units = [
        ("Scinari Cathallar — 130 pts — votre général",
         "M6\"  ·  Sv 6+  ·  Contrôle 2  ·  5 PV  ·  WIZARD (1)",
         [["Despairing Touch (mêlée)", "3 A", "3+", "4+", "-", "D3", ""]],
         ["<b>Darkness of the Soul</b> (phase de héros) : une unité ennemie visible à 18\" ; sur 3+, "
          "elle ne peut plus utiliser de commandement jusqu'à votre prochain tour.",
          "<b>Comment le jouer :</b> il reste au centre, derrière les Wardens. Il lance Realmshield, il "
          "coupe le commandement le plus dangereux du tour, et il ne combat jamais. Son trait "
          "<i>Flawless Commander</i> se joue une seule fois, au déploiement."]),

        ("Vanari Auralan Wardens — 120 pts (10 fig.) / 240 pts (20 fig.)",
         "M6\"  ·  Sv 4+  ·  Contrôle 1  ·  1 PV par figurine",
         [["Warden Pike and Blade (mêlée)", "2 A", "3+", "4+", "-", "1",
           "Anti-charge (+1 Rend), Crit (Mortal)"]],
         ["<b>Anticipated Strike</b> : si l'unité n'a pas chargé ce tour-ci, elle annule l'effet "
          "<i>Charge (+1 Damage)</i> des attaques ennemies qui la visent.",
          "<b>Comment les jouer :</b> ils ne chargent pas, ils reçoivent. Placez-les sur l'objectif, "
          "gravez Alaithi pour le Ward 5+, dépensez All-out Defence, et laissez la cavalerie adverse se "
          "briser dessus. Les 6 naturels font des dégâts mortels : sur 40 dés, cela compte."]),

        ("Ydrilan Riverblades — 140 pts (10 fig.)",
         "M7\"  ·  Sv 5+  ·  Contrôle 1  ·  1 PV par figurine",
         [["Ythara Darts (tir 10\")", "2 A", "3+", "4+", "-", "1", "Shoot in Combat"],
          ["Ydrilan Blades (mêlée)", "2 A", "3+", "4+", "1", "1", ""]],
         ["<b>Travel The Waterways</b> (phase de mouvement) : l'unité est retirée et redéployée "
          "entièrement à 6\" d'un bord de table, à plus de 9\" de tout ennemi. La manche où vous gravez "
          "Ydriliqi, elle peut se poser <b>n'importe où</b> à plus de 9\".",
          "<b>Relentless as the Driving Current</b> (phase de combat) : si elle est au contact, elle se "
          "déplace de 2D6\" en traversant les figurines ennemies, mais doit finir au contact.",
          "<b>Comment les jouer :</b> c'est un outil de score, pas un combattant. Ils vont chercher "
          "l'objectif que personne ne garde, ou débordent un flanc au dernier tour."]),

        ("The Light of Eltharion — 300 pts",
         "M6\"  ·  Sv 3+  ·  Contrôle 2  ·  7 PV  ·  <b>WARD (4+)</b>  ·  UNIQUE",
         [["Searing Darts of Light (tir 12\")", "3 A", "2+", "3+", "2", "D3", "Shoot in Combat"],
          ["Fangsword of Eltharion (mêlée)", "5 A", "2+", "3+", "3", "3", "Crit (2 Hits)"],
          ["Celennari Blade (mêlée)", "2 A", "2+", "3+", "1", "3", "Anti-HERO / Anti-MONSTER (+1 Rend)"]],
         ["<b>Supreme Swordmaster</b> : ignore tous les modificateurs négatifs à ses jets de touche et "
          "de blessure.",
          "<b>Valorous Intervention</b> (phase de combat, s'il n'est pas engagé) : il est retiré et "
          "replacé au contact d'une unité amie déjà engagée. C'est un téléport de combat.",
          "<b>Comment le jouer :</b> c'est l'unité la plus rentable de la faction (85e percentile "
          "toutes armées confondues). Ward 4+, Sv 3+, Rend 3 : il tue les héros et les monstres. "
          "Gardez-le légèrement en retrait la manche 1, puis servez-vous de <i>Valorous Intervention</i> "
          "pour arriver là où l'engagement se décide."]),

        ("Lyrior Uthralle, Warden of Ymetrica — 250 pts",
         "M14\"  ·  Sv 3+  ·  Contrôle 2  ·  7 PV  ·  WIZARD  ·  UNIQUE",
         [["Daemonbane (mêlée)", "2 A", "2+", "3+", "1", "2", "Anti-DAEMON (+1 Rend), Charge (+1 Dmg)"],
          ["Lyrior's Sword (mêlée)", "5 A", "2+", "3+", "1", "2", "Charge (+1 Dmg), Crit (Mortal)"],
          ["Farael's Horns and Claws (mêlée)", "4 A", "4+", "3+", "1", "1", "Companion"]],
         ["<b>Champion of the Lord Phoenix</b> : les unités VANARI amies visibles à 12\" comptent une "
          "instance supplémentaire de Varinor pour leurs propres capacités.",
          "<b>Focused Fury</b> (phase de héros) : jet de 2D6, +2 s'il est au contact ; il gagne "
          "STRIKE-FIRST pour le tour.",
          "<b>Comment le jouer :</b> il escorte les Dawnriders. Ses deux armes ont <i>Charge "
          "(+1 Damage)</i> : il ne vaut le coup qu'en chargeant. STRIKE-FIRST plus Warhost of Duality "
          "permet de frapper deux fois avant que l'adversaire n'active quoi que ce soit."]),

        ("Vanari Dawnriders — 180 pts (5 fig.)",
         "M14\"  ·  Sv 4+  ·  Contrôle 1  ·  3 PV par figurine",
         [["Dawnrider Lance and Blade (mêlée)", "2 A", "3+", "4+", "1", "1",
           "Charge (+1 Dmg), Crit (Mortal)"],
          ["Stallions' Dashing Hooves (mêlée)", "2 A", "5+", "3+", "-", "1", "Companion"]],
         ["<b>Dawnrider Charge</b> : +1 de Rend aux lances si l'unité a chargé ce tour-ci.",
          "<b>Comment les jouer :</b> leur profil ne vaut que chargé — Rend 2 et 2 dégâts par lance. "
          "Avec Varinor gravée (+1 à la charge) et la commande <i>Forward to Victory</i>, une charge de "
          "9\" devient fiable. Ne les envoyez jamais sur un bloc d'infanterie lourde : ils sont là pour "
          "les unités de soutien et les flancs."]),

        ("Hurakan Windchargers — 160 pts (5 fig.)",
         "M14\"  ·  Sv 4+  ·  Contrôle 1  ·  3 PV par figurine",
         [["Windcharger Bow (tir 12\")", "3 A", "3+", "4+", "1", "1",
           "Anti-CAVALRY (+1 Rend), Crit (Auto-wound)"],
          ["Windcharger Blade (mêlée)", "1 A", "4+", "4+", "-", "1", ""],
          ["Treerunner's Claws (mêlée)", "2 A", "5+", "3+", "-", "1", "Companion"]],
         ["<b>Guided by the Winds</b> : à partir de <b>2 instances d'Oreali</b> gravées, +6\" de portée "
          "aux arcs (18\" au lieu de 12\").",
          "<b>Comment les jouer :</b> 15 tirs à 3+/4+ avec auto-blessure sur les 6, et 14\" de "
          "mouvement. Ils chassent les petites unités de soutien et les héros à pied, jamais un bloc "
          "d'élite. Gardez-les à 12\" de Sevireth pour son instance d'Oreali."]),

        ("Sevireth, Lord of the Seventh Wind — 340 pts",
         "M18\"  ·  Sv 4+  ·  Contrôle 5  ·  10 PV  ·  <b>WARD (5+)</b>  ·  MONSTER  ·  UNIQUE",
         [["Enathrai, the Howling Death (tir 15\")", "4 A", "2+", "3+", "3", "3", "Shoot in Combat"],
          ["Swirling Shards (mêlée)", "6 A", "2+", "4+", "-", "1", "Crit (Mortal)"]],
         ["<b>Call of the Winds</b> : les unités HURAKAN amies à 12\" comptent une instance "
          "supplémentaire d'Oreali.",
          "<b>Spirit of the Wind</b> : s'il a tiré ce tour-ci, il se déplace de D6\", +2\" par instance "
          "d'Oreali gravée. Il ne peut pas finir au contact.",
          "<b>Searing Desert Winds</b> (phase de combat) : jusqu'à 3 unités ennemies à 6\" ; un D3 "
          "chacune, sur 2+ dégâts mortels égaux au résultat, et -1 à leurs jets de blessure pour le tour.",
          "<b>Comment le jouer :</b> 18\" de mouvement, tir Rend 3 utilisable au contact, puis un "
          "mouvement gratuit après avoir tiré. Il ne tient pas un objectif face à une vraie unité : il "
          "tire, il recule, et il va prendre l'objectif que l'adversaire a laissé vide."]),

        ("Vanari Auralan Sentinels — 140 pts (10 fig.)",
         "M6\"  ·  Sv 5+  ·  Contrôle 1  ·  1 PV par figurine",
         [["Auralan Bow (tir 18\")", "2 A", "3+", "4+", "1", "1", "Crit (Auto-wound)"],
          ["Sentinel Blade (mêlée)", "1 A", "3+", "4+", "-", "1", ""]],
         ["<b>Lofted Shots</b> : +6\" de portée (24\") mais -1 pour toucher, pour le reste du tour.",
          "<b>Comment les jouer :</b> 20 tirs par tour. Ils restent en arrière sur un objectif de votre "
          "moitié de table et usent les unités de soutien. À 5+ de sauvegarde et 1 PV, ils fondent au "
          "moindre contact — ne les laissez jamais à portée de charge."]),
    ]

    for name, profile, weapons, notes in units:
        sub = [
            ("h2", name),
            ("p", f"<i>{profile}</i>"),
            ("table", ["Arme", "A", "Touche", "Bless.", "Rend", "Dégâts", "Mots-clés"],
             weapons, [48 * mm, 10 * mm, 15 * mm, 15 * mm, 12 * mm, 16 * mm, 62 * mm],
             {"align_right": (1, 2, 3, 4, 5)}),
        ]
        sub += [("p", n) for n in notes]
        blocks.append(("keep", sub))
        blocks.append(("spacer", 3))

    blocks += [
        ("section", "Petit glossaire anglais / français"),
        ("table", ["Terme anglais", "Traduction", "Précision"], [
            ["Battle round", "Manche", "Une manche = un tour pour chacun des deux joueurs."],
            ["Turn", "Tour", "Les six phases d'un seul joueur."],
            ["Warscroll", "Fiche d'unité", "Le profil et les capacités d'une unité."],
            ["Regiment", "Régiment", "1 héros + jusqu'à 3 autres unités, déployés ensemble."],
            ["Drop", "Vague de déploiement", "Un régiment posé sur la table. Moins de drops = vous "
                                             "choisissez plus souvent qui commence."],
            ["Reinforced", "Renforcée", "Unité au double de sa taille et de son coût. Vos Wardens à "
                                        "20 figurines sont une unité renforcée."],
            ["Control score", "Score de contrôle", "Somme des Contrôle des figurines qui contestent "
                                                   "un objectif."],
            ["Ward", "Protection", "Seconde sauvegarde, insensible au Rend."],
            ["Rend", "Pénétration", "Se soustrait à la sauvegarde adverse."],
            ["Mortal damage", "Dégâts mortels", "Ignorent la sauvegarde et le Rend, mais pas le Ward."],
            ["Strike-first / Strike-last", "Frappe en premier / en dernier",
             "Modifie l'ordre d'activation en phase de combat."],
            ["Combat range", "Zone de combat", "3\" autour d'une figurine."],
            ["Unbind", "Dissiper", "Tentative d'annuler un sort adverse avec un sorcier."],
            ["Manifestation", "Manifestation", "Une « figurine-sort » invoquée sur la table."],
            ["Battle tactic", "Tactique de bataille", "Objectif secondaire choisi avant la partie, 5 PV."],
            ["Unique", "Unique", "Personnage nommé : un seul exemplaire, et ni artefact ni trait héroïque."],
        ], [42 * mm, 40 * mm, 96 * mm]),

        ("box", "Note d'exactitude",
         "Les profils, capacités de warscroll, runes, formations, traits, artefacts et sorts de ce "
         "document sont repris de l'export Wahapedia présent dans le dépôt (mise à jour du 26/05/2026). "
         "Les <b>commandes universelles</b> et les règles générales du jeu sont en revanche résumées en "
         "langage courant à partir de sources secondaires : en cas de désaccord en partie, le texte du "
         "<i>General's Handbook 2026-27</i> et du livre de règles fait foi."),
    ]

    return build_document(
        "02_Lumineth_regles_expliquees.pdf",
        "Lumineth Realm-lords — Les règles expliquées",
        "Le Livre des Néophytes",
        "Comprendre Age of Sigmar et les Lumineth Realm-lords en partant de zéro",
        [
            "<b>Ce document part du principe que vous n'avez jamais joué.</b> Il explique d'abord "
            "comment on gagne une partie d'Age of Sigmar, comment on lit une fiche d'unité et comment "
            "se résout une attaque, puis il détaille les règles propres aux Lumineth : le moteur "
            "runique, les formations, les traits, les artefacts et les sorts.",
            "<b>La dernière partie</b> reprend, une par une, les dix unités de votre liste : profil "
            "complet, capacités traduites, et une consigne de jeu pour chacune.",
            "Lisez-le une fois en entier, puis gardez la fiche « Déroulement d'un tour » à côté de vous "
            "pendant la partie.",
        ],
        "LUMINETH REALM-LORDS  ·  LES RÈGLES EXPLIQUÉES",
        blocks,
        cover_footer="Fiche II sur IV — Compendium Lumineth",
    )
