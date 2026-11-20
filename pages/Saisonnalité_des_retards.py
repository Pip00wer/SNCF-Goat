"""Page Streamlit : saisonnalité des scores de fiabilité sur tout le réseau."""

from pathlib import Path

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from sncf_project.config import cols_to_drop, columns_mapping, poids_gravité
from sncf_project.preprocessing import get_data_and_preprocess
from sncf_project.saisonnalite import (
    LIBELLES_SCORES,
    SCORES,
    SCORES_DECROISSANTS,
    calculer_scores_mensuels,
    heatmap_saisonniere,
    profil_saisonnier,
)

DATA = Path(__file__).parents[1] / "data"

# Couleurs : rouge = mois moins fiable, bleu = mois plus fiable
ROUGE = "#d6604d"
BLEU = "#4393c3"
ECHELLE_HEATMAP = [
    [0.0, "#b2182b"],
    [0.25, ROUGE],
    [0.5, "#f7f7f7"],
    [0.75, BLEU],
    [1.0, "#2166ac"],
]


@st.cache_data
def charger_scores():
    """Calcule une seule fois les scores mensuels de toutes les liaisons."""
    df = get_data_and_preprocess(
        DATA / "regularite-mensuelle-tgv-aqst.csv", cols_to_drop, columns_mapping
    )
    return calculer_scores_mensuels(df, poids_gravité, aller_retour=True)


def unite(score):
    """Unité d'affichage d'un score."""
    return "min" if score in SCORES_DECROISSANTS else "pts"


st.set_page_config(page_title="Saisonnalité des TGV", layout="wide")

with st.sidebar:
    st.page_link("app.py", label="Carte de fiabilité")
    st.page_link(
        "pages/Saisonnalité_des_retards.py",
        label="Saisonnalité des retards",
    )
    st.divider()

st.title("Quels mois de l'année les TGV sont-ils le moins fiables ?")
scores = charger_scores()

with st.sidebar:
    score = st.selectbox(
        "Score étudié",
        options=SCORES,
        index=2,
        format_func=LIBELLES_SCORES.get,
    )

# 1. Les quatre scores mois par mois
st.header("Les quatre scores mois par mois")
heatmap = heatmap_saisonniere(scores)
borne = float(heatmap.abs().max().max()) or 1.0
figure_heatmap = px.imshow(
    heatmap,
    color_continuous_scale=ECHELLE_HEATMAP,
    zmin=-borne,
    zmax=borne,
    text_auto=".0f",
    aspect="auto",
    labels={"color": "Écart (%)", "x": "", "y": ""},
)
figure_heatmap.update_traces(xgap=2, ygap=2)
figure_heatmap.update_layout(height=320, margin={"t": 10, "b": 10})
st.plotly_chart(figure_heatmap, width="stretch")
st.caption(
    "Écart de chaque mois à la moyenne annuelle du score, en %. "
    "Bleu = mois plus fiable que la moyenne, rouge = moins fiable "
    "(le sens est corrigé pour le score 4, exprimé en minutes)."
)

# 2. Profil détaillé du score choisi
st.header(LIBELLES_SCORES[score])
profil = profil_saisonnier(scores, score)
pire = profil.loc[profil["ecart_favorable_pct"].idxmin()]
meilleur = profil.loc[profil["ecart_favorable_pct"].idxmax()]
col_graphe, col_texte = st.columns([3, 1])
with col_graphe:
    figure_profil = go.Figure()
    figure_profil.add_bar(
        x=profil["nom_mois"],
        y=profil["valeur"],
        marker_color=[ROUGE if e < 0 else BLEU for e in profil["ecart_favorable_pct"]],
    )
    figure_profil.add_hline(
        y=float(profil["moyenne"].iloc[0]),
        line_dash="dash",
        annotation_text="moyenne annuelle",
    )
    figure_profil.update_yaxes(
        range=[
            float(profil["valeur"].min()) * 0.95,
            float(profil["valeur"].max()) * 1.02,
        ],
        title=unite(score),
    )
    figure_profil.update_layout(height=350, margin={"t": 10})
    st.plotly_chart(figure_profil, width="stretch")
with col_texte:
    st.metric(
        "Pire mois",
        pire["nom_mois"],
        f"{pire['ecart_favorable_pct']:+.1f} % vs moyenne",
    )
    st.metric(
        "Meilleur mois",
        meilleur["nom_mois"],
        f"{meilleur['ecart_favorable_pct']:+.1f} % vs moyenne",
    )


st.divider()
st.caption(
    "\\* Le score 5 n'est pas étudié ici. Il ne mesure pas la fiabilité "
    "d'une liaison dans l'absolu : il la compare aux 10 % des pires liaisons "
    "du réseau. C'est donc une note relative. Si tout le réseau va très bien, "
    "les pires liaisons vont bien aussi, et une liaison correcte peut quand "
    "même obtenir une note faible. Comparer cette note d'un mois à l'autre "
    "n'aurait donc pas vraiment de sens."
)
