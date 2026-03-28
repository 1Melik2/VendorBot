from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import os

load_dotenv()

DASHBOARD_URL = "https://prod.vendorcafe.com/content2/todo"
AUTH_SESSION_FILE = "auth_session.json"


def login_manually(page, context):
    #Opens VendorCafe and pauses so I can log in
    page.goto("https://www.vendorcafe.com/vendorcafe/")
    page.wait_for_timeout(3000)

    # Auto-fill email so I only have to solve reCAPTCHA
    email = os.getenv("VENDORCAFE_USERNAME")
    password = os.getenv("VENDORCAFE_PASSWORD")
    if email:
        page.fill("#userId", email)

    print("\n" + "=" * 50)
    print("Email is pre-filled. Solve the reCAPTCHA")
    print("and click Login. Password will auto-fill next.")
    print("=" * 50)

    # Wait for the password page to load (user solves reCAPTCHA first)
    page.wait_for_selector("#txtPassword", timeout=120000)  # 2 min to solve captcha
    if password:
        page.fill("#txtPassword", password)
        print("Password auto-filled! Click Login.")

    # Wait for 2FA page and auto-check "Remember this device for 30 days"
    try:
        page.wait_for_selector("#rememberMeCheckbox", timeout=60000)  # 1 min to click login
        page.check("#rememberMeCheckbox")
        print("'Remember device for 30 days' checked! Enter your 2FA code.")
    except Exception:
        print("No 2FA page — skipping")

    input("\nPress ENTER here after you're on the dashboard... ")
    
    # Save cookies so we skip login next time
    context.storage_state(path=AUTH_SESSION_FILE)
    print("Session saved!")


def navigate_to_purchase_orders(page):
    # Wait for the Client Profiles tab to actually exist, then click
    page.wait_for_selector('[data-selenium-id="header-menu-item-mega-/vcprofile"]', timeout=15000)
    page.click('[data-selenium-id="header-menu-item-mega-/vcprofile"]')

    # Wait for Purchase Order tab to appear, then click
    page.wait_for_selector('[href="/content2/vcprofile/search/po"]', timeout=15000)
    page.click('[href="/content2/vcprofile/search/po"]')


def find_and_click_po(page, po_number: str):
    # Wait for the PO button to appear in the table, then click
    page.wait_for_selector(f'button:has-text("{po_number}")', timeout=15000)
    page.get_by_role("button", name=po_number).click()

    # Wait for the PO details table to load
    page.wait_for_selector('.scrollable-yardi-table table tbody tr', timeout=15000)

    # Make sure the first invoice line item is selected (checked)
    page.wait_for_selector('.scrollable-yardi-table table tbody tr input[type="checkbox"]', timeout=15000)
    page.check('.scrollable-yardi-table table tbody tr input[type="checkbox"]')
    page.wait_for_timeout(1000)  # Give it a moment to register the selection



def handle_create_invoice_popups(page):
    # Step 1: Click "Create Invoice" button
    page.wait_for_selector('button:has-text("Create Invoice")', timeout=15000)
    page.get_by_role("button", name="Create Invoice").click()
    page.wait_for_timeout(1000)

    # Step 2: Click "Upload a PDF Invoice" tab
    page.wait_for_selector("#ngb-nav-12", timeout=15000)
    page.click("#ngb-nav-12")
    page.wait_for_timeout(1000)

    # Step 3: Click "OK" on the "Leave Page?" popup (may not always appear)
    try:
        page.wait_for_selector("#confirm-ok-btn", timeout=5000)
        page.click("#confirm-ok-btn")
        page.wait_for_timeout(1000)
    except Exception:
        print("No 'Leave Page?' popup — skipping")
    
    # Step 4: Click "Close" on the Purchase Order Details popup (may not always appear)
    try:
        page.wait_for_selector('button[yardi-button].btn-light', timeout=5000)
        page.click('button[yardi-button].btn-light')
        page.wait_for_timeout(1000)
    except Exception:
        print("No 'Close' popup — skipping")


def fill_and_submit_invoice(page, invoice_data: dict, pdf_path: str):
    # Step 1: Upload the PDF file
    page.wait_for_selector("#pdfFileInput", timeout=15000)
    page.set_input_files("#pdfFileInput", os.path.abspath(pdf_path))
    
    # Step 2: Fill in Invoice No.
    page.wait_for_selector("#invoiceNoInput", timeout=15000)
    page.fill("#invoiceNoInput", invoice_data["invoice_num"])
    
    # Step 3: Fill in Invoice Date
    page.wait_for_selector("#invoiceDateInput", timeout=15000)
    page.fill("#invoiceDateInput", invoice_data["date"])
    
    # Step 4: Click Submit
    #page.wait_for_selector('button:has-text("Submit")', timeout=15000)
    #page.get_by_role("button", name="Submit").click()
    #page.wait_for_timeout(3000)



def run_bot(invoice_data: dict, pdf_path: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        #UNCOMMENT WHEN READY TO DEPLOY
        '''# Run headless in Docker (no screen), headed locally (so you can see it)
        is_docker = os.getenv("DOCKER_ENV", "false") == "true"
        browser = p.chromium.launch(headless=is_docker)'''


        # Load saved session if it exists
        if os.path.exists(AUTH_SESSION_FILE):
            context = browser.new_context(storage_state=AUTH_SESSION_FILE)
        else:
            context = browser.new_context()

        page = context.new_page()
        page.goto(DASHBOARD_URL)
        page.wait_for_timeout(10000)  # Give VendorCafe time to finish redirecting

        print(f"Current URL: {page.url}")

        # Check if we're ACTUALLY logged in by looking for a dashboard element
        # URL checking is unreliable because VendorCafe bounces between /todo and /login
        try:
            page.wait_for_selector('[data-selenium-id="header-menu-item-mega-/vcprofile"]', timeout=10000)
            print("Already logged in!")
        except Exception:
            print("Session expired — starting fresh login...")
            # Close old context with stale cookies (but keep auth_session.json on disk)
            context.close()
            # Fresh context = no stale cookies = no redirect loop
            context = browser.new_context()
            page = context.new_page()
            login_manually(page, context)  # This saves new cookies to auth_session.json
            # Open a new page after login
            page = context.new_page()
            page.goto(DASHBOARD_URL)
            page.wait_for_timeout(10000)

        # Wait for the page to fully load before clicking anything
        page.wait_for_timeout(3000)

        navigate_to_purchase_orders(page)
        find_and_click_po(page, invoice_data["po_number"])
        handle_create_invoice_popups(page)
        fill_and_submit_invoice(page, invoice_data, pdf_path)
        # Pause so user can review and manually click Submit
        # If user closes the browser/tab, that's fine — catch the error
        try:
            page.wait_for_timeout(120000)  # 2 min to review and submit
        except Exception:
            pass  # User closed browser — they submitted manually

        print("Done!")
        try:
            browser.close()
        except Exception:
            pass  # Browser already closed


if __name__ == "__main__":
    # Test with sample data from  extractor
    test_data = {
        "po_number": "105126",
        "invoice_num": "1208",
        "date": "03/15/2026",
        "total": "1,760.50",
    }
    run_bot(test_data, "sample_invoices/Invoice 1208_example.pdf")
