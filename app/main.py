import os
from camoufox.sync_api import Camoufox


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SESSION_PATH = os.path.join(BASE_DIR, "sessions", "session.json")

def main():
    # create sessions dir if not exists
    os.makedirs(os.path.dirname(SESSION_PATH), exist_ok=True)

    with Camoufox(headless=False) as browser:
        if os.path.exists(SESSION_PATH):
            page = browser.new_page(storage_state=SESSION_PATH)
        else:
            page = browser.new_page()

        # page.goto(GOOGLE_MAPS_URL, wait_until="domcontentloaded")

        # save session
        page.context.storage_state(path=SESSION_PATH)      
        input("\nPress Enter to close the browser...")


if __name__ == "__main__":
    main()
