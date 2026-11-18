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
uv venv

# Installer les dépendances
uv sync

# Lancer l'application
uv run streamlit run app.py
```

L'application sera accessible sur http://localhost:8501.

### Avec Docker

Il est également possible de lancer l'application directement avec Docker.

```bash
# Récupérer l'image
docker pull <DOCKERHUB_USERNAME>/sncf-project:latest

# Lancer le conteneur
docker run -p 8501:8501 <DOCKERHUB_USERNAME>/sncf-project:latest
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