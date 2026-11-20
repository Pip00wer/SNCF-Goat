"""

Fichier de config pour le projet SNCF.
Ces paramètres permettent le bon deroulement du projet.
Ils peuvent être modifier par l'utilisateur selon ses besoins.


"""

aller_retour = True  # Indique si l'on considère un ligne sur l'aller-retour ou si on differtentie le sens de marche

start_date = "2024-01-01"  # Date de début de la période d'analyse
end_date = "2024-12-31"  # Date de fin de la période d'analyse


# Poids attribués à chaque catégorie de gravité des retards, utilisé pour le score_2. Plus le pids est élevé plus on pénalise le score,
# c'est-à-dire que les retards plus graves auront un impact plus important sur le score.
poids_gravité = {"15_30": 0.2, "30_60": 0.5, "60": 0.8, "annules": 1.0}

# Chemin vers le fichier de données contenant la régularité mensuelle des TGV
file_path = "data/regularite-mensuelle-tgv-aqst.csv"


# Colonnes à supprimer du jeu de données après le prétraitement car pas utilisés lors de NOTRE étude
cols_to_drop = [
    "Service",
    "Commentaire annulations",
    "Commentaire annulations",
    "Commentaire retards au départ",
    "Commentaire retards à l'arrivée",
    "Prct retard pour causes externes",
    "Prct retard pour cause infrastructure",
    "Prct retard pour cause gestion trafic",
    "Prct retard pour cause matériel roulant",
    "Prct retard pour cause gestion en gare et réutilisation de matériel",
    "Prct retard pour cause prise en compte voyageurs (affluence, gestions PSH, correspondances)",
    "Nombre de trains en retard au départ",
    "Retard moyen des trains en retard au départ",
    "Retard moyen de tous les trains au départ",
]

# Mapping des colonnes du fichier de données vers des noms plus explicites et uniformes pour l'analyse
columns_mapping = {
    "Gare de départ": "départ",
    "Gare d'arrivée": "arrivée",
    "Date": "date",
    "Durée moyenne du trajet": "moy_trajet (min)",
    "Nombre de circulations prévues": "nb_prevues",
    "Nombre de trains annulés": "nb_annules",
    "Nombre de trains en retard au départ": "nb_retard_dep",
    "Retard moyen des trains en retard au départ": "retard_moy_dep",
    "Retard moyen de tous les trains au départ": "retard_moy_all_dep",
    "Nombre de trains en retard à l'arrivée": "nb_retard_arr",
    "Retard moyen des trains en retard à l'arrivée": "retard_moy_arr",
    "Retard moyen de tous les trains à l'arrivée": "retard_moy_all_arr",
    "Nombre trains en retard > 15min": "nb_>15min",
    "Retard moyen trains en retard > 15 (si liaison concurrencée par vol)": "retard_moy_>15min",
    "Nombre trains en retard > 30min": "nb_>30min",
    "Nombre trains en retard > 60min": "nb_>60min",
}
