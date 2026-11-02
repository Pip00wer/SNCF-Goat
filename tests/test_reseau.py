"""Tests des itinéraires calculés sur le vrai réseau ferré."""

from pathlib import Path

import numpy as np
import pytest

from sncf_project.gares import GARES
from sncf_project.reseau import GareInconnueError, ReseauFerre, en_km

CSV_RFN = Path(__file__).parents[1] / "data" / "formes-des-lignes-du-rfn.csv"


@pytest.fixture(scope="module")
def reseau() -> ReseauFerre:
    """Réseau chargé une seule fois pour tous les tests (~0,3 s)."""
    return ReseauFerre(CSV_RFN)


def distance_km(point: list[float], lat: float, lon: float) -> float:
    """Distance entre un point ``[lon, lat]`` et une position ``(lat, lon)``."""
    a, b = en_km(np.array([point, [lon, lat]]))
    return float(np.linalg.norm(a - b))


def passe_par(trace: list[list[float]], lat: float, lon: float) -> bool:
    """Vrai si l'itinéraire passe à moins de 10 km de la position."""
    return min(distance_km(p, lat, lon) for p in trace) < 10


def test_itineraire_va_d_une_gare_a_l_autre(reseau: ReseauFerre) -> None:
    trace = reseau.itineraire("LYON PART DIEU", "MARSEILLE ST CHARLES")
    assert distance_km(trace[0], *GARES["LYON PART DIEU"]) < 2
    assert distance_km(trace[-1], *GARES["MARSEILLE ST CHARLES"]) < 2


def test_itineraire_privilegie_les_lgv(reseau: ReseauFerre) -> None:
    # Plus court en km par Limoges, mais les TGV passent par la LGV et Bordeaux
    trace = reseau.itineraire("PARIS MONTPARNASSE", "TOULOUSE MATABIAU")
    assert passe_par(trace, *GARES["BORDEAUX ST JEAN"])
    assert not passe_par(trace, 45.836, 1.268)  # Limoges


def test_raccord_de_sete(reseau: ReseauFerre) -> None:
    # Sans le raccord des tracés à Sète, l'itinéraire contournait par la Lozère
    trace = reseau.itineraire("MONTPELLIER", "PERPIGNAN")
    assert passe_par(trace, 43.412, 3.696)  # Sète


def test_gares_etrangeres_rejointes_depuis_la_frontiere(reseau: ReseauFerre) -> None:
    trace = reseau.itineraire("FRANCFORT", "ITALIE")
    assert distance_km(trace[0], *GARES["FRANCFORT"]) < 0.1
    assert distance_km(trace[-1], *GARES["ITALIE"]) < 0.1
    assert passe_par(trace, 49.19, 6.90)  # Forbach
    assert passe_par(trace, 45.19, 6.66)  # Modane


def test_gare_inconnue(reseau: ReseauFerre) -> None:
    with pytest.raises(GareInconnueError):
        reseau.itineraire("PARIS", "LYON PART DIEU")
