from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LLM APIs
    GOOGLE_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""

    # LLM Model Configuration
    # Clinical & Fashion
    CLINICAL_PRIMARY_MODEL: str = "openai/gpt-oss-120b:free"
    CLINICAL_BACKUP_MODEL: str = "google/gemini-2.5-flash"

    # Coding/AI Dev
    AIDEV_PRIMARY_MODEL: str = "stepfun/step-3.5-flash:free"
    AIDEV_BACKUP_MODEL: str = "arcee-ai/trinity-large-preview:free"

    # Finance
    FINANCE_PRIMARY_MODEL: str = "google/gemini-2.5-flash"
    FINANCE_BACKUP_MODEL: str = "arcee-ai/trinity-large-preview:free"

    # Default model settings
    DEFAULT_TEMPERATURE: float = 0.7
    DEFAULT_MAX_TOKENS: int = 4096

    # Database & State Persistence
    NEON_DATABASE_URL: str = ""

    # MCP Server Authentication
    GITHUB_TOKEN: str = ""

    # Application Settings
    ALLOWED_FS_PATH: str = "./dr_ikechukwu_pa"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    FLASK_SECRET_KEY: str = ""  # Must be set in production - generate with: python -c "import secrets; print(secrets.token_hex(32))"

    # Vector Database (Qdrant)
    QDRANT_API_KEY: str = ""
    QDRANT_URL: str = ""

    # Security Configuration
    CORS_ALLOWED_ORIGINS: str = ""
    DR_IKECHUKWU_PA_API_KEY: str = ""
    POSTGRES_PASSWORD: str = ""  # Must be set in production

    class Config:
        env_file = ".env"


settings = Settings()
