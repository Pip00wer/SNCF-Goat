"""Coordonnées (lat, lon) des gares présentes dans le jeu de régularité TGV (AQST).

Le jeu AQST ne fournit que des noms de gares : on les géolocalise à la main.
"ITALIE" est une destination agrégée, placée arbitrairement à Milano Centrale.
"""

GARES: dict[str, tuple[float, float]] = {
    "AIX EN PROVENCE TGV": (43.4553, 5.3173),
    "ANGERS SAINT LAUD": (47.4646, -0.5562),
    "ANGOULEME": (45.6534, 0.1650),
    "ANNECY": (45.9020, 6.1220),
    "ARRAS": (50.2867, 2.7811),
    "AVIGNON TGV": (43.9216, 4.7860),
    "BARCELONA": (41.3791, 2.1402),
    "BELLEGARDE (AIN)": (46.1084, 5.8260),
    "BESANCON FRANCHE COMTE TGV": (47.3075, 5.9547),
    "BORDEAUX ST JEAN": (44.8259, -0.5562),
    "BREST": (48.3881, -4.4799),
    "CHAMBERY CHALLES LES EAUX": (45.5714, 5.9196),
    "DIJON VILLE": (47.3234, 5.0274),
    "DOUAI": (50.3713, 3.0903),
    "DUNKERQUE": (51.0306, 2.3684),
    "FRANCFORT": (50.1070, 8.6632),
    "GENEVE": (46.2101, 6.1424),
    "GRENOBLE": (45.1914, 5.7146),
    "ITALIE": (45.4862, 9.2046),
    "LA ROCHELLE VILLE": (46.1525, -1.1453),
    "LAUSANNE": (46.5168, 6.6291),
    "LAVAL": (48.0761, -0.7613),
    "LE CREUSOT MONTCEAU MONTCHANIN": (46.7656, 4.4994),
    "LE MANS": (47.9954, 0.1923),
    "LILLE": (50.6390, 3.0757),
    "LYON PART DIEU": (45.7606, 4.8594),
    "MACON LOCHE": (46.2817, 4.7792),
    "MADRID": (40.4066, -3.6892),
    "MARNE LA VALLEE": (48.8700, 2.7828),
    "MARSEILLE ST CHARLES": (43.3027, 5.3806),
    "METZ": (49.1098, 6.1773),
    "MONTPELLIER": (43.6047, 3.8806),
    "MULHOUSE VILLE": (47.7417, 7.3428),
    "NANCY": (48.6898, 6.1743),
    "NANTES": (47.2173, -1.5420),
    "NICE VILLE": (43.7046, 7.2618),
    "NIMES": (43.8325, 4.3660),
    "PARIS EST": (48.8768, 2.3592),
    "PARIS LYON": (48.8443, 2.3744),
    "PARIS MONTPARNASSE": (48.8412, 2.3203),
    "PARIS NORD": (48.8809, 2.3553),
    "PARIS VAUGIRARD": (48.8380, 2.3170),
    "PERPIGNAN": (42.6960, 2.8796),
    "POITIERS": (46.5822, 0.3330),
    "QUIMPER": (47.9946, -4.0915),
    "REIMS": (49.2590, 4.0244),
    "RENNES": (48.1035, -1.6723),
    "SAINT ETIENNE CHATEAUCREUX": (45.4433, 4.3995),
    "ST MALO": (48.6475, -2.0040),
    "ST PIERRE DES CORPS": (47.3858, 0.7238),
    "STRASBOURG": (48.5850, 7.7344),
    "STUTTGART": (48.7840, 9.1817),
    "TOULON": (43.1283, 5.9295),
    "TOULOUSE MATABIAU": (43.6113, 1.4536),
    "TOURCOING": (50.7163, 3.1695),
    "TOURS": (47.3897, 0.6937),
    "VALENCE ALIXAN TGV": (44.9910, 4.9786),
    "VANNES": (47.6644, -2.7520),
    "ZURICH": (47.3779, 8.5403),
}

# Gares hors du réseau français : point de passage frontière (lat, lon) où l'itinéraire
# quitte le RFN, avant de rejoindre la gare en ligne droite.
ENTREES_RFN: dict[str, tuple[float, float]] = {
    "BARCELONA": (42.4700, 2.8600),  # Le Perthus
    "MADRID": (42.4700, 2.8600),  # Le Perthus
    "FRANCFORT": (49.1883, 6.8964),  # Forbach
    "STUTTGART": (48.5745, 7.7980),  # Strasbourg - Kehl
    "ZURICH": (47.5905, 7.5590),  # Saint-Louis - Bâle
    "LAUSANNE": (46.7051, 6.3790),  # Vallorbe
    "ITALIE": (45.1906, 6.6589),  # Modane
}
