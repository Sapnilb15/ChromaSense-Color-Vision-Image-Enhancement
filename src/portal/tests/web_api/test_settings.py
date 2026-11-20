import pytest

from chromasense.main.settings import Settings


def test_defaults_when_unset():
    assert Settings.from_env({}) == Settings(
        data_dir="/data", confusion_threshold=10.0, palette_colors=12, idle_minutes=30.0
    )


def test_values_come_from_the_environment():
    settings = Settings.from_env(
        {
            "CHROMASENSE_DATA_DIR": "/tmp/x",
            "CHROMASENSE_CONFUSION_THRESHOLD": "8",
            "CHROMASENSE_PALETTE_COLORS": "16",
            "CHROMASENSE_IDLE_MINUTES": "5",
        }
    )
    assert settings == Settings("/tmp/x", 8.0, 16, 5.0)


def test_blank_values_use_defaults():
    assert Settings.from_env({"CHROMASENSE_IDLE_MINUTES": "  "}).idle_minutes == 30.0


@pytest.mark.parametrize(
    "env",
    [
        {"CHROMASENSE_CONFUSION_THRESHOLD": "0"},
        {"CHROMASENSE_PALETTE_COLORS": "0"},
        {"CHROMASENSE_IDLE_MINUTES": "-1"},
        {"CHROMASENSE_IDLE_MINUTES": "soon"},
    ],
)
def test_invalid_values_stop_startup(env):
    with pytest.raises(ValueError):
        Settings.from_env(env)
