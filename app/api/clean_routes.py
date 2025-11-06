from fastapi import APIRouter
from loguru import logger

from app.ingestion.cleaning_pipeline import run_cleaning_pipeline

router = APIRouter(prefix="/clean", tags=["Cleaning"])


@router.post("/")
def clean_data():
    logger.info("API Trigger: Running cleaning pipeline...")
    run_cleaning_pipeline()
    return {"message": "Cleaning pipeline executed successfully"}
