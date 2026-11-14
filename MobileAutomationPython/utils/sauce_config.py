import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(ENV_FILE)
SAUCE_USERNAME = os.getenv("SAUCE_USERNAME")
SAUCE_ACCESS_KEY = os.getenv("SAUCE_ACCESS_KEY")
SAUCE_URL = os.getenv(
    "SAUCE_URL",
    "https://ondemand.eu-central-1.saucelabs.com/wd/hub",
)
ATOM_APP_ID = os.getenv(
    "SAUCE_APP",
    "storage:2cdac6d4-7eb4-4ef6-903a-6f98eb11b77d",
)
MOBILE_NUMBER = os.getenv("MOBILE_NUMBER")
ATOM_APP_PACKAGE = "mm.com.atom.store"
ATOM_APP_ACTIVITY = "mm.cws.telenor.app.LauncherDefault"


def get_sauce_capabilities(test_name):
    if not SAUCE_USERNAME or not SAUCE_ACCESS_KEY:
        raise RuntimeError(
            "Missing Sauce Labs credentials. "
            "Set SAUCE_USERNAME and SAUCE_ACCESS_KEY in .env."
        )

    return {
        "username": SAUCE_USERNAME,
        "accessKey": SAUCE_ACCESS_KEY,
        "name": test_name,
        "build": "ATOM Store Android Automation",
        "appiumVersion": "latest",
    }