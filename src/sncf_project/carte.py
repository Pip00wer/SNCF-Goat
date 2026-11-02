"""Carte pydeck des liaisons TGV, colorées selon un indicateur (ex. score).

Fond : réseau ferré. Par-dessus : liaisons le long des voies, puis gares.
"""

import numpy as np
import pandas as pd
import pydeck as pdk

from sncf_project.gares import GARES

# Échelle vert -> jaune -> rouge : vert pour les valeurs faibles
ECHELLE = np.array([[26, 152, 80], [250, 200, 40], [215, 48, 39]])
COULEUR_RESEAU = [55, 65, 85, 120]
COULEUR_GARE = [40, 40, 40, 220]


def bornes(valeurs: pd.Series) -> tuple[float, float]:
    # on prend les percentiles 5/95 pour lisser les valeurs extrèmes
    return float(np.nanpercentile(valeurs, 5)), float(np.nanpercentile(valeurs, 95))


def couleurs(valeurs: pd.Series, bas: float, haut: float) -> list[list[int]]:
    """Couleur RGBA de chaque valeur sur l'échelle vert -> rouge.

    :param valeurs: valeurs de l'indicateur.
    :param bas: valeur affichée en vert (et en dessous).
    :param haut: valeur affichée en rouge (et au-dessus).
    :return: une couleur ``[r, g, b, a]`` par valeur.
    """
    t = np.clip((valeurs.to_numpy(dtype=float) - bas) / max(haut - bas, 1e-9), 0, 1)
    rgb = np.column_stack([np.interp(t, [0, 0.5, 1], ECHELLE[:, k]) for k in range(3)])
    return [[*map(int, c), 230] for c in rgb]


def legende(bas: float, haut: float, unite: str) -> str:
    """Légende HTML de l'échelle de couleurs, à afficher avec ``st.markdown``.

    :param bas: valeur de l'extrémité verte.
    :param haut: valeur de l'extrémité rouge.
    :param unite: unité affichée après les valeurs (ex. ``"%"``).
    :return: fragment HTML.
    """
    gradient = ", ".join(f"rgb({r},{g},{b})" for r, g, b in ECHELLE)
    return (
        '<div style="display:flex;align-items:center;gap:8px;font-size:0.85rem">'
        f"<span>{bas:.1f} {unite}</span>"
        '<div style="flex:1;max-width:260px;height:10px;border-radius:5px;'
        f'background:linear-gradient(to right, {gradient})"></div>'
        f"<span>{haut:.1f} {unite}</span></div>"
    )


def creer_carte(
    liaisons: pd.DataFrame,
    nom_indicateur: str,
    reseau: list[np.ndarray] | None = None,
) -> pdk.Deck:
    """Construit la carte des liaisons.

    :param liaisons: une ligne par liaison, avec les colonnes ``gare_a``,
        ``gare_b``, ``itineraire`` (liste de ``[lon, lat]``), ``valeur``
        (l'indicateur à colorer) et ``prevus`` (nombre de circulations).
    :param nom_indicateur: nom de l'indicateur, affiché au survol.
    :param reseau: tracés du réseau ferré à afficher en fond (optionnel).
    :return: la carte, à afficher avec ``st.pydeck_chart``.
    """
    bas, haut = bornes(liaisons["valeur"])
    liaisons = liaisons.assign(
        couleur=couleurs(liaisons["valeur"], bas, haut),
        largeur=2 + 6 * np.sqrt(liaisons["prevus"] / liaisons["prevus"].max()),
        info=[
            f"<b>{a} ↔ {b}</b><br/>{nom_indicateur} : {v:.1f}<br/>"
            f"{int(p)} circulations prévues"
            for a, b, v, p in liaisons[
                ["gare_a", "gare_b", "valeur", "prevus"]
            ].itertuples(index=False)
        ],
    )
    # Les liaisons partagent souvent les mêmes voies :
    # les plus fines sont dessinées par-dessus
    liaisons = liaisons.sort_values("largeur", ascending=False)

    noms = sorted(set(liaisons["gare_a"]) | set(liaisons["gare_b"]))
    gares = pd.DataFrame(
        {
            "position": [GARES[g][::-1] for g in noms],
            "info": [f"<b>{g}</b>" for g in noms],
        }
    )

    couches = []
    if reseau is not None:
        couches.append(
            pdk.Layer(
                "PathLayer",
                pd.DataFrame({"path": [np.round(t, 4).tolist() for t in reseau]}),
                get_path="path",
                get_color=COULEUR_RESEAU,
                get_width=300,
                width_min_pixels=1,
            )
        )
    couches.append(
        pdk.Layer(
            "PathLayer",
            liaisons,
            get_path="itineraire",
            get_color="couleur",
            # width_units="pixels" n'est pas transmis par st.pydeck_chart : largeur en
            # mètres, calibrée pour le zoom initial (~3 km par pixel), bornée en pixels
            get_width="largeur * 3000",
            width_min_pixels=2,
            width_max_pixels=14,
            cap_rounded=True,
            joint_rounded=True,
            pickable=True,
            auto_highlight=True,
        )
    )
    couches.append(
        pdk.Layer(
            "ScatterplotLayer",
            gares,
            get_position="position",
            get_fill_color=COULEUR_GARE,
            get_line_color=[255, 255, 255],
            get_radius=4000,
            radius_min_pixels=3,
            stroked=True,
            line_width_min_pixels=1,
            pickable=True,
        )
    )
    return pdk.Deck(
        layers=couches,
        initial_view_state=pdk.ViewState(latitude=46.6, longitude=2.5, zoom=5),
        map_provider="carto",
        map_style=pdk.map_styles.CARTO_LIGHT,
        tooltip={"html": "{info}", "style": {"fontSize": "12px"}},
    )
