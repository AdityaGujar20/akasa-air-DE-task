from fastapi import APIRouter, HTTPException
from loguru import logger
from app.ingestion.db_loader import run_db_loader

router = APIRouter(prefix="/db", tags=["DB Loader"])


@router.post("/load")
def load_data_to_db():
    logger.info("API Trigger: Loading data into MySQL...")
    try:
        run_db_loader()
        return {"message": "Data loaded into database successfully!", "status": "success"}
    except FileNotFoundError as e:
        logger.error(f"File not found error: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except ConnectionError as e:
        logger.error(f"Database connection error: {e}")
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        logger.error(f"Database setup error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load data: {str(e)}")
