"""Carte des liaisons TGV sur le réseau ferré.

Lancer avec : uv run streamlit run app.py
"""

from pathlib import Path

import pandas as pd
import streamlit as st

from sncf_project.carte import bornes, creer_carte, legende
from sncf_project.reseau import ReseauFerre

DATA = Path(__file__).parent / "data"


@st.cache_resource
def charger_reseau() -> ReseauFerre:
    """Charge le réseau ferré une seule fois pour toute l'application."""
    return ReseauFerre(DATA / "formes-des-lignes-du-rfn.csv")


@st.cache_data
def charger_regularite() -> pd.DataFrame:
    """Charge la régularité mensuelle ; A → B et B → A forment une même liaison."""
    df = pd.read_csv(DATA / "regularite-mensuelle-tgv-aqst.csv", sep=";")
    df["mois"] = pd.to_datetime(df["Date"], format="%Y-%m")
    gares = df[["Gare de départ", "Gare d'arrivée"]]
    df["gare_a"], df["gare_b"] = gares.min(axis=1), gares.max(axis=1)
    return df


@st.cache_data
def itineraire(gare_a: str, gare_b: str) -> list[list[float]]:
    """Itinéraire d'une liaison, mis en cache car le calcul prend ~20 ms."""
    return charger_reseau().itineraire(gare_a, gare_b)


def taux_retard_15(regularite: pd.DataFrame) -> pd.DataFrame:
    """Part des trains en retard de plus de 15 min, par liaison.

    Indicateur provisoire, à remplacer par le score de fiabilité.
    """
    liaisons = regularite.groupby(["gare_a", "gare_b"], as_index=False).agg(
        prevus=("Nombre de circulations prévues", "sum"),
        annules=("Nombre de trains annulés", "sum"),
        retards=("Nombre trains en retard > 15min", "sum"),
    )
    liaisons["valeur"] = (
        100 * liaisons["retards"] / (liaisons["prevus"] - liaisons["annules"])
    )
    return liaisons


st.set_page_config(page_title="Carte des TGV", page_icon="🚄", layout="wide")
st.title(
    "Peut-on construire un score de fiabilité par liaison, combinant taux "
    "d’annulation et retard moyen, et le représenter sur une carte du réseau ?"
)

regularite = charger_regularite()
mois = sorted(regularite["mois"].unique())
with st.sidebar:
    debut, fin = st.select_slider(
        "Période",
        options=mois,
        value=(mois[-12], mois[-1]),
        format_func=lambda m: pd.Timestamp(m).strftime("%m/%Y"),
    )
    gare = st.selectbox(
        "Gare",
        [
            "Toutes les gares",
            *sorted(set(regularite["gare_a"]) | set(regularite["gare_b"])),
        ],
    )
    afficher_reseau = st.checkbox("Afficher le réseau ferré", value=True)

selection = regularite[regularite["mois"].between(debut, fin)]
if gare != "Toutes les gares":
    selection = selection[(selection["gare_a"] == gare) | (selection["gare_b"] == gare)]

if selection.empty:
    st.info("Aucune circulation pour cette gare sur la période choisie.")
    st.stop()

liaisons = taux_retard_15(selection)
liaisons["itineraire"] = [
    itineraire(a, b) for a, b in zip(liaisons["gare_a"], liaisons["gare_b"])
]

nom_indicateur = "Trains en retard > 15 min (%)"
reseau = charger_reseau().traces if afficher_reseau else None
st.pydeck_chart(creer_carte(liaisons, nom_indicateur, reseau), height=650)
st.markdown(
    f"**{nom_indicateur}** {legende(*bornes(liaisons['valeur']), '%')}",
    unsafe_allow_html=True,
)
st.caption(
    "Épaisseur proportionnelle au nombre de circulations prévues. "
    "Les itinéraires sont reconstitués (trajet le plus rapide sur le réseau, "
    "en privilégiant les LGV), ce ne sont pas les sillons réels. "
    "Sources : SNCF Réseau (formes des lignes du RFN), AQST (régularité mensuelle TGV)."
)
