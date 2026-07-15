from pathlib import Path

from app.config import clear_settings_cache, get_settings
from app.services.app_registry import AppRegistry


def test_load_seeded_app_registry() -> None:
    apps, errors = AppRegistry(Path("config/apps.yml")).load()

    assert errors == []
    assert len(apps) == 7
    assert apps[0].id == "casaos"
    assert apps[-1].id == "rysen-labs-dashboard"


def test_legacy_apps_yml_is_supported(tmp_path: Path) -> None:
    config = tmp_path / "apps.yml"
    config.write_text(
        """
applications:
  - name: Legacy App
    url: http://127.0.0.1:8080
    description: Old shape
    category: Apps
    container_names:
      - legacy
""",
        encoding="utf-8",
    )

    apps, errors = AppRegistry(config).load()

    assert errors == []
    assert apps[0].id == "legacy-app"
    assert apps[0].container_name == "legacy"


def test_invalid_apps_yml_returns_useful_error(tmp_path: Path) -> None:
    config = tmp_path / "apps.yml"
    config.write_text("applications:\n  - id: bad id\n    name: Bad\n", encoding="utf-8")

    apps, errors = AppRegistry(config).load()

    assert apps == []
    assert "Application entry 1 is invalid" in errors[0]


def test_environment_overrides(monkeypatch) -> None:
    clear_settings_cache()
    monkeypatch.setenv("DASHBOARD_PORT", "9090")
    monkeypatch.setenv("ENABLE_DOCKER_INTEGRATION", "true")
    monkeypatch.setenv("ENABLE_GIT_INTEGRATION", "true")
    monkeypatch.setenv("GIT_COMMAND_TIMEOUT_SECONDS", "3")
    monkeypatch.setenv("GIT_MAX_REPOSITORIES", "12")
    monkeypatch.setenv("GIT_SCAN_CACHE_SECONDS", "7")
    monkeypatch.setenv("SAFE_MODE", "true")

    settings = get_settings()

    assert settings.dashboard_port == 9090
    assert settings.enable_docker_integration is True
    assert settings.enable_git_integration is True
    assert settings.git_command_timeout_seconds == 3
    assert settings.git_max_repositories == 12
    assert settings.git_scan_cache_seconds == 7
    assert settings.safe_mode is True
    clear_settings_cache()
