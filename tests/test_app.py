from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).parents[1] / "app.py"


def test_application_demarre_et_affiche_les_filtres() -> None:
    app = AppTest.from_file(str(APP)).run(timeout=60)

    assert not app.exception
    assert len(app.selectbox) == 1
    assert len(app.multiselect) == 1
    assert app.title[0].value.startswith("Affichage de différents")


def test_selection_du_score_met_a_jour_l_indicateur() -> None:
    app = AppTest.from_file(str(APP)).run(timeout=60)
    app.selectbox[0].set_value("score_5").run(timeout=60)

    assert not app.exception
    assert any("P90 réseau" in element.value for element in app.markdown)