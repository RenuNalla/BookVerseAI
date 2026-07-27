from app.core.config import Settings


def test_cors_origins_accepts_comma_separated_string(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:4200,http://localhost:8080")

    settings = Settings()

    assert settings.get_cors_origins() == [
        "http://localhost:4200",
        "http://localhost:8080",
    ]
