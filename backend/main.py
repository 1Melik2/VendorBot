from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import os
import shutil
import asyncio

from extractor import extract_invoice_data
from bot import run_bot
from scraper import scrape_pending_pos

#create the FastAPI app
app = FastAPI(title="VendorBot API")

# CORS = Cross-Origin Resource Sharing
# This allows your React frontend (running on localhost:5173)
# to talk to this backend (running on localhost:8000)
# Without this, the browser blocks the request for security
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # "*" = allow any frontend URL (fine for dev)
    allow_methods=["*"],        # allow GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],        # allow any headers
)


#health check endpoint
@app.get("/")
def health_check():
    return {"status": "running", "message": "VendorBot API is live"}


# Step 1: Quick check — extract PO from PDF and check if it's pending
@app.post("/api/check-invoice")
async def check_invoice(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # Save the uploaded PDF with its original filename
    tmp_dir = tempfile.mkdtemp()
    tmp_path = os.path.join(tmp_dir, file.filename)
    with open(tmp_path, "wb") as tmp:
        shutil.copyfileobj(file.file, tmp)

    try:
        invoice_data = extract_invoice_data(tmp_path)
        po_number = invoice_data.get("po_number", "")

        # Check if this PO is pending on VendorCafe
        pending_pos = await asyncio.to_thread(scrape_pending_pos)
        pending_po_numbers = {po["po_number"] for po in pending_pos}
        is_pending = po_number in pending_po_numbers

    except Exception as e:
        shutil.rmtree(tmp_dir)
        raise HTTPException(status_code=500, detail=str(e))

    if not is_pending:
        shutil.rmtree(tmp_dir)

    return {
        "invoice_data": invoice_data,
        "is_pending": is_pending,
        "tmp_dir": tmp_dir if is_pending else None,
        "tmp_path": tmp_path if is_pending else None,
        "message": f"PO #{po_number} is pending — ready to upload!" if is_pending
                   else f"PO #{po_number} is not pending — no upload needed",
    }


# Step 2: Actually upload the invoice to VendorCafe
@app.post("/api/upload-invoice")
async def upload_invoice(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    tmp_dir = tempfile.mkdtemp()
    tmp_path = os.path.join(tmp_dir, file.filename)
    with open(tmp_path, "wb") as tmp:
        shutil.copyfileobj(file.file, tmp)

    try:
        invoice_data = extract_invoice_data(tmp_path)
        await asyncio.to_thread(run_bot, invoice_data, tmp_path)
    except Exception as e:
        shutil.rmtree(tmp_dir)
        raise HTTPException(status_code=500, detail=str(e))

    shutil.rmtree(tmp_dir)
    return {"status": "success", "invoice_data": invoice_data, "message": f"PO #{invoice_data.get('po_number', '')} uploaded!"}


@app.get("/api/pending-pos")
async def get_pending_pos():
    try:
        pos = await asyncio.to_thread(scrape_pending_pos)
        return {"status": "success", "pos": pos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
