from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import os

load_dotenv()

DASHBOARD_URL = "https://prod.vendorcafe.com/content2/todo"
AUTH_SESSION_FILE = "auth_session.json"


def login_manually(page, context):
    #Opens VendorCafe and pauses so I can log 
    page.goto("https://www.vendorcafe.com/vendorcafe/")
    print("\n" + "=" * 50)
    print("LOG IN MANUALLY in the Chromium window!")
    print("Solve the reCAPTCHA, enter your credentials,")
    print("and get to the dashboard.")
    print("=" * 50)
    input("\nPress ENTER here after you're on the dashboard... ")
    
    # Save cookies so we skip login next time
    context.storage_state(path=AUTH_SESSION_FILE)
    print("Session saved!")


def navigate_to_purchase_orders(page):
    # Wait for the Client Profiles tab to actually exist on the page
    page.wait_for_selector('[data-selenium-id="header-menu-item-mega-/vcprofile"]')

    # Click "Client Profiles" tab
    page.click('[data-selenium-id="header-menu-item-mega-/vcprofile"]')
    page.wait_for_timeout(2000)

    # Click "Purchase Order" tab
    page.click('[href="/content2/vcprofile/search/po"]')
    page.wait_for_timeout(2000)


def find_and_click_po(page, po_number: str):
    page.get_by_role("button", name=po_number).click()
    page.wait_for_timeout(2000)



def handle_create_invoice_popups(page):
    # Step 1: Click "Create Invoice" button
    page.get_by_role("button", name="Create Invoice").click()
    page.wait_for_timeout(2000)

    # Step 2: Click "Upload a PDF Invoice" tab
    page.click("#ngb-nav-12")	
    page.wait_for_timeout(2000)

    # Step 3: Click "OK" on the "Leave Page?" popup
    page.click("#confirm-ok-btn")	
    page.wait_for_timeout(2000)
    
    # Step 4: Click "Close" on the Purchase Order Details popup
    page.get_by_role("dialog").get_by_text("Close").click()
    page.wait_for_timeout(2000)


def fill_and_submit_invoice(page, invoice_data: dict, pdf_path: str):
    # Step 1: Upload the PDF file
    page.set_input_files("#pdfFileInput", os.path.abspath(pdf_path))
    page.wait_for_timeout(2000)
    
    # Step 2: Fill in Invoice No.
    page.fill("#invoiceNoInput", invoice_data["invoice_num"])
    
    # Step 3: Fill in Invoice Date
    page.fill("#invoiceDateInput", invoice_data["date"])
    
    # Step 4: Click Submit
    #page.get_by_role("button", name="Submit").click()
    #page.wait_for_timeout(3000)



def run_bot(invoice_data: dict, pdf_path: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        # Load saved session if it exists
        if os.path.exists(AUTH_SESSION_FILE):
            context = browser.new_context(storage_state=AUTH_SESSION_FILE)
        else:
            context = browser.new_context()

        page = context.new_page()
        page.goto(DASHBOARD_URL)
        page.wait_for_timeout(5000)  # Give VendorCafe time to finish redirecting

        print(f"Current URL: {page.url}")

        # If I'm not on the dashboard, I need to log in manually
        if "login" in page.url or "vendorcafe.com/vendorcafe" in page.url:
            print("Not logged in!")
            login_manually(page, context)
            #open a new page after login
            page = context.new_page()
            page.goto(DASHBOARD_URL)
            page.wait_for_timeout(5000)
        else:
            print("Already logged in!")

        # Wait for the page to fully load before clicking anything
        page.wait_for_timeout(3000)

        navigate_to_purchase_orders(page)
        find_and_click_po(page, invoice_data["po_number"])
        handle_create_invoice_popups(page)
        fill_and_submit_invoice(page, invoice_data, pdf_path)

        page.wait_for_timeout(5000)  # Pause so you can see the result
        print("Done!")
        browser.close()


if __name__ == "__main__":
    # Test with sample data from your extractor
    test_data = {
        "po_number": "105126",
        "invoice_num": "1208",
        "date": "03/15/2026",
        "total": "1,760.50",
    }
    run_bot(test_data, "sample_invoices/Invoice 1208_example.pdf")
