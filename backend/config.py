from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openrouter_api_key: str = ""
    openrouter_model: str = "meta-llama/llama-3.1-8b-instruct"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # Generation controls, tuned for an 8B model specifically.
    # Smaller models are more prone to drifting into incoherent output on
    # vague inputs, especially as generation length grows. Lower temperature
    # and a tighter token budget keep it closer to the prompt's examples
    # and reduce room to spiral.
    model_temperature: float = 0.3
    model_temperature_retry: float = 0.1  # fully deterministic on retry
    model_frequency_penalty: float = 0.5
    model_presence_penalty: float = 0.3
    model_max_tokens: int = 600  # tight budget; the prompt's length limits
                                  # mean this is plenty for a valid response

    request_timeout_seconds: float = 30.0
    max_description_length: int = 6000
    min_description_length: int = 15
    max_retries: int = 2

    # Dev-friendly default (24 hours) so repeated local testing sessions
    # don't keep hitting token expiry. Set this lower (e.g. 60) via .env
    # once you deploy anywhere real.
    access_token_expire_minutes: int = 60 * 24

    app_name: str = "AI Bug Investigator"
    environment: str = "development"
    allowed_origins: str = "*"
    log_level: str = "INFO"

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def cors_origins(self) -> list[str]:
        if self.allowed_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    @property
    def is_free_tier_model(self) -> bool:
        return self.openrouter_model.endswith(":free") or self.openrouter_model == "openrouter/free"

    @property
    def is_small_model(self) -> bool:
        """
        Rough heuristic flag for small/lower-capability models (by name),
        used only to log a startup note that quality-guard retries may
        fire more often on these than on larger models. Not a hard block --
        just visibility, so a spike in retries isn't a silent mystery later.
        """
        small_model_markers = ["8b", "7b", "3b", "1b", "mini", "haiku", "small"]
        model_lower = self.openrouter_model.lower()
        return any(marker in model_lower for marker in small_model_markers)


@lru_cache
def get_settings() -> Settings:
    return Settings()