import pdfplumber
import re
import os


def extract_invoice_data(pdf_path: str) -> dict:
    with pdfplumber.open(pdf_path) as pdf:
        full_text = ""
        for page in pdf.pages:
            full_text += page.extract_text() or ""
    
    #print("--- RAW TEXT ----")
    #print(full_text)
    print("----------------")

    #getting what I need from the pdf

    po_match = re.search(r"Po:\s*(\d+)", full_text)  

    inv_match = re.search(r"Invoice no\.:\s*(\d+)", full_text)

    date_match = re.search(r"Invoice date:\s*(\d{2}\/\d{2}\/\d{4})", full_text)

    total_match = re.search(r"Total\s*\$([\d,]+\.\d{2})", full_text)

    return {
        "po_number": po_match.group(1) if po_match else None,
        "invoice_num": inv_match.group(1) if inv_match else None,
        "date": date_match.group(1) if date_match else None,
        "total": total_match.group(1) if total_match else None,
    }


if __name__ == "__main__":
    for invoice in os.listdir("sample_invoices"):
        if invoice.endswith(".pdf"):
            result = extract_invoice_data(f"sample_invoices/{invoice}")
            print(result)
