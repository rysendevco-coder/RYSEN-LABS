from pathlib import Path

from app.config import load_app_cards


def test_load_seeded_app_cards() -> None:
    cards = load_app_cards(Path("config/apps.yml"))

    assert len(cards) == 7
    assert cards[0].name == "CasaOS"
    assert cards[-1].name == "Rysen Labs Dashboard"
