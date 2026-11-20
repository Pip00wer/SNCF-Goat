import pandas as pd
import numpy as np

"""
Fichier de scoring pour le projet SNCF.
Contient les fonctions permettant de calculer différents scores de performance des lignes.

Les scores sont des notes entre 0 et 100, sauf score_4, exprimé en minutes.

0 : Rien ne va 
100 : Parfait, aucun retard ni annulation
"""


# Calcul du score 1 : proportion de trajets effectués sans retard supérieur à 15 minutes.
def score_1(df):

    df["score_1"] = (
        (df["nb_trajets"] - df["nb_>15min"]) / df["nb_prevues"] * 100
    ).round(3)

    return df


# Calcul du score 2 : pondération des retards selon leur gravité et des annulations.
def score_2(df, poids_gravité):
    df["nb_15-30"] = df["nb_>15min"] - df["nb_>30min"]
    df["nb_30-60"] = df["nb_>30min"] - df["nb_>60min"]

    df["score_2"] = (
        (
            1
            - (
                df["nb_15-30"] * poids_gravité["15_30"]
                + df["nb_30-60"] * poids_gravité["30_60"]
                + df["nb_>60min"] * poids_gravité["60"]
                + df["nb_annules"] * poids_gravité["annules"]
            )
            / df["nb_prevues"]
        )
        * 100
    ).round(3)

    return df


# Calcul du score 3 : Retard moyen relatif au temps de trajet moyen et annulation des trajets
def score_3(df):

    df["score_3"] = 100 * (
        (1 - (df["nb_annules"] / df["nb_prevues"]))
        * (1 - (df["retard_moy_all"] / df["moy_durée"]))
    ).round(3)

    return df


# Calcul du score 4 : coût moyen des retards et annulations, en minutes par train prévu.
def score_4(df: pd.DataFrame, debut: pd.Timestamp, fin: pd.Timestamp) -> pd.DataFrame:
    # Les données sont mensuelles : inclure tous les jours des mois sélectionnés.
    premier_jour = pd.Timestamp(debut).to_period("M").start_time
    fin_exclue = (pd.Timestamp(fin).to_period("M") + 1).start_time
    if pd.isna(premier_jour) or pd.isna(fin_exclue) or fin_exclue <= premier_jour:
        raise ValueError("La période du score 4 doit contenir au moins un mois valide.")
    # 15 h exploitables par jour, avec les jours réels de chaque mois (février inclus).
    minutes_exploitables = (fin_exclue - premier_jour).days * (22 - 7) * 60
    prevues = df["nb_prevues"].where(df["nb_prevues"].gt(0))
    # L'espacement moyen théorique des trains sert de coût d'annulation, majoré
    # de 10 % du temps de trajet ; chaque annulation coûte au maximum 120 minutes.
    penalite = (minutes_exploitables / prevues + 0.1 * df["moy_durée"]).clip(upper=120)
    cout_annulations = (df["nb_annules"] * penalite).where(df["nb_annules"].ne(0), 0)
    # La moyenne de tous les trains restitue les minutes totales, sans nouvelle pondération.
    minutes_retard = (df["retard_moy_all"].clip(lower=0) * df["nb_trajets"]).where(
        df["nb_trajets"].ne(0), 0
    )
    # Répartir le coût sur tous les trains prévus, pas seulement les trains en retard.
    df["score_4"] = (minutes_retard + cout_annulations) / prevues
    return df


def _penalite_relative(valeur: pd.Series, seuil: pd.Series) -> pd.Series:
    """Reprend la normalisation du notebook, y compris les P90 nuls ou négatifs."""
    # Au-delà du seuil, la pénalité reste à 1 ; une donnée manquante reste manquante.
    ratio = valeur.div(seuil.where(seuil.gt(0))).clip(lower=0, upper=1)
    return ratio.where(seuil.gt(0), valeur.gt(0).astype(float)).where(
        valeur.notna() & seuil.notna()
    )


def _indicateurs_reseau(df: pd.DataFrame) -> pd.DataFrame:
    """Utilise les moyennes existantes, pondérées par aggregate_by_ligne."""
    valides = df["nb_prevues"].gt(0) & df["nb_annules"].between(0, df["nb_prevues"])
    return pd.DataFrame(
        {
            "annulation_pct": (100 * df["nb_annules"] / df["nb_prevues"]).where(
                valides
            ),
            "retard_arrive_min": df["retard_moy_all"].where(
                valides & df["nb_trajets"].gt(0)
            ),
        }
    )


# Calcul du score 5 : comparaison des moyennes de la période au P90 du réseau.
def score_5(df: pd.DataFrame) -> pd.DataFrame:
    # Inclure tous les trains pour tenir compte aussi de la fréquence des retards.
    indicateurs = _indicateurs_reseau(df)
    # Chaque liaison fusionnée pèse autant dans le P90, quel que soit son trafic.
    p90 = indicateurs.quantile(0.90)
    annulation = _penalite_relative(
        indicateurs["annulation_pct"],
        pd.Series(p90["annulation_pct"], index=df.index),
    )
    retard = _penalite_relative(
        indicateurs["retard_arrive_min"],
        pd.Series(p90["retard_arrive_min"], index=df.index),
    )
    # Note relative au réseau : 30 % annulations, 70 % retards ; une note haute est favorable.
    df["score_5"] = (100 * (1 - 0.3 * annulation - 0.7 * retard)).clip(
        lower=0, upper=100
    )
    return df


def all_scores_and_sort(df, poids_gravité, sort_by="score_1", *, debut, fin):
    df = score_1(df)
    df = score_2(df, poids_gravité)
    df = score_3(df)
    df = score_4(df, debut, fin)
    df = score_5(df)
    return df.sort_values(by=sort_by, ascending=sort_by == "score_4")
