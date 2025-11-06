from fastapi import APIRouter, UploadFile, File
import shutil
import os

router = APIRouter(prefix="/upload", tags=["Upload"])

UPLOAD_DIR = "data/upload"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/customers")
async def upload_customers(file: UploadFile = File(...)):
    save_path = os.path.join(UPLOAD_DIR, "customers.csv")
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"message": "customers.csv uploaded successfully"}

@router.post("/orders")
async def upload_orders(file: UploadFile = File(...)):
    save_path = os.path.join(UPLOAD_DIR, "orders.xml")
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"message": "orders.xml uploaded successfully"}
