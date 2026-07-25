import os
import uuid
import time
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from backend.app.api.dependencies import get_mongo_service, get_current_client_id
from backend.app.services.mongo_service import MongoService
from backend.app.services.template_parser import parse_template_file
from backend.app.schemas.template_schemas import (
    TemplateUploadResponse,
    TemplateListResponse,
    TemplateMetadataResponse
)
from backend.app.core.exceptions import SecurityError

router = APIRouter()

MAX_FILE_SIZE = 15 * 1024 * 1024  # 15 MB limit
ALLOWED_EXTENSIONS = {".docx", ".pptx"}
STORAGE_BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "storage", "templates")
)

@router.post("/templates/upload", response_model=TemplateUploadResponse)
async def upload_template(
    client_id: str = Form(...),
    template_name: str = Form(...),
    description: str = Form(...),
    file: UploadFile = File(...),
    mongo: MongoService = Depends(get_mongo_service),
    auth_client_id: str = Depends(get_current_client_id)
):
    """
    Accepts template file (.docx/.pptx) upload for a client.
    Enforces tenant isolation, file extension check, and 15MB size limit.
    Parses structure into extracted_structure and stores original on disk.
    """
    if client_id != auth_client_id:
        raise SecurityError("Tenant isolation mismatch")

    filename = file.filename or ""
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{ext}'. Only .docx and .pptx files are allowed."
        )

    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds maximum allowed limit of 15MB (file size: {len(file_bytes)} bytes)."
        )

    template_id = f"tmpl_{uuid.uuid4().hex[:12]}"
    file_type = ext.lstrip(".")

    # Step 1: Parse structure using python-docx / python-pptx
    try:
        extracted_structure = parse_template_file(file_bytes, filename)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to parse template document structure: {str(e)}"
        )

    # Step 2: Write original file to disk
    client_storage_dir = os.path.join(STORAGE_BASE_DIR, client_id)
    os.makedirs(client_storage_dir, exist_ok=True)
    storage_path = os.path.join(client_storage_dir, f"{template_id}{ext}")
    with open(storage_path, "wb") as f:
        f.write(file_bytes)

    # Step 3: Insert metadata + extracted_structure into Mongo
    doc = {
        "template_id": template_id,
        "client_id": client_id,
        "template_name": template_name,
        "description": description,
        "original_filename": filename,
        "file_type": file_type,
        "storage_path": storage_path,
        "extracted_structure": extracted_structure,
        "uploaded_at": int(time.time())
    }
    mongo.save_template(doc)

    return TemplateUploadResponse(
        status="success",
        template_id=template_id,
        template_name=template_name,
        message="Template uploaded, parsed, and stored successfully."
    )


@router.get("/templates/list", response_model=TemplateListResponse)
async def list_templates(
    client_id: str,
    mongo: MongoService = Depends(get_mongo_service),
    auth_client_id: str = Depends(get_current_client_id)
):
    """
    Returns list of template metadata documents for the authenticated client.
    """
    if client_id != auth_client_id:
        raise SecurityError("Tenant isolation mismatch")

    templates = mongo.list_templates(client_id=client_id)
    response_items = []
    for item in templates:
        response_items.append(TemplateMetadataResponse(
            template_id=item["template_id"],
            client_id=item["client_id"],
            template_name=item["template_name"],
            description=item.get("description", ""),
            original_filename=item.get("original_filename", ""),
            file_type=item.get("file_type", ""),
            uploaded_at=item.get("uploaded_at", int(time.time()))
        ))

    return TemplateListResponse(status="success", templates=response_items)


@router.get("/templates/download/{template_id}")
async def download_template(
    template_id: str,
    mongo: MongoService = Depends(get_mongo_service),
    auth_client_id: str = Depends(get_current_client_id)
):
    """
    Streams back original uploaded template file after verifying client ownership.
    """
    try:
        template = mongo.get_template_by_id(template_id=template_id, client_id=auth_client_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Template with ID '{template_id}' not found.")
    except ValueError as ve:
        raise HTTPException(status_code=403, detail=str(ve))
    except Exception:
        raise HTTPException(status_code=404, detail="Template not found.")

    storage_path = template.get("storage_path")
    if not storage_path or not os.path.exists(storage_path):
        raise HTTPException(status_code=404, detail="Original template file not found on storage server.")

    original_filename = template.get("original_filename", f"{template_id}.{template.get('file_type', 'bin')}")
    return FileResponse(
        path=storage_path,
        filename=original_filename,
        media_type="application/octet-stream"
    )
