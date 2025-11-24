from playwright.sync_api import sync_playwright, expect
import time

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Navigate to the Minimal UI
        print("Navigating to http://127.0.0.1:8081/")
        page.goto("http://127.0.0.1:8081/")

        # Verify Title
        print("Verifying title...")
        expect(page).to_have_title("PDF Atomic Pro")

        # Verify Health Check (Wait for fetch to complete)
        print("Verifying health status...")
        health_status = page.locator("#health-status")
        expect(health_status).to_have_text("Sistema Online (Backend OK)")

        # Verify Button exists
        process_btn = page.locator("#btn-process")
        expect(process_btn).to_be_visible()
        expect(process_btn).to_have_text("Procesar CSV")

        # Click the button
        print("Clicking process button...")
        process_btn.click()

        # Verify status update
        print("Verifying batch process status...")
        batch_status = page.locator("#batch-status")
        # Expect text to contain "Comando enviado"
        expect(batch_status).to_contain_text("Comando enviado")

        # Take screenshot
        screenshot_path = "/home/jules/verification/verification.png"
        page.screenshot(path=screenshot_path)
        print(f"Screenshot saved to {screenshot_path}")

        browser.close()

if __name__ == "__main__":
    run()
