"""Tests unitaires du module saisonnalite : un test par fonction."""

import pandas as pd
import pytest

from sncf_project.config import poids_gravité
from sncf_project.saisonnalite import (
    calculer_scores_mensuels,
    heatmap_saisonniere,
    moyenne_ponderee,
    profil_saisonnier,
)


def fausses_donnees():
    """Une année, deux liaisons, avec beaucoup plus de retard en juillet."""
    lignes = []
    for m in range(1, 13):
        retard = 15.0 if m == 7 else 2.0 + 0.5 * m
        for depart in ["LYON", "NANTES"]:
            lignes.append(
                {
                    "mois": pd.Timestamp(f"2023-{m:02d}"),
                    "départ": depart,
                    "arrivée": "PARIS",
                    "moy_trajet (min)": 120.0,
                    "nb_prevues": 100,
                    "nb_annules": 2,
                    "nb_trajets": 98,
                    "nb_retard_arr": 20,
                    "retard_moy_arr": 20.0,
                    "retard_moy_all_arr": retard,
                    "nb_>15min": int(retard),
                    "retard_moy_>15min": 30.0,
                    "nb_>30min": int(retard / 2),
                    "nb_>60min": 1,
                }
            )
    return pd.DataFrame(lignes)


def test_moyenne_ponderee():
    # check si la ponderation fonctionne
    df = pd.DataFrame({"g": ["a", "a", "a"], "x": [10.0, 20.0, None], "w": [1, 3, 100]})
    assert moyenne_ponderee(df, "x", ["g"], poids="w")["a"] == 17.5



def test_calculer_scores_mensuels():
    #check si on obtient bien une ligne par liaison et par mois
    scores = calculer_scores_mensuels(fausses_donnees(), poids_gravité)
    assert len(scores) == 24  # 2 liaisons × 12 mois
    assert "score_4" in scores.columns

    with pytest.raises(ValueError):
        calculer_scores_mensuels(pd.DataFrame(), poids_gravité)


def test_profil_saisonnier():
    #check si score, moyenne et ecart donne le bon resultat
    scores = calculer_scores_mensuels(fausses_donnees(), poids_gravité)
    profil = profil_saisonnier(scores, "score_3")
    pire_mois = profil.loc[profil["ecart_favorable_pct"].idxmin(), "nom_mois"]
    assert pire_mois == "juil."

    with pytest.raises(ValueError):
        profil_saisonnier(scores, "score_9")


def test_heatmap_saisonniere():
    #donne la taille du tab 
    scores = calculer_scores_mensuels(fausses_donnees(), poids_gravité)
    heatmap = heatmap_saisonniere(scores)
    assert heatmap.shape == (4, 12)  # 4 scores × 12 mois
    assert (heatmap["juil."] < 0).all()  # juillet est le pire mois partout