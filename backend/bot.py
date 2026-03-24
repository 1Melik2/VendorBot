from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import os

load_dotenv()

DASHBOARD_URL = "https://prod.vendorcafe.com/content2/todo"
AUTH_SESSION_FILE = "auth_session.json"


def login_manually(page):
    """Opens the login page and waits for you to log in manually."""
    page.goto("https://www.vendorcafe.com/vendorcafe/")
    print("Please log in manually (solve reCAPTCHA, enter credentials)...")
    # YOUR TURN: wait until you're on the dashboard
    # Hint: page.wait_for_url() can wait until the URL changes to the dashboard
    # page.wait_for_url("**/content2/**", timeout=120000)  # 2 min to log in
    print("Login successful!")


def is_logged_in(page):
    """Check if we landed on the dashboard or got redirected to login."""
    # YOUR TURN: figure out how to tell if you're logged in
    # Hint: check the current URL — does it contain "content2" or "login"?
    pass


def navigate_to_purchase_orders(page):
    """Navigate from dashboard to Client Profiles > Purchase Order tab."""
    # YOUR TURN: use the selectors from your notes
    # Step 1: Click "Client Profiles" tab
    # Hint: page.click() with the right selector
    
    # Step 2: Click "Purchase Order" tab
    # Hint: look at the selector you found — it has an href attribute
    
    pass


def find_and_click_po(page, po_number: str):
    """Find the PO number in the list and click it."""
    # YOUR TURN: find the right PO in the table
    # Hint: page.get_by_text() or page.locator() can find elements by text
    # Remember: the PO number is a purple link/button in a table cell
    
    pass


def handle_create_invoice_popups(page):
    """Click Create Invoice, handle the popups, get to the upload page."""
    # YOUR TURN: there are multiple steps here from your notes
    # Step 1: Click "Create Invoice" button
    
    # Step 2: Click "Upload a PDF Invoice" tab
    
    # Step 3: Click "OK" on the "Leave Page?" popup
    
    # Step 4: Click "Close" on the Purchase Order Details popup
    
    pass


def fill_and_submit_invoice(page, invoice_data: dict, pdf_path: str):
    """Upload PDF, fill in invoice details, and submit."""
    # YOUR TURN: this is where the magic happens
    # Step 1: Upload the PDF file
    # Hint: page.set_input_files("#pdfFileInput", pdf_path)
    
    # Step 2: Fill in Invoice No.
    # Hint: page.fill("#invoiceNoInput", invoice_data["invoice_num"])
    
    # Step 3: Fill in Invoice Date
    # Hint: page.fill("#invoiceDateInput", invoice_data["date"])
    
    # Step 4: Click Submit
    
    pass


def run_bot(invoice_data: dict, pdf_path: str):
    """Main bot function — ties everything together."""
    with sync_playwright() as p:
        # Try to load saved session, otherwise start fresh
        if os.path.exists(AUTH_SESSION_FILE):
            context = p.chromium.launch(headless=False).new_context(
                storage_state=AUTH_SESSION_FILE
            )
        else:
            context = p.chromium.launch(headless=False).new_context()

        page = context.new_page()
        page.goto(DASHBOARD_URL)
        page.wait_for_load_state("networkidle")

        # Check if we need to log in
        if not is_logged_in(page):
            login_manually(page)
            # Save session so we don't have to log in next time
            context.storage_state(path=AUTH_SESSION_FILE)
            print("💾 Session saved!")

        # YOUR TURN: call your functions in order
        # navigate_to_purchase_orders(page)
        # find_and_click_po(page, invoice_data["po_number"])
        # handle_create_invoice_popups(page)
        # fill_and_submit_invoice(page, invoice_data, pdf_path)

        print("🎉 Done!")
        context.close()


if __name__ == "__main__":
    # Test with sample data from your extractor
    test_data = {
        "po_number": "105349",
        "invoice_num": "1192",
        "date": "02/24/2026",
        "total": "1,383.00",
    }
    run_bot(test_data, "sample_invoices/Invoice_1192.pdf")
