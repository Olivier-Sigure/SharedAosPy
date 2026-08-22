"""Fiche IV — Stratégies : par type d'adversaire et par type de scénario."""
from __future__ import annotations

from reportlab.lib.units import mm

from lumineth_pdf_kit import build_document, CONTENT_W, GOLD, BLOOD_RED, QUARTZ, BLOOD_GREEN

W = CONTENT_W


def build():
    blocks = [
        ("section_here", "Rappel : qui sont les Lumineth"),
        ("lead", "Avant toute stratégie, il faut accepter l'identité de la faction. Les chiffres du "
                 "dépôt sont sans ambiguïté : en rendement de combat brut, Lumineth est <b>20e sur "
                 "25 armées</b>. Vous ne gagnerez pas l'échange de dégâts. Vous gagnerez au placement, "
                 "au ward et au score."),

        ("h2", "Vos cinq forces réelles"),
        ("table", ["Force", "D'où elle vient", "Comment on s'en sert"], [
            ["<b>Résistance empilable</b>",
             "Ward 5+ (Alaithi), Ward 5+ (Realmshield), All-out Defence, Anticipated Strike, "
             "-1 pour toucher (Oreali).",
             "Une seule unité peut cumuler trois couches défensives sur une manche. Choisissez "
             "laquelle et tenez le point avec."],
            ["<b>Double activation</b>",
             "<i>Strike as One</i> (Warhost of Duality).",
             "Tuer une unité avant qu'elle ne réplique. C'est votre seul vrai outil de « burst »."],
            ["<b>Mobilité asymétrique</b>",
             "Sevireth M18\", Riverblades téléport, Windchargers M14\", Flawless Commander au "
             "déploiement.",
             "Vous arrivez sur les objectifs faibles avant l'adversaire, et vous refusez les "
             "engagements que vous perdez."],
            ["<b>Déni de commandement</b>",
             "<i>Darkness of the Soul</i> du Cathallar, tous les tours, gratuitement.",
             "Annuler le All-out Attack, le contre-charge ou le Redeploy qui aurait fait basculer "
             "l'engagement."],
            ["<b>Montée en puissance</b>",
             "La scripture accumule les runes ; Thalari récompense la manche 5.",
             "Vous êtes plus fort à la manche 4 qu'à la manche 1. Survivez au début, gagnez la fin."],
        ], [36 * mm, 70 * mm, 72 * mm], {"bold_first": False}),

        ("h2", "Vos trois faiblesses structurelles"),
        ("ul", [
            "<b>Peu de dégâts par point investi.</b> Seul le Light of Eltharion est au-dessus de la "
            "moyenne du jeu. Ne cherchez jamais un échange frontal contre une unité d'élite.",
            "<b>Fragilité des unités de tir.</b> Sentinels : sauvegarde 5+, 1 PV. Une seule charge "
            "réussie les efface.",
            "<b>Peu de magie.</b> Deux lanceurs seulement. Contre une armée à quatre sorciers, vous "
            "ne gagnerez pas la guerre magique — protégez juste Realmshield.",
        ]),

        # ------------------------------------------------------------------
        ("section", "Le plan de base, manche par manche"),
        ("lead", "Ce plan fonctionne contre la majorité des adversaires. Les pages suivantes indiquent "
                 "quand s'en écarter."),
        ("table", ["Manche", "Objectif de la manche", "Ce que vous faites"], [
            ["<b>1</b>", "Occuper sans s'exposer",
             "Gravez Varinor. Flawless Commander a déjà avancé trois unités au déploiement. Prenez les "
             "objectifs de votre moitié, restez à plus de 12\" de tout ce qui charge. Les Sentinels "
             "tirent. Riverblades en attente."],
            ["<b>2</b>", "Bloquer l'assaut",
             "Gravez Ydriliqi (-2 aux charges ennemies autour des Wardens, +1 aux blessures via "
             "Varinor). Téléportez les Riverblades sur un objectif non gardé. Realmshield sur le bloc."],
            ["<b>3</b>", "Encaisser et tenir",
             "Gravez Alaithi : Ward 5+, Anti-charge (+1 Rend) et -1 aux blessures ennemies. C'est la "
             "manche où l'adversaire vient au contact — et où il doit s'y casser les dents."],
            ["<b>4</b>", "Reprendre le terrain",
             "Gravez Oreali : -1 pour toucher, +4\" de Mouvement, +5 au contrôle. C'est votre fenêtre "
             "offensive : Strike as One sur l'engagement décisif, Dawnriders sur un flanc."],
            ["<b>5</b>", "Marquer le maximum",
             "Gravez Thalari : +4\" de Mouvement et critiques sur 5+ pour toute l'armée. Riverblades et "
             "Sevireth vont chercher les derniers objectifs. Ne prenez aucun risque inutile."],
        ], [16 * mm, 40 * mm, 122 * mm], {"bold_first": False}),

        # ------------------------------------------------------------------
        ("section", "Stratégie par type d'adversaire"),
        ("lead", "Six archétypes couvrent la quasi-totalité du jeu. Identifiez celui d'en face au "
                 "déploiement, et adaptez la gravure."),

        ("h2", "1. L'élite lente et dure"),
        ("p", "<i>Stormcast Eternals, Ossiarch Bonereapers, Slaves to Darkness, Maggotkin of Nurgle, "
              "Fyreslayers.</i> Peu de figurines, très bonnes sauvegardes, souvent un ward."),
        ("table", ["Point", "Analyse et consigne"], [
            ["<b>La menace</b>", "Ils encaissent tout ce que vous leur envoyez et gagnent l'échange sur "
                                 "la durée. Vos Wardens n'ont pas de Rend : contre une sauvegarde 3+, "
                                 "ils ne font presque rien."],
            ["<b>Gravure</b>", "Varinor tôt (pour l'harmonie Anti-charge d'Alaithi), puis Alaithi. "
                               "Le +1 aux blessures Varinor+Ydriliqi vaut plus que la mobilité ici."],
            ["<b>Qui fait quoi</b>", "Le Light of Eltharion est votre seule vraie réponse : Rend 3, "
                                     "Anti-HERO et Anti-MONSTER. Envoyez-le sur leur pièce maîtresse "
                                     "avec Strike as One. Les Wardens bloquent, ils ne tuent pas."],
            ["<b>Erreur à éviter</b>", "Engager le bloc principal. Vous perdrez. Bloquez-le avec les "
                                       "Wardens et allez marquer ailleurs avec le reste."],
        ], [30 * mm, 148 * mm]),

        ("h2", "2. La horde"),
        ("p", "<i>Skaven, Gloomspite Gitz, Flesh-eater Courts, Kruleboyz, Nighthaunt.</i> "
              "Beaucoup de figurines, peu de résistance individuelle, gros scores de contrôle."),
        ("table", ["Point", "Analyse et consigne"], [
            ["<b>La menace</b>", "Ils vous noient au contrôle et vous submergent par le nombre "
                                 "d'attaques. Le danger n'est pas la qualité, c'est le volume."],
            ["<b>Gravure</b>", "Alaithi tôt (Ward 5+ contre un grand nombre d'attaques faibles), puis "
                               "Oreali (-1 pour toucher, ce qui coûte énormément à une horde)."],
            ["<b>Qui fait quoi</b>", "Sentinels et Windchargers font leur meilleur travail : leurs "
                                     "critiques auto-blessants tuent les figurines à 1 PV. Les Wardens "
                                     "avec Crit (Mortal) sur 40 dés font des ravages."],
            ["<b>Erreur à éviter</b>", "Se laisser encercler. Une horde gagne quand elle peut vous "
                                       "engager de trois côtés — gardez un flanc contre un décor."],
        ], [30 * mm, 148 * mm]),

        ("h2", "3. L'alpha rapide"),
        ("p", "<i>Daughters of Khaine, Hedonites of Slaanesh, Blades of Khorne, Idoneth Deepkin, "
              "Ironjawz.</i> Beaucoup de mouvement, frappe au tour 1 ou 2, souvent STRIKE-FIRST."),
        ("table", ["Point", "Analyse et consigne"], [
            ["<b>La menace</b>", "Ils vous atteignent avant que votre scripture ne soit montée en "
                                 "puissance. Une charge de la manche 1 sur les Sentinels et vous perdez "
                                 "140 points sans rien faire."],
            ["<b>Gravure</b>", "Ydriliqi dès la manche 1 (-2 aux jets de charge à 12\" des cibles) : "
                               "c'est la meilleure défense anti-alpha du jeu. Alaithi en manche 2."],
            ["<b>Qui fait quoi</b>", "Les Wardens sont le mur : Anticipated Strike annule leur "
                                     "<i>Charge (+1 Damage)</i>. <b>Redeploy</b> pour sortir les "
                                     "Sentinels de la zone de charge. Darkness of the Soul sur leur "
                                     "unité de tête."],
            ["<b>Erreur à éviter</b>", "Déployer en avant à la manche 1. Contre un alpha, vous "
                                       "commencez en retrait et vous laissez venir : votre courbe de "
                                       "puissance monte, la leur descend."],
        ], [30 * mm, 148 * mm]),

        ("h2", "4. Les monstres et les géants"),
        ("p", "<i>Sons of Behemat, Ogor Mawtribes, Seraphon à dinosaures, Stormdrakes.</i> "
              "Peu d'unités, énormément de points de vie chacune."),
        ("table", ["Point", "Analyse et consigne"], [
            ["<b>La menace</b>", "Sons of Behemat est la seule armée du jeu au rendement de combat "
                                 "franchement positif dans les résultats chargés (+11,6 % de ROI "
                                 "médian). Une seule figurine peut effacer un bloc."],
            ["<b>Gravure</b>", "Oreali tôt (-1 pour toucher fait très mal à une unité qui a peu "
                               "d'attaques mais des dégâts énormes), puis Alaithi."],
            ["<b>Qui fait quoi</b>", "Le Light of Eltharion (Anti-MONSTER +1 Rend, donc Rend 2 sur la "
                                     "Celennari Blade) et Sevireth (Rend 3 à distance). Les Windchargers "
                                     "n'y peuvent rien : envoyez-les marquer ailleurs."],
            ["<b>Erreur à éviter</b>", "Nourrir le monstre. Peu d'unités en face = peu de couverture : "
                                       "il y a toujours deux objectifs vides à prendre pendant qu'il "
                                       "mange un bloc de Wardens."],
        ], [30 * mm, 148 * mm]),

        ("h2", "5. Le tir lourd"),
        ("p", "<i>Kharadron Overlords, Cities of Sigmar, Seraphon, autres Lumineth.</i>"),
        ("table", ["Point", "Analyse et consigne"], [
            ["<b>La menace</b>", "Vous êtes plus lents qu'eux et vos unités de tir sont plus fragiles. "
                                 "Un duel à distance est perdu d'avance."],
            ["<b>Gravure</b>", "Alaithi et Oreali. Attention : Oreali ne réduit que les jets de touche "
                               "des attaques <b>de mêlée</b> — contre du tir, c'est le Ward qui compte."],
            ["<b>Qui fait quoi</b>", "Foncez. Varinor (+1 à la course et à la charge) et le mouvement "
                                     "du déploiement de Flawless Commander. Sevireth va tuer leurs "
                                     "héros de soutien : il est plus rapide que tout ce qu'ils ont."],
            ["<b>Erreur à éviter</b>", "Rester à couvert et échanger des tirs. Vous perdrez la course "
                                       "aux points en restant chez vous."],
        ], [30 * mm, 148 * mm]),

        ("h2", "6. La magie lourde"),
        ("p", "<i>Disciples of Tzeentch, Seraphon, Nighthaunt, Soulblight Gravelords.</i>"),
        ("table", ["Point", "Analyse et consigne"], [
            ["<b>La menace</b>", "Les dégâts mortels traversent vos sauvegardes. Ils sont en revanche "
                                 "arrêtés par le Ward — d'où l'importance d'Alaithi et de Realmshield."],
            ["<b>Gravure</b>", "Alaithi en priorité, et Thalari plus tôt que d'habitude (+2 aux "
                               "incantations : cela améliore vos chances de dissiper)."],
            ["<b>Qui fait quoi</b>", "Vos deux sorciers servent surtout à dissiper. Le Cathallar coupe "
                                     "les commandements ; contre Tzeentch, visez leur unité de "
                                     "manipulation du destin."],
            ["<b>Erreur à éviter</b>", "Regrouper toute l'armée. Les sorts de zone adorent les paquets "
                                       "serrés — espacez, sauf quand Realmshield est en jeu."],
        ], [30 * mm, 148 * mm]),

        ("h2", "Repère chiffré : quelles armées gagnent l'échange de dégâts"),
        ("p", "ROI médian par armée, tous duels confondus (résultats AoSPy chargés, 722 unités). "
              "Plus le chiffre est haut, plus l'armée est efficace point pour point — donc plus il faut "
              "éviter l'échange frontal."),
        ("table", ["Armées à ne jamais affronter de face", "ROI médian", "Armées que vous pouvez engager",
                   "ROI médian"], [
            ["Sons of Behemat", "+11,6 %", "Ossiarch Bonereapers", "-12,1 %"],
            ["Stormcast Eternals", "+3,7 %", "Flesh-eater Courts", "-13,8 %"],
            ["Sylvaneth", "+0,8 %", "Soulblight Gravelords", "-14,5 %"],
            ["Maggotkin of Nurgle", "-1,0 %", "<i>Lumineth Realm-lords</i>", "<i>-15,1 %</i>"],
            ["Ironjawz", "-2,5 %", "Fyreslayers", "-15,2 %"],
            ["Skaven", "-3,1 %", "Idoneth Deepkin", "-19,8 %"],
            ["Blades of Khorne", "-4,6 %", "Cities of Sigmar", "-20,2 %"],
            ["Gloomspite Gitz", "-4,8 %", "Nighthaunt", "-25,6 %"],
            ["Kharadron Overlords", "-7,5 %", "Disciples of Tzeentch", "-33,3 %"],
        ], [58 * mm, 26 * mm, 66 * mm, 28 * mm], {"align_right": (1, 3), "bold_first": False}),
        ("small", "Rappel : ce classement ne mesure que les dégâts. Une armée basse dans cette colonne "
                  "peut parfaitement vous battre au score — Nighthaunt et Tzeentch en sont les meilleurs "
                  "exemples."),

        # ------------------------------------------------------------------
        ("section", "Stratégie par type de scénario"),
        ("lead", "Le General's Handbook 2026-27 propose douze battleplans. Ils se ramènent à quatre "
                 "formes de carte, et c'est la forme qui dicte votre plan."),

        ("table", ["Forme de carte", "Ce qu'elle demande", "Votre plan Lumineth"], [
            ["<b>Objectifs centraux</b><br/>(un ou deux points au milieu)",
             "Une bagarre frontale prolongée, souvent décidée à la manche 3.",
             "C'est votre meilleur cas. Le bloc de 20 Wardens s'installe sur le point central avec "
             "Alaithi, Realmshield et All-out Defence. Tout le reste tourne autour. Gravez Ydriliqi "
             "puis Alaithi tôt."],
            ["<b>Objectifs dispersés</b><br/>(quatre à six points répartis)",
             "De la mobilité et de la présence simultanée en plusieurs endroits.",
             "Votre deuxième meilleur cas. Riverblades, Sevireth et Windchargers prennent trois points "
             "à eux seuls. Gravez Varinor puis Oreali. Ne concentrez pas l'armée."],
            ["<b>Objectifs en territoire adverse</b><br/>(il faut avancer)",
             "Aller chercher les points chez l'ennemi, donc s'exposer.",
             "Votre cas le plus difficile. Utilisez Flawless Commander au déploiement, Varinor manche 1, "
             "et le téléport des Riverblades manche 2 avec Ydriliqi. Sevireth part seul sur le flanc."],
            ["<b>Objectifs mobiles ou changeants</b><br/>(le point actif change de manche en manche)",
             "De la réactivité et des unités capables de se redéployer.",
             "Excellent pour vous. Gardez les Riverblades en réserve le plus longtemps possible et "
             "réservez Elemental Push et Oreali (+4\" de Mouvement) pour la manche où le point bouge."],
        ], [42 * mm, 54 * mm, 82 * mm], {"bold_first": False}),

        ("note", "Les douze battleplans de la saison 2026-27",
         "<i>Into the Fire · Bloodstained Coasts · Avalanche of Ash · Caverns of Slaughter · What's "
         "Yours Is Ours · Hidden Under Ash-Clouds · Warped Ruins · Curse of the Gnaw · Seize the Embers "
         "· Treacherous Ground · Escape from the Coast · Power of the Realms.</i><br/><br/>"
         "Lisez toujours en premier <b>combien d'objectifs</b> et <b>où</b> : c'est cela qui détermine "
         "votre plan, pas le nom du scénario.", GOLD),

        ("h2", "Choisir ses battle tactics"),
        ("p", "Vous choisissez deux cartes pendant la composition d'armée. Chaque carte se joue dans "
              "l'ordre Affray, puis Strike, puis Domination. Avec cette liste :"),
        ("ul", [
            "<b>Privilégiez les tactiques de contrôle et de position</b> plutôt que celles qui exigent "
            "de détruire une unité précise. Votre armée occupe bien, elle tue mal.",
            "<b>Les tactiques « tuer un héros »</b> sont jouables uniquement grâce au Light of "
            "Eltharion (Anti-HERO +1 Rend) et à Sevireth. Prévoyez-les pour la manche 3 ou 4, quand "
            "votre scripture est montée.",
            "<b>Les tactiques « être dans le territoire adverse »</b> sont faciles pour vous : les "
            "Riverblades se téléportent, Sevireth a 18\" de mouvement.",
            "Attention : si vous saisissez l'initiative (double tour), vous ne pouvez compléter aucune "
            "battle tactic ce tour-là.",
        ]),

        ("h2", "Déploiement et priorité"),
        ("ul", [
            "<b>Quatre régiments, donc quatre drops.</b> C'est peu : vous aurez souvent le choix de "
            "qui commence.",
            "<b>Faut-il commencer ?</b> Avec cette liste, non, dans la majorité des cas. Vous êtes une "
            "armée de réaction : laissez l'adversaire s'avancer, il entrera dans votre portée sans que "
            "vous ayez à vous exposer. L'exception : les scénarios où il faut aller chercher les points "
            "chez lui.",
            "<b>Ordre de pose :</b> posez d'abord les Wardens et le Cathallar (ils décident où sera "
            "votre centre de gravité), gardez Sevireth et les Riverblades pour la fin — ce sont eux qui "
            "réagissent au déploiement adverse.",
            "<b>N'oubliez pas Flawless Commander</b> après le déploiement : trois unités d'infanterie "
            "font un mouvement normal avant le premier tour.",
        ]),

        # ------------------------------------------------------------------
        ("section", "Check-list d'avant-partie"),
        ("ol", [
            "Lire le battleplan : <b>combien d'objectifs, où, et quand ils marquent</b>.",
            "Regarder la liste adverse et l'assigner à un des six archétypes ci-dessus.",
            "En déduire la <b>séquence de gravure</b> des cinq manches et l'écrire sur la feuille.",
            "Choisir les deux battle tactics en fonction du scénario, pas de l'envie.",
            "Décider si vous voulez commencer ou non.",
            "Déployer : Wardens et Cathallar d'abord, Sevireth et Riverblades en dernier.",
            "<b>Utiliser Flawless Commander</b> — trois mouvements normaux gratuits.",
            "Poser le Shrine Luminor (gratuit) là où il gênera l'adversaire ou couvrira un objectif.",
        ]),

        ("box", "La phrase à se répéter",
         "Les Lumineth ne détruisent pas l'armée d'en face : ils la retardent, la contournent et la "
         "prennent de vitesse au score. Chaque fois que vous hésitez entre « attaquer cette unité » et "
         "« aller tenir ce point », allez tenir le point."),
    ]

    return build_document(
        "04_Lumineth_strategies.pdf",
        "Lumineth Realm-lords — Stratégies",
        "L'Art de la Lumière",
        "Stratégies par type d'adversaire et par type de scénario",
        [
            "<b>Ce document répond à une seule question :</b> une fois la liste posée sur la table, "
            "que fait-on ? Il rappelle d'abord l'identité de la faction, donne un plan de base en cinq "
            "manches, puis décline la stratégie selon six archétypes d'adversaires et quatre formes de "
            "scénario.",
            "Les repères chiffrés proviennent des résultats AoSPy du dépôt (722 unités, 25 armées) : "
            "ils indiquent quelles armées gagnent l'échange de dégâts — donc lesquelles il faut "
            "absolument éviter d'affronter de face.",
            "La dernière page est une check-list à dérouler avant chaque partie.",
        ],
        "LUMINETH REALM-LORDS  ·  STRATÉGIES",
        blocks,
        cover_footer="Fiche IV sur IV — Compendium Lumineth",
    )
