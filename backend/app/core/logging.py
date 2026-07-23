import logging
import sys
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from app.core.config import settings

def setup_logging() -> None:
    """Configure structured logging and Sentry integration."""
    
    # Configure baseline logging format
    log_format = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
    
    logging.basicConfig(
        level=logging.INFO if settings.ENVIRONMENT == "production" else logging.DEBUG,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set logging level for noisy packages
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("pdfminer").setLevel(logging.WARNING)
    logging.getLogger("pdfplumber").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.ENVIRONMENT == "development" else logging.WARN
    )

    # Initialize Sentry if DSN is set
    if settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.ENVIRONMENT,
            integrations=[FastApiIntegration()],
            traces_sample_rate=1.0 if settings.ENVIRONMENT != "production" else 0.1,
            profiles_sample_rate=1.0 if settings.ENVIRONMENT != "production" else 0.1,
        )
        logging.info("Sentry integration initialized successfully.")
    else:
        logging.info("Sentry DSN not provided. Skipping Sentry initialization.")
