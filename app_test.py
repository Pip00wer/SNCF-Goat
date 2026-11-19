"""Carte des liaisons TGV sur le réseau ferré.

Lancer avec : uv run streamlit run app.py
"""

from pathlib import Path

import pandas as pd
import streamlit as st

from sncf_project.aggregation import aggregate_by_ligne
from sncf_project.carte import bornes, creer_carte, legende
from sncf_project.config import (
    cols_to_drop,
    columns_mapping,
    poids_gravité,
)
from sncf_project.preprocessing import get_data_and_preprocess
from sncf_project.reseau import ReseauFerre
from sncf_project.scoring import all_scores_and_sort

DATA = Path(__file__).parent / "data"


@st.cache_resource
def charger_reseau() -> ReseauFerre:
    """Charge le réseau ferré une seule fois pour toute l'application."""
    return ReseauFerre(DATA / "formes-des-lignes-du-rfn.csv")


@st.cache_data
def charger_donnees_propres() -> pd.DataFrame:
    """Charge et nettoie les données de régularité via le preprocessing."""
    df = get_data_and_preprocess(
        DATA / "regularite-mensuelle-tgv-aqst.csv",
        cols_to_drop,
        columns_mapping,
    )
    df["date"] = pd.to_datetime(df["date"], format="%Y-%m")
    return df



#@st.cache_data
#def charger_regularite() -> pd.DataFrame:
#    """Charge la régularité mensuelle ; A → B et B → A forment une même liaison."""
#    df = pd.read_csv(DATA / "regularite-mensuelle-tgv-aqst.csv", sep=";")
#    df["mois"] = pd.to_datetime(df["Date"], format="%Y-%m")
#    gares = df[["Gare de départ", "Gare d'arrivée"]]
#    df["gare_a"], df["gare_b"] = gares.min(axis=1), gares.max(axis=1)
#    return df


@st.cache_data
def itineraire(gare_a: str, gare_b: str) -> list[list[float]]:
    """Itinéraire d'une liaison, mis en cache car le calcul prend ~20 ms."""
    return charger_reseau().itineraire(gare_a, gare_b)


#def taux_retard_15(regularite: pd.DataFrame) -> pd.DataFrame:
#    """Part des trains en retard de plus de 15 min, par liaison.

#    Indicateur provisoire, à remplacer par le score de fiabilité.
    
#    liaisons = regularite.groupby(["gare_a", "gare_b"], as_index=False).agg(
#        prevus=("Nombre de circulations prévues", "sum"),
#        annules=("Nombre de trains annulés", "sum"),
#        retards=("Nombre trains en retard > 15min", "sum"),
#    )
#    liaisons["valeur"] = (
#        100 * liaisons["retards"] / (liaisons["prevus"] - liaisons["annules"])
#    )
#    return liaisons

@st.cache_data
def calculer_liaisons_scorees(
    df: pd.DataFrame,
    debut: pd.Timestamp,
    fin: pd.Timestamp,
    gare: str,
    choix_score: str,
) -> pd.DataFrame:
    """Agrège sur la période choisie, calcule les scores et formate pour la carte."""
    # 1. Agrégation (aller_retour=True pour matcher la carte)
    agg_df, lignes_dict = aggregate_by_ligne(
        df,
        start_date=debut,
        end_date=fin,
        aller_retour=True,
    )

    # 2. Scoring
    scores_df = all_scores_and_sort(agg_df, poids_gravité, sort_by=choix_score)

    # 3. Récupération de gare_a et gare_b via numero_ligne et lignes_dict
    numeros = (
        scores_df["numero_ligne"]
        if "numero_ligne" in scores_df.columns
        else scores_df.index
    )
    paires = [lignes_dict.get(num, (None, None)) for num in numeros]

    gares = pd.DataFrame(paires, index=scores_df.index, columns=["départ", "arrivée"])
    scores_df = scores_df.dropna(subset=[])  # garde l'alignement
    scores_df["gare_a"] = gares["départ"]
    scores_df["gare_b"] = gares["arrivée"]
    scores_df = scores_df.dropna(subset=["gare_a", "gare_b"])
    gares_triees = scores_df[["gare_a", "gare_b"]].copy()
    scores_df["gare_a"] = gares_triees.min(axis=1)
    scores_df["gare_b"] = gares_triees.max(axis=1)

    # 4. Filtre sur la gare sélectionnée dans la sidebar
    if gare != "Toutes les gares":
        scores_df = scores_df[
            (scores_df["gare_a"] == gare) | (scores_df["gare_b"] == gare)
        ]

    # 5. Renommage pour correspondre exactement à ce qu'attend creer_carte()
    scores_df = scores_df.rename(
        columns={
            choix_score: "valeur",
            "nb_prevues": "prevus",
        }
    )
    return scores_df.reset_index()



st.set_page_config(page_title="Carte des TGV", page_icon="🚄", layout="wide")
st.title(
    "Peut-on construire un score de fiabilité par liaison, combinant taux "
    "d’annulation et retard moyen, et le représenter sur une carte du réseau ?"
)

df_clean = charger_donnees_propres()
mois = sorted(df_clean["mois"].unique())
toutes_gares = sorted(set(df_clean["départ"]) | set(df_clean["arrivée"]))

with st.sidebar:
    debut, fin = st.select_slider(
        "Période",
        options=mois,
        value=(mois[-12], mois[-1]),
        format_func=lambda m: pd.Timestamp(m).strftime("%m/%Y"),
    )
    
    gare = st.selectbox("Gare", ["Toutes les gares", *toutes_gares])
    choix_score = st.selectbox(
        "Méthode de scoring",
        options=["score_1", "score_2", "score_3"],
        index=2,
        format_func=lambda s: {
            "score_1": "Score 1 – Taux de réussite",
            "score_2": "Score 2 – Gravité des retards",
            "score_3": "Score 3 – Relatif au temps de trajet",
        }[s],
    )
    afficher_reseau = st.checkbox("Afficher le réseau ferré", value=True)

liaisons = calculer_liaisons_scorees(df_clean, debut, fin, gare, choix_score)


if liaisons.empty:
    st.info("Aucune circulation pour cette gare sur la période choisie.")
    st.stop()

liaisons["itineraire"] = [
    itineraire(a, b) for a, b in zip(liaisons["gare_a"], liaisons["gare_b"])
]

noms_indicateurs = {
    "score_1": "Score de fiabilité – Taux de réussite (/100)",
    "score_2": "Score de fiabilité – Gravité des retards (/100)",
    "score_3": "Score de fiabilité – Relatif au temps de trajet (/100)",
}
nom_indicateur = noms_indicateurs[choix_score]

reseau = charger_reseau().traces if afficher_reseau else None
st.pydeck_chart(creer_carte(liaisons, nom_indicateur, reseau), height=650)
st.markdown(
    f"**{nom_indicateur}** {legende(*bornes(liaisons['valeur']), ' pts')}",
    unsafe_allow_html=True,
)
st.caption(
    "Épaisseur proportionnelle au nombre de circulations prévues. "
    "Les itinéraires sont reconstitués (trajet le plus rapide sur le réseau, "
    "en privilégiant les LGV), ce ne sont pas les sillons réels. "
    "Sources : SNCF Réseau (formes des lignes du RFN), AQST (régularité mensuelle TGV)."
)
