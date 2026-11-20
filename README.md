# SNCF GOAT 🚄

Application Streamlit pour explorer et comparer la régularité des liaisons TGV.

**Application disponible en ligne :** https://sncf-goat.streamlit.app/

## Explorer les liaisons

- Carte interactive colorée selon le score sélectionné, avec une épaisseur proportionnelle au nombre de circulations prévues.
- Infobulles et tableau de classement pour comparer les liaisons, leur score et leur volume de trains.
- Filtres par période et par gare, sélection de la méthode de scoring et affichage optionnel du réseau ferré.

Les itinéraires dessinés sont reconstitués à partir du réseau ferré; ils ne représentent pas les sillons réellement empruntés par les trains.

## Lancer le projet

### Avec Python et uv

Prérequis : Python 3.13 ou supérieur et [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/Pip00wer/SNCF-Goat.git
cd SNCF-Goat
uv sync
uv run streamlit run app.py
```

L'application est accessible à l'adresse http://localhost:8501.

### Avec Docker

```bash
docker pull pip00wer/sncf-project:latest
docker run --rm -p 8501:8501 pip00wer/sncf-project:latest
```

L'application est accessible à l'adresse http://localhost:8501.

## Comprendre les scores

Les calculs portent sur les données agrégées par liaison et sur la période sélectionnée. Par défaut, les deux sens d'une liaison sont regroupés. Les scores 1, 2, 3 et 5 sont des notes où **100 est favorable**; le score 4 est exprimé en minutes et se lit à l'inverse : **plus il est bas, mieux c'est**.

Dans les formules, `prévus` désigne le nombre de circulations programmées, `réalisés` le nombre de trains non annulés, et `retard moyen tous trains` inclut les trains à l'heure. Les moyennes utilisées sont pondérées lors de l'agrégation des données.

### Score 1 — Taux de réussite

```text
100 × (réalisés − trains avec plus de 15 min de retard) / prévus
```

Une annulation ou un retard de **plus de** 15 minutes ne compte pas comme une réussite. Ce score, facile à interpréter, indique la part des trains prévus qui ont été réalisés sans retard important.

### Score 2 — Gravité des retards

```text
100 × (1 − (0,2 × retards de 15 à 30 min
          + 0,5 × retards de 30 à 60 min
          + 0,8 × retards de plus de 60 min
          + 1,0 × annulations) / prévus)
```

Les catégories sont exclusives : un retard de plus de 60 minutes est compté dans la catégorie la plus grave. Les coefficients sont les pondérations configurées dans le projet. Ce score distingue les petites perturbations des retards sévères et des annulations, qui ont un poids plus important.

### Score 3 — Efficacité relative à la durée du trajet

```text
100 × (1 − annulations / prévus)
    × (1 − retard moyen tous trains / durée moyenne du trajet)
```

Le score combine la part de trains non annulés et le retard rapporté à la durée moyenne du trajet. Il met ainsi les retards en perspective : à retard égal, l'impact relatif est plus fort sur un trajet court. Il est utile pour comparer les perturbations à l'échelle du voyage, plutôt qu'en minutes seules.

### Score 4 — Minutes de perturbation par train prévu

```text
(minutes de retard + coût estimé des annulations) / prévus
```

Les minutes de retard sont estimées à partir du retard moyen de tous les trains, y compris ceux à l'heure. Chaque annulation reçoit un coût calculé à partir de l'intervalle théorique entre les trains, augmenté de 10 % de la durée moyenne du trajet; ce coût est plafonné à 120 minutes par annulation. L'intervalle est estimé sur les minutes exploitables de 7 h à 22 h pour tous les jours des mois sélectionnés.

Le résultat est une mesure en minutes par circulation programmée. Son avantage est de réunir retards et annulations dans une unité concrète pour comparer le volume moyen de perturbation.

### Score 5 — Comparaison au P90 du réseau

```text
100 × (1 − 0,3 × pénalité_annulations − 0,7 × pénalité_retards)
```

Chaque pénalité compare la liaison au 90e percentile (P90) du réseau sur la période : le taux d'annulation pour l'une, le retard moyen de tous les trains pour l'autre. La pénalité est normalisée par rapport à ce seuil et plafonnée à 1. Les annulations comptent pour 30 % et les retards pour 70 % de la note.

Cette note situe une liaison par rapport aux performances du réseau, sans dépendre directement du volume de trains de chaque ligne. Elle est donc relative et peut évoluer lorsque les performances des autres liaisons changent.

Les moyennes de retard et de durée sont calculées lors de l'agrégation, et non à nouveau dans les fonctions de scoring. Une liaison sans score calculable n'est pas affichée pour l'indicateur choisi.

## Données

Le projet utilise les données mensuelles de régularité des TGV de l'AQST et les formes des lignes du réseau ferré de SNCF Réseau. Les résultats dépendent de la période choisie et des données disponibles.

## Tests

Pour lancer les tests :

```bash
uv run pytest
```

## CI/CD

Un workflow GitHub Actions est configuré pour s'exécuter à chaque push sur la branche `main`.

Il permet de :

- Installer les dépendances et exécuter les tests.
- Construire l'image Docker.
- Publier l'image sur Docker Hub si les tests passent.

Les identifiants Docker Hub sont stockés dans les GitHub Secrets (`DOCKERHUB_USERNAME` et `DOCKERHUB_TOKEN`).
