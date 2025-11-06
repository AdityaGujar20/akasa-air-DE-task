from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.upload_routes import router as upload_router
from app.api.db_load_routes import router as db_loader_router
from app.api.kpi_db_routes import router as kpi_db_router
from app.api.kpi_memory_routes import router as kpi_memory_router

from app.ingestion.cleaning_pipeline import run_cleaning_pipeline

from app.db.connection import Base, engine


app = FastAPI(
    title="Akasa Air Data Pipeline",
    description="Data ingestion, cleaning, loading, and KPI generation",
    version="1.0.0",
)

@app.on_event("startup")
def create_tables():
    Base.metadata.create_all(bind=engine)
    print("Tables created automatically on startup.")


app.include_router(upload_router)
app.include_router(db_loader_router)
app.include_router(kpi_db_router)
app.include_router(kpi_memory_router)

@app.post("/clean")
def clean_data():
    run_cleaning_pipeline()
    return {"message": "Cleaning pipeline completed"}


app.mount("/static", StaticFiles(directory="app/ui/static"), name="static")
templates = Jinja2Templates(directory="app/ui/templates")


@app.get("/ui")
def ui_dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})
