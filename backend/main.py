from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import os
import shutil

from extractor import extract_invoice_data
from bot import run_bot

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


#main endpoint, receives a PDF invoice and processes it
@app.post("/api/upload-invoice")
async def upload_invoice(file: UploadFile = File(...)):

    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")


    # Save the uploaded PDF to a temporary file

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        invoice_data = extract_invoice_data(tmp_path)
        run_bot(invoice_data, tmp_path)
        
    except Exception as e:
        os.unlink(tmp_path)
        raise HTTPException(status_code=500, detail=str(e))
    
    #clean up the temp file and return the result
    os.unlink(tmp_path)
    return {"status": "success", "invoice_data": invoice_data}

