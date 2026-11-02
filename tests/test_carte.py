"""Tests de la construction de la carte."""

import numpy as np
import pandas as pd

from sncf_project.carte import ECHELLE, bornes, couleurs, creer_carte, legende

VERT, ROUGE = ECHELLE[0].tolist(), ECHELLE[-1].tolist()


def test_couleurs_du_vert_au_rouge() -> None:
    resultat = couleurs(pd.Series([0, 5, 10]), bas=0, haut=10)
    assert resultat[0][:3] == VERT
    assert resultat[2][:3] == ROUGE


def test_couleurs_hors_bornes_ramenees_aux_extremites() -> None:
    resultat = couleurs(pd.Series([-50, 500]), bas=0, haut=10)
    assert resultat[0][:3] == VERT
    assert resultat[1][:3] == ROUGE


def test_bornes_ignorent_une_valeur_extreme() -> None:
    bas, haut = bornes(pd.Series([*range(1, 100), 10_000]))
    assert haut < 100


def test_legende_affiche_les_bornes() -> None:
    html = legende(8.1, 24.7, "%")
    assert "8.1 %" in html and "24.7 %" in html


def liaisons_exemple() -> pd.DataFrame:
    """Deux liaisons avec des itinéraires simplifiés."""
    return pd.DataFrame(
        {
            "gare_a": ["LYON PART DIEU", "LILLE"],
            "gare_b": ["PARIS LYON", "PARIS NORD"],
            "itineraire": [
                [[4.86, 45.76], [2.37, 48.84]],
                [[3.07, 50.64], [2.35, 48.88]],
            ],
            "valeur": [12.0, 20.0],
            "prevus": [1000, 100],
        }
    )


def test_creer_carte_avec_et_sans_reseau() -> None:
    reseau = [np.array([[2.0, 48.0], [2.1, 48.1]])]
    avec = creer_carte(liaisons_exemple(), "Retard", reseau)
    sans = creer_carte(liaisons_exemple(), "Retard")
    # réseau en fond + liaisons + gares
    assert [c.type for c in avec.layers] == [
        "PathLayer",
        "PathLayer",
        "ScatterplotLayer",
    ]
    assert [c.type for c in sans.layers] == ["PathLayer", "ScatterplotLayer"]


def test_creer_carte_infobulle_des_liaisons() -> None:
    carte = creer_carte(liaisons_exemple(), "Retard")
    premiere = carte.layers[0].data[0]
    # La liaison la plus fréquentée est dessinée en premier (sous les autres)
    assert premiere["titre"] == "LYON PART DIEU ↔ PARIS LYON"
    # Pas de HTML dans les données : Streamlit l'afficherait tel quel
    assert premiere["detail"] == "Retard : 12.0\n1000 circulations prévues"
