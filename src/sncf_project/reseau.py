"""Réseau ferré national (RFN) : tracés des lignes et itinéraires entre gares.

Les tracés des lignes exploitées forment un graphe (un nœud par point de tracé).
L'itinéraire d'une liaison est le chemin le plus rapide sur ce graphe, en
privilégiant les LGV. C'est une reconstitution : les données ne disent pas par
où passent réellement les TGV.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components, dijkstra
from scipy.spatial import cKDTree

from sncf_project.gares import ENTREES_RFN, GARES

# Codes ligne des LGV, repérés par leurs très grands rayons de courbe (> 3 km)
LGV = {
    752000,  # Sud-Est, Rhône-Alpes et Méditerranée
    431000,  # Atlantique (Paris - Tours)
    429000,  # Atlantique (branche Le Mans)
    408000,  # Bretagne - Pays de la Loire
    566000,  # Sud Europe Atlantique
    226000,  # Nord
    216000,  # Nord (branche Calais)
    5000,  # Est européenne
    14000,  # Rhin - Rhône
    834000,  # Contournement Nîmes - Montpellier
}
VITESSE_LGV_KMH = 300
VITESSE_CLASSIQUE_KMH = 140
# Les tracés ne se touchent pas toujours exactement aux jonctions (380 m de trou à Sète)
TOLERANCE_RACCORD_KM = 0.5


class GareInconnueError(ValueError):
    """Levée quand une gare n'a pas de coordonnées dans ``GARES``."""


def en_km(lon_lat: np.ndarray) -> np.ndarray:
    """Projette des points ``(lon, lat)`` en km.

    Projection équirectangulaire centrée sur la France : suffisante pour
    comparer des distances à l'échelle du pays.

    :param lon_lat: tableau de forme ``(n, 2)``.
    :return: tableau ``(n, 2)`` de coordonnées en km.
    """
    return np.column_stack(
        [lon_lat[:, 0] * 111.32 * np.cos(np.radians(46.5)), lon_lat[:, 1] * 110.57]
    )


class ReseauFerre:
    """Lignes exploitées du RFN et calcul d'itinéraires entre gares.

    :param chemin_csv: fichier ``formes-des-lignes-du-rfn.csv``.
    """

    def __init__(self, chemin_csv: Path) -> None:
        lignes = pd.read_csv(chemin_csv, sep=";")
        lignes = lignes[lignes["MNEMO"] == "EXPLOITE"]
        #: Tracé ``[[lon, lat], ...]`` de chaque tronçon exploité.
        self.traces: list[np.ndarray] = [
            np.array(json.loads(s)["coordinates"]) for s in lignes["Geo Shape"]
        ]
        self._construire_graphe(lignes["CODE_LIGNE"].isin(LGV).tolist())

    def _construire_graphe(self, sur_lgv: list[bool]) -> None:
        """Construit le graphe pondéré par le temps de parcours (en heures)."""
        points = np.concatenate(self.traces)
        # Un point commun à deux tracés (à 1 m près) devient un seul nœud
        self._xy, premier, noeud = np.unique(
            np.round(en_km(points), 3), axis=0, return_index=True, return_inverse=True
        )
        noeud = noeud.ravel()
        self._lon_lat = points[premier]

        sources, cibles, vitesses, extremites = [], [], [], []
        debut = 0
        for trace, lgv in zip(self.traces, sur_lgv):
            ids = noeud[debut : debut + len(trace)]
            debut += len(trace)
            sources.append(ids[:-1])
            cibles.append(ids[1:])
            vitesse = VITESSE_LGV_KMH if lgv else VITESSE_CLASSIQUE_KMH
            vitesses.append(np.full(len(ids) - 1, vitesse))
            extremites += [ids[0], ids[-1]]

        # Relie chaque extrémité de tracé aux nœuds proches pour combler les trous
        arbre = cKDTree(self._xy)
        for e in set(extremites):
            voisins = [
                v
                for v in arbre.query_ball_point(self._xy[e], r=TOLERANCE_RACCORD_KM)
                if v != e
            ]
            sources.append(np.full(len(voisins), e))
            cibles.append(np.array(voisins, dtype=int))
            vitesses.append(np.full(len(voisins), VITESSE_CLASSIQUE_KMH))

        s, c, v = (np.concatenate(x) for x in (sources, cibles, vitesses))
        durees = np.linalg.norm(self._xy[s] - self._xy[c], axis=1) / v + 1e-9
        n = len(self._xy)
        self._graphe = coo_matrix((durees, (s, c)), shape=(n, n)).tocsr()

        # Les gares ne s'accrochent qu'à la partie connexe principale du réseau
        _, composante = connected_components(self._graphe, directed=False)
        self._accroches = np.flatnonzero(composante == np.bincount(composante).argmax())
        self._arbre_accroches = cKDTree(self._xy[self._accroches])

    def _noeud_de_gare(self, gare: str) -> int:
        """Nœud du réseau le plus proche de la gare (ou de sa frontière)."""
        if gare not in GARES:
            raise GareInconnueError(f"Gare inconnue : {gare!r}")
        lat, lon = ENTREES_RFN.get(gare, GARES[gare])
        _, i = self._arbre_accroches.query(en_km(np.array([[lon, lat]]))[0])
        return int(self._accroches[i])

    def itineraire(self, gare_a: str, gare_b: str) -> list[list[float]]:
        """Itinéraire le plus rapide entre deux gares, le long des voies.

        Pour une gare étrangère, le tracé suit le réseau français jusqu'à la
        frontière puis rejoint la gare en ligne droite.

        :param gare_a: nom de la gare de départ (clé de ``GARES``).
        :param gare_b: nom de la gare d'arrivée (clé de ``GARES``).
        :return: liste de points ``[lon, lat]``.
        :raises GareInconnueError: si une des gares n'est pas dans ``GARES``.
        """
        depart, arrivee = self._noeud_de_gare(gare_a), self._noeud_de_gare(gare_b)
        _, predecesseurs = dijkstra(
            self._graphe, directed=False, indices=depart, return_predecessors=True
        )
        chemin = [arrivee]
        while chemin[-1] != depart:
            chemin.append(predecesseurs[chemin[-1]])
        trace = self._lon_lat[chemin[::-1]].tolist()

        if gare_a in ENTREES_RFN:
            trace.insert(0, GARES[gare_a][::-1])
        if gare_b in ENTREES_RFN:
            trace.append(GARES[gare_b][::-1])
        return np.round(trace, 4).tolist()
