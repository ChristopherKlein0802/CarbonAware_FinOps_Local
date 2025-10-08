"""Central application configuration with optional pydantic dependency."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

try:  # pragma: no cover
    from dotenv import load_dotenv  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    load_dotenv = lambda *args, **kwargs: None  # type: ignore

load_dotenv()

try:
    from pydantic import Field  # type: ignore

    try:
        from pydantic import AliasChoices  # type: ignore
    except ImportError:  # pragma: no cover - AliasChoices introduced in pydantic v2
        AliasChoices = None  # type: ignore[assignment]
    try:  # Pydantic v2 exposes HttpUrl at top level
        from pydantic import HttpUrl  # type: ignore
    except ImportError:  # pragma: no cover - fallback for older/newer variants
        try:
            from pydantic.networks import HttpUrl  # type: ignore[attr-defined]
        except ImportError:  # Final fallback if HttpUrl is missing entirely
            HttpUrl = str  # type: ignore[misc,assignment]
    try:
        from pydantic_settings import BaseSettings  # type: ignore

        try:
            from pydantic_settings import SettingsConfigDict  # type: ignore
        except ImportError:  # pragma: no cover - pydantic-settings v1 style
            SettingsConfigDict = None  # type: ignore[assignment]
    except ModuleNotFoundError:  # pragma: no cover - align with fallback handling
        raise ImportError from None
except (ModuleNotFoundError, ImportError):  # pragma: no cover - lightweight fallback for environments without pydantic

    class Settings:  # type: ignore[override]
        def __init__(self) -> None:
            self.aws_profile: str = os.getenv("AWS_PROFILE", "carbon-finops-sandbox")
            self.aws_region: str = os.getenv("AWS_REGION", "eu-central-1")
            self.electricitymaps_api_key: str | None = os.getenv("ELECTRICITYMAP_API_KEY")
            self.electricitymaps_base_url: str = os.getenv(
                "ELECTRICITYMAP_BASE_URL", "https://api-access.electricitymaps.com/v3"
            )
            self.enable_hourly_carbon_collection: bool = os.getenv(
                "ENABLE_HOURLY_CARBON_COLLECTION", "false"
            ).strip().lower() in {"1", "true", "yes", "on"}
            self.boavizta_base_url: str = os.getenv("BOAVIZTA_BASE_URL", "https://api.boavizta.org/v1")
            self.http_timeout_seconds: float = float(os.getenv("HTTP_TIMEOUT_SECONDS", "30"))
            self.cache_root: Path = Path(os.getenv("CACHE_ROOT", ".cache"))
            # Financial constants
            self.eur_usd_rate: float = float(os.getenv("EUR_USD_RATE", "0.92"))  # ECB official rate
            self.aws_region_to_zone: Dict[str, str] = {
                "eu-central-1": "DE",
                "eu-west-1": "IE",
                "eu-west-2": "GB",
                "eu-west-3": "FR",
                "eu-north-1": "SE",
                "us-east-1": "US-NE-ISO",
                "us-west-2": "US-NW-PACW",
            }
            self.aws_pricing_region_labels: Dict[str, str] = {
                "eu-central-1": "EU (Frankfurt)",
                "eu-west-1": "EU (Ireland)",
                "us-east-1": "US East (N. Virginia)",
                "us-west-2": "US West (Oregon)",
            }

    settings = Settings()
else:

    def _env_alias(name: str) -> dict[str, Any]:
        if AliasChoices:
            return {"validation_alias": AliasChoices(name)}
        return {"env": name}

    class Settings(BaseSettings):
        if "SettingsConfigDict" in globals() and SettingsConfigDict is not None:
            model_config = SettingsConfigDict(
                env_file=".env",
                env_file_encoding="utf-8",
                extra="ignore",
            )

        aws_profile: str = Field(default="carbon-finops-sandbox", **_env_alias("AWS_PROFILE"))
        aws_region: str = Field(default="eu-central-1", **_env_alias("AWS_REGION"))

        electricitymaps_api_key: str | None = Field(default=None, **_env_alias("ELECTRICITYMAP_API_KEY"))

        electricitymaps_base_url: HttpUrl = Field(
            default="https://api-access.electricitymaps.com/v3",
            **_env_alias("ELECTRICITYMAP_BASE_URL"),
        )
        enable_hourly_carbon_collection: bool = Field(
            default=False,
            **_env_alias("ENABLE_HOURLY_CARBON_COLLECTION"),
        )

        boavizta_base_url: HttpUrl = Field(
            default="https://api.boavizta.org/v1",
            **_env_alias("BOAVIZTA_BASE_URL"),
        )

        http_timeout_seconds: float = Field(default=30.0, **_env_alias("HTTP_TIMEOUT_SECONDS"))

        cache_root: Path = Field(default=Path(".cache"), **_env_alias("CACHE_ROOT"))

        # Financial constants
        eur_usd_rate: float = Field(default=0.92, **_env_alias("EUR_USD_RATE"))  # ECB official rate

        aws_region_to_zone: Dict[str, str] = Field(
            default_factory=lambda: {
                "eu-central-1": "DE",
                "eu-west-1": "IE",
                "eu-west-2": "GB",
                "eu-west-3": "FR",
                "eu-north-1": "SE",
                "us-east-1": "US-NE-ISO",
                "us-west-2": "US-NW-PACW",
            }
        )
        aws_pricing_region_labels: Dict[str, str] = Field(
            default_factory=lambda: {
                "eu-central-1": "EU (Frankfurt)",
                "eu-west-1": "EU (Ireland)",
                "us-east-1": "US East (N. Virginia)",
                "us-west-2": "US West (Oregon)",
            }
        )

        if SettingsConfigDict is None:

            class Config:  # type: ignore[override]
                env_file = ".env"
                env_file_encoding = "utf-8"

    settings = Settings()
