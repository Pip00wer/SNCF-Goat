# SNCF GOAT 🚄

Application développée avec Streamlit.

**Application disponible en ligne :** https://sncf-goat.streamlit.app/

## Lancer le projet en local

Deux méthodes sont possibles pour lancer l'application.

### Avec Python et uv

Prérequis : Python 3.13+ et [uv](https://docs.astral.sh/uv/).

```bash
# Cloner le projet
git clone https://github.com/Pip00wer/SNCF-Goat.git
cd SNCF-Goat

# Créer l'environnement virtuel
uv venv --python 3.13

# Installer les dépendances
uv sync

# Lancer l'application
uv run streamlit run app.py
```

L'application sera accessible sur http://localhost:8501.

### Comparer les cinq scores

Lancer la carte expérimentale avec `uv run streamlit run app_test.py`.
Les deux scores supplémentaires sont calculés sur la période sélectionnée :

- **score_4** : minutes équivalentes de perturbation par train prévu
  (retards et coût des annulations : `minutes_exploitables / nb_prevues + 0.1 * moy_durée`,
  pénalité plafonnée à 120 minutes).
  Le temps exploitable couvre 7 h à 22 h chaque jour de la période sélectionnée,
  soit 900 minutes par jour, avec les mois de début et de fin inclus en entier
  (27 000 minutes pour 30 jours).
  Une valeur faible est favorable.
- **score_5** : note sur 100 relative au P90 des liaisons sur toute la période,
  avec 30 % de pénalité d'annulation et 70 % de pénalité de retard moyen
  de tous les trains, y compris ceux à l'heure (`retard_moy_all`).

Les deux sens d'une liaison sont fusionnés par `aggregate_by_ligne`.
Les scores 4 et 5 réutilisent directement les moyennes pondérées sur la période :
`retard_moy_all` pour le coût total des retards et la comparaison au P90 réseau,
et `moy_durée` pour la pénalité d'annulation.
Les moyennes ne sont pas recalculées dans le scoring.
Le filtre par gare est appliqué après les scores pour garder une référence réseau.
Une liaison sans score calculable n'est pas affichée pour l'indicateur choisi.

### Avec Docker

Il est également possible de lancer l'application directement avec Docker.

```bash
# Récupérer l'image
docker pull pip00wer/sncf-project:latest

# Lancer le conteneur
docker run -p 8501:8501 pip00wer/sncf-project:latest
```

L'application sera accessible sur http://localhost:8501.

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