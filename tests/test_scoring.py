"""Vérifie la réutilisation des moyennes pondérées pour les nouveaux scores."""

import pandas as pd
import pytest

from sncf_project.aggregation import aggregate_by_ligne
from sncf_project.config import poids_gravité
from sncf_project.scoring import (
    _penalite_relative,
    all_scores_and_sort,
    score_4,
    score_5,
)

DEBUT = pd.Timestamp("2024-01-01")
FIN = pd.Timestamp("2024-02-01")


@pytest.fixture
def observations() -> pd.DataFrame:
    df = pd.DataFrame(
        [
            ("A", "B", "2024-01", 100, 0, 10.0, 100),
            ("B", "A", "2024-01", 300, 60, 30.0, 200),
            ("A", "B", "2024-02", 100, 0, 5.0, 100),
            ("C", "D", "2024-01", 100, 0, 50.0, 100),
            ("D", "C", "2024-02", 100, 100, None, 100),
        ],
        columns=[
            "départ",
            "arrivée",
            "date",
            "nb_prevues",
            "nb_annules",
            "retard_moy_arr",
            "moy_trajet (min)",
        ],
    )
    df["date"] = pd.to_datetime(df["date"])
    df["nb_trajets"] = df["nb_prevues"] - df["nb_annules"]
    df["nb_retard_arr"] = [10, 60, 5, 20, 0]
    df["retard_moy_all_arr"] = (
        df["retard_moy_arr"] * df["nb_retard_arr"] / df["nb_trajets"]
    ).fillna(0)
    df["retard_moy_>15min"] = df["retard_moy_arr"]
    df["nb_>15min"] = 0
    df["nb_>30min"] = 0
    df["nb_>60min"] = 0
    return df


def test_scores_4_et_5_utilisent_les_moyennes_de_la_periode(
    observations: pd.DataFrame,
) -> None:
    agrege, _ = aggregate_by_ligne(observations, aller_retour=True)
    scores = all_scores_and_sort(
        agrege.copy(),
        poids_gravité,
        sort_by="score_4",
        debut=DEBUT,
        fin=FIN,
    )
    assert scores["numero_ligne"].tolist() == [1, 2]
    scores = scores.set_index("numero_ligne")
    # Les volumes de toute la période entrent dans la pénalité, sans moyenne mensuelle.
    cout_annulations = 60 * min(60 * 900 / 500 + 0.1 * (68_000 / 440), 120)
    assert scores.loc[1, "score_4"] == pytest.approx((1_925 + cout_annulations) / 500)
    assert scores.loc[2, "score_4"] == pytest.approx(65)
    p90_retard = 0.1 * (1_925 / 440) + 0.9 * 10
    p90_annulation = 0.1 * 12 + 0.9 * 50
    assert scores.loc[1, "score_5"] == pytest.approx(
        100 * (1 - 0.3 * 12 / p90_annulation - 0.7 * (1_925 / 440) / p90_retard)
    )
    assert scores.loc[2, "score_5"] == 0
    moyennes = ["moy_durée", "moy_retard", "retard_moy_all"]
    pd.testing.assert_frame_equal(
        scores[moyennes].sort_index(),
        agrege.set_index("numero_ligne")[moyennes].sort_index(),
    )


def test_periode_selectionnee_et_moyennes_existantes(
    observations: pd.DataFrame,
) -> None:
    debut = fin = pd.Timestamp("2024-02-01")
    agrege, _ = aggregate_by_ligne(observations, debut, fin, aller_retour=True)
    scores = all_scores_and_sort(
        agrege,
        poids_gravité,
        sort_by="score_5",
        debut=debut,
        fin=fin,
    )
    ab = scores.loc[scores["gare_a"].eq("A")].iloc[0]
    assert ab["score_4"] == 0.25
    assert ab["score_5"] == pytest.approx(30)


def test_aucun_train_en_retard_ne_penalise_pas_la_note(
    observations: pd.DataFrame,
) -> None:
    observations["nb_annules"] = 0
    observations["nb_trajets"] = observations["nb_prevues"]
    observations["nb_retard_arr"] = 0
    observations["retard_moy_arr"] = 0
    observations["retard_moy_all_arr"] = 0
    agrege, _ = aggregate_by_ligne(observations, aller_retour=True)
    assert agrege["moy_retard"].isna().all()
    scores = all_scores_and_sort(
        agrege,
        poids_gravité,
        sort_by="score_5",
        debut=DEBUT,
        fin=FIN,
    )
    assert scores["score_4"].eq(0).all()
    assert scores["score_5"].eq(100).all()


def test_penalite_p90_nul_negatif_ou_manquant() -> None:
    resultat = _penalite_relative(
        pd.Series([0.0, 5.0, -2.0, 5.0, None, 5.0]),
        pd.Series([0.0, 0.0, -1.0, -1.0, 10.0, None]),
    )
    assert resultat.iloc[:4].tolist() == [0, 1, 0, 1]
    assert resultat.iloc[4:].isna().all()


@pytest.mark.parametrize(
    ("debut", "fin", "jours"),
    [
        ("2023-02-01", "2023-02-01", 28),
        ("2024-02-01", "2024-02-01", 29),
        ("2024-04-01", "2024-04-01", 30),
        ("2024-01-01", "2024-01-01", 31),
        ("2023-12-01", "2024-02-01", 91),
    ],
)
def test_score_4_compte_les_jours_des_mois_inclus(debut, fin, jours) -> None:
    df = pd.DataFrame(
        {
            "nb_prevues": [10_000],
            "nb_annules": [1_000],
            "nb_trajets": [9_000],
            "moy_durée": [100.0],
            "retard_moy_all": [2.0],
        }
    )
    resultat = score_4(df, pd.Timestamp(debut), pd.Timestamp(fin))
    assert resultat.loc[0, "score_4"] == pytest.approx(
        (18_000 + 1_000 * (jours * 900 / 10_000 + 10)) / 10_000
    )


def test_score_4_reste_stable_quand_la_periode_et_le_trafic_doublent() -> None:
    df = pd.DataFrame(
        {
            "nb_prevues": [1_000],
            "nb_annules": [100],
            "nb_trajets": [900],
            "moy_durée": [100.0],
            "retard_moy_all": [2.0],
        }
    )
    double = df.copy()
    double[["nb_prevues", "nb_annules", "nb_trajets"]] *= 2
    simple = score_4(df, pd.Timestamp("2024-07-01"), pd.Timestamp("2024-07-01"))
    etendu = score_4(double, pd.Timestamp("2024-07-01"), pd.Timestamp("2024-08-01"))
    assert simple.loc[0, "score_4"] == pytest.approx(etendu.loc[0, "score_4"])


def test_score_5_tient_compte_de_la_frequence_des_retards() -> None:
    df = pd.DataFrame(
        {
            "nb_prevues": [100, 100],
            "nb_annules": [0, 0],
            "nb_trajets": [100, 100],
            "nb_retard_arr": [1, 50],
            "moy_retard": [30.0, 30.0],
            "retard_moy_all": [0.3, 15.0],
        }
    )
    resultat = score_5(df)
    assert resultat.loc[0, "score_5"] == pytest.approx(100 * (1 - 0.7 * 0.3 / 13.53))
    assert resultat.loc[1, "score_5"] == pytest.approx(30)
