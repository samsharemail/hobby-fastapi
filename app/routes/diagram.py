# app/routes/diagram.py
from fastapi import APIRouter, UploadFile, File, Form
import os
from app.utils.zip_handler import extract_zip
from app.services.parser_service import parse_dotnet_project
from app.services.mermaid_builder import build_mermaid

router = APIRouter()

@router.post("/generate-from-zip")
async def generate_from_zip(
    file: UploadFile = File(...),
    selected_controller: str = Form(None)
):
    # save zip
    zip_path = f"temp_{file.filename}"
    with open(zip_path, "wb") as buffer:
        buffer.write(await file.read())

    extracted_path = extract_zip(zip_path)

    architecture, controllers_sorted = parse_dotnet_project(extracted_path)

    # if client passed a selected_controller use it (otherwise None)
    mermaid = build_mermaid(architecture, selected_controller)

    # return controllers_sorted so frontend can offer selection
    return {
        "architecture": architecture,
        "controllers_sorted": controllers_sorted,
        "mermaid": mermaid
    }