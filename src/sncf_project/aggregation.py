"""
Fichier d'agrégation pour le projet SNCF.
Contient les fonctions permettant d'agréger les données par ligne et de calculer les métriques pondérées (moyennes).
"""

import numpy as np
import pandas as pd


def add_ligne(df: pd.DataFrame, aller_retour: bool) -> pd.DataFrame:
    df = df.copy()
    if not aller_retour:
        df["gare_a"] = df["départ"]
        df["gare_b"] = df["arrivée"]
    else:
        paires_triees = np.sort(df[["départ", "arrivée"]].values, axis=1)
        df["gare_a"] = paires_triees[:, 0]
        df["gare_b"] = paires_triees[:, 1]

    df["numero_ligne"] = df.groupby(["gare_a", "gare_b"]).ngroup() + 1
    return df


def filter_study(df: pd.DataFrame, start_date, end_date) -> pd.DataFrame:
    return df[(df["date"] >= start_date) & (df["date"] <= end_date)].copy()


def set_ponderation(df: pd.DataFrame) -> pd.DataFrame:
    df["pond_moy_durée"] = df["moy_trajet (min)"] * df["nb_trajets"]
    df["pond_retard_moy_retard"] = df["retard_moy_arr"] * df["nb_retard_arr"]
    df["pond_retard_moy_all"] = df["retard_moy_all_arr"] * df["nb_trajets"]
    df["pond_moy_retard>15"] = df["retard_moy_>15min"] * df["nb_>15min"]
    return df


def aggregate_by_ligne(
    df: pd.DataFrame,
    start_date=None,
    end_date=None,
    aller_retour: bool = False,
):
    if start_date is not None and end_date is not None:
        df = filter_study(df, start_date, end_date)

    df = add_ligne(df, aller_retour)

    lignes_dict = (
        df[["numero_ligne", "gare_a", "gare_b"]]
        .drop_duplicates()
        .set_index("numero_ligne")
        .apply(tuple, axis=1)
        .to_dict()
    )

    df = set_ponderation(df)

    # On groupe par numero_ligne, gare_a et gare_b pour garder les noms de gares en colonnes
    agg_df = df.groupby(["numero_ligne", "gare_a", "gare_b"], as_index=False).agg(
        {
            "nb_prevues": "sum",
            "nb_annules": "sum",
            "pond_moy_durée": "sum",
            "pond_retard_moy_retard": "sum",
            "pond_retard_moy_all": "sum",
            "pond_moy_retard>15": "sum",
            "nb_trajets": "sum",
            "nb_retard_arr": "sum",
            "nb_>15min": "sum",
            "nb_>30min": "sum",
            "nb_>60min": "sum",
        }
    )

    # .replace(0, np.nan) évite les divisions par zéro si une ligne a 0 retard > 15min
    agg_df["moy_durée"] = agg_df["pond_moy_durée"] / agg_df["nb_trajets"].replace(
        0, np.nan
    )
    agg_df["moy_retard"] = agg_df["pond_retard_moy_retard"] / agg_df[
        "nb_retard_arr"
    ].replace(0, np.nan)
    agg_df["retard_moy_all"] = agg_df["pond_retard_moy_all"] / agg_df[
        "nb_trajets"
    ].replace(0, np.nan)
    agg_df["moy_retard>15"] = agg_df["pond_moy_retard>15"] / agg_df[
        "nb_>15min"
    ].replace(0, np.nan)

    pond_to_drop = [
        "pond_moy_durée",
        "pond_retard_moy_retard",
        "pond_retard_moy_all",
        "pond_moy_retard>15",
    ]
    agg_df = agg_df.drop(columns=pond_to_drop)

    return agg_df, lignes_dict
