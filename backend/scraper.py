from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import os

load_dotenv()

DASHBOARD_URL = "https://prod.vendorcafe.com/content2/todo"
AUTH_SESSION_FILE = "auth_session.json"


def scrape_pending_pos():
    """
    Scrapes the VendorCafe Purchase Orders table and returns
    only POs where Pending PO Amount > 0.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # Load saved session
        if os.path.exists(AUTH_SESSION_FILE):
            context = browser.new_context(storage_state=AUTH_SESSION_FILE)
        else:
            browser.close()
            raise Exception("No auth session found. Run bot.py first to log in.")

        page = context.new_page()
        page.goto(DASHBOARD_URL)
        page.wait_for_timeout(10000)

        #check if logged in
        try:
            page.wait_for_selector(
                '[data-selenium-id="header-menu-item-mega-/vcprofile"]', timeout=10000
            )
        except Exception:
            browser.close()
            raise Exception("Session expired. Run bot.py first to re-login.")

        #go to Purchase Orders page
        page.wait_for_selector(
            '[data-selenium-id="header-menu-item-mega-/vcprofile"]', timeout=15000
        )
        page.click('[data-selenium-id="header-menu-item-mega-/vcprofile"]')
        page.wait_for_selector(
            '[href="/content2/vcprofile/search/po"]', timeout=15000
        )
        page.click('[href="/content2/vcprofile/search/po"]')

        # Wait for the PO table to load
        page.wait_for_selector("po-table .scrollable-yardi-table table tbody tr", timeout=15000)
        page.wait_for_timeout(2000)

        #get all rows from the PO table
        rows = page.query_selector_all("po-table .scrollable-yardi-table table tbody tr")

        pending_pos = []

        for i, row in enumerate(rows):
            try:
                # PO No.
                po_no_el = row.query_selector(f'[data-selenium-id="table-cell-data-selenium-id-1-{i}"] button')
                po_no = po_no_el.inner_text().strip() if po_no_el else ""

                # PO Description
                desc_el = row.query_selector(f'[data-selenium-id="table-cell-data-selenium-id-2-{i}"]')
                description = desc_el.inner_text().strip() if desc_el else ""

                # PO Amount
                po_amt_el = row.query_selector(f'[data-selenium-id="table-cell-data-selenium-id-5-{i}"]')
                po_amount = po_amt_el.inner_text().strip() if po_amt_el else "0"

                # Pending PO Amount - Important part
                pending_el = row.query_selector(f'[data-selenium-id="table-cell-data-selenium-id-7-{i}"]')
                pending_amount = pending_el.inner_text().strip() if pending_el else "0"

                # Property Name
                prop_el = row.query_selector(f'[data-selenium-id="table-cell-data-selenium-id-9-{i}"]')
                property_name = prop_el.inner_text().strip() if prop_el else ""

                # Unit
                unit_el = row.query_selector(f'[data-selenium-id="table-cell-data-selenium-id-11-{i}"]')
                unit = unit_el.inner_text().strip() if unit_el else ""

                # Order Date
                date_el = row.query_selector(f'[data-selenium-id="table-cell-data-selenium-id-12-{i}"]')
                order_date = date_el.inner_text().strip() if date_el else ""

                # Filter: only include POs with pending amount > 0
                pending_num = float(pending_amount.replace(",", "")) if pending_amount else 0
                if pending_num > 0:
                    pending_pos.append({
                        "po_number": po_no,
                        "description": description,
                        "po_amount": po_amount,
                        "pending_amount": pending_amount,
                        "property_name": property_name,
                        "unit": unit,
                        "order_date": order_date,
                    })

            except Exception as e:
                print(f"Error scraping row {i}: {e}")
                continue

        browser.close()
        return pending_pos


# Quick test
if __name__ == "__main__":
    results = scrape_pending_pos()
    print(f"\nFound {len(results)} POs with pending amounts:\n")
    for po in results:
        print(f"  PO #{po['po_number']} | {po['property_name']} Unit {po['unit']} | "
              f"Amount: ${po['po_amount']} | Pending: ${po['pending_amount']} | {po['order_date']}")
