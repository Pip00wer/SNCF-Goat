"""Saisonnalité des 4 scores de fiabilité.
On calcule les scores pour chaque liaison et chaque mois, pour voir quels mois
sont les pires et les meilleurs.
Pour le score 5, n'est pas étudié ici
"""

import logging

import numpy as np
import pandas as pd

from sncf_project.aggregation import aggregate_by_ligne
from sncf_project.scoring import score_1, score_2, score_3, score_4

logger = logging.getLogger(__name__)

SCORES = ["score_1", "score_2", "score_3", "score_4"]
SCORES_DECROISSANTS = {"score_4"}  # scores où une valeur basse est meilleure

LIBELLES_SCORES = {
    "score_1": "Score 1 – Taux de réussite",
    "score_2": "Score 2 – Gravité des retards",
    "score_3": "Score 3 – En fonction du temps de trajet",
    "score_4": "Score 4 – Minutes de perturbation",
}

NOMS_MOIS = [
    "janv.", "févr.", "mars", "avr.", "mai", "juin","juil.", "août", "sept.", "oct.", "nov.", "déc.",]


def moyenne_ponderee(df, colonne, cles, poids="nb_prevues"):
    # Moyenne de colonne par groupe, pondérée par le nombre de trains
    # Sans dropna, les lignes vides compteraient dans le total des poids
    df = df.dropna(subset=[colonne])
    df = df.assign(produit=df[colonne] * df[poids])
    sommes = df.groupby(cles)[["produit", poids]].sum()
    return sommes["produit"] / sommes[poids]


def calculer_scores_mensuels(df, poids_gravite, aller_retour=True):
    """Calcule les 4 scores pour chaque liaison et chaque mois."""
    if df.empty or "mois" not in df.columns:
        logger.error("Données invalides : DataFrame vide ou sans colonne mois")
        raise ValueError("Le DataFrame est vide ou incomplet.")

    resultats = []
    for mois, donnees_du_mois in df.groupby("mois"):
        agg, _ = aggregate_by_ligne(donnees_du_mois, aller_retour=aller_retour)
        agg = score_1(agg)
        agg = score_2(agg, poids_gravite)
        agg = score_3(agg)
        agg = score_4(agg, mois, mois)  # le score 4 dépend du nombre de jours
        agg["mois"] = mois
        resultats.append(agg)
    scores = pd.concat(resultats, ignore_index=True)
    #Après la boucle, resultats contient 105 tableaux (pour chaue mois). concat les empile en un seul grand tableau.

    # Une division par 0 donne l'infini : on le remplace par une valeur Nan
    scores[SCORES] = scores[SCORES].replace([np.inf, -np.inf], np.nan)
    scores["mois_annee"] = scores["mois"].dt.month  # 1 = janvier

    logger.info("Scores mensuels calculés : %d lignes", len(scores))
    return scores


def profil_saisonnier(scores, score):
    # Moyenne d'un score pour chaque mois de l'année, toutes années confondues.
    if score not in SCORES:
        raise ValueError(f"Score inconnu : {score}")

    valeurs = moyenne_ponderee(scores, score, ["mois_annee"])
    valides = scores.dropna(subset=[score])
    moyenne = (valides[score] * valides["nb_prevues"]).sum() / valides[
        "nb_prevues"
    ].sum()

    # Écart en % à la moyenne. Signe inversé pour le score 4, pour que
    # dans tous les cas : écart positif = mois meilleur que la moyenne.
    ecart = 100 * (valeurs - moyenne) / abs(moyenne)
    if score in SCORES_DECROISSANTS:
        ecart = -ecart

    return pd.DataFrame(
        {
            "nom_mois": [NOMS_MOIS[m - 1] for m in valeurs.index],
            "valeur": valeurs.to_numpy(),
            "moyenne": moyenne,
            "ecart_favorable_pct": ecart.to_numpy(),
        }
    )


def heatmap_saisonniere(scores):
    # Écart en % de chaque score pour chaque mois, pour la heatmap.
    heatmap = pd.DataFrame()
    for score in SCORES:
        profil = profil_saisonnier(scores, score)
        heatmap[LIBELLES_SCORES[score]] = profil["ecart_favorable_pct"].to_numpy()
    heatmap.index = profil["nom_mois"]
    return heatmap.T  # .T met les scores en lignes et les mois en colonnes