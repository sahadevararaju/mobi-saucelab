
import time
from pathlib import Path

from appium.webdriver.common.appiumby import AppiumBy
from utils.driver_factory import create_android_driver
from utils.sauce_config import ATOM_APP_ID

driver = None

try:
    driver = create_android_driver(
        test_name="ATOM Store - Select English",
        app=ATOM_APP_ID,
    )

    time.sleep(5)

    # Tap the language selector near the bottom of the welcome screen.
    driver.tap([(540, 2108)])
    time.sleep(3)

    print("Screen after tapping language selector:")
    print(driver.page_source)

    output = Path("reports")
    output.mkdir(exist_ok=True)

    path = output / "atom_language_screen.xml"
    path.write_text(driver.page_source, encoding="utf-8")
    print(f"\nSaved: {path.resolve()}")

    input(
        "\nCheck the Sauce Labs live device. If a language menu appears, "
        "select English manually. Then press ENTER to capture the screen."
    )

    xml = driver.page_source
    path = output / "atom_after_language_selection.xml"
    path.write_text(xml, encoding="utf-8")

    print(f"\nUpdated hierarchy saved: {path.resolve()}")
    print(xml)

except Exception as exc:
    print(f"Capture failed: {exc}")
    raise

finally:
    if driver:
        driver.quit()
