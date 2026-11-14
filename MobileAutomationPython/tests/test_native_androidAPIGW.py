import re
import time
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree

import pytest
from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from utils.sauce_config import ATOM_APP_PACKAGE, MOBILE_NUMBER


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCREENSHOT_DIR = PROJECT_ROOT / "reports" / "screenshots"
UI_DUMP_DIR = PROJECT_ROOT / "reports" / "ui_dumps"
MAX_HOME_TOOLTIPS = 10
MAX_PROMOTIONAL_SCREENS = 5
EXECUTION_ID = None


@pytest.fixture(scope="session", autouse=True)
def _initialize_evidence_execution_id():
    _get_execution_id(reset=True)


def _get_execution_id(reset=False):
    global EXECUTION_ID
    if reset or EXECUTION_ID is None:
        EXECUTION_ID = datetime.now().strftime("%Y%m%d_%H%M%S")
    return EXECUTION_ID

TEST_CASES = {
    "TC001": (
        "Verify the latest APK launches successfully",
        "Latest ATOM Store APK",
        "Launch the application.",
        "The ATOM Store application launches successfully.",
    ),
    "TC002": (
        "Verify the Welcome screen appears correctly",
        "Welcome screen",
        "Inspect the logo, login option, and language selector.",
        "The Welcome screen and its expected controls are displayed.",
    ),
    "TC003": (
        "Verify the user can select English",
        "English",
        "Open the language selector and choose English.",
        "English is selected and the app returns to the Welcome screen.",
    ),
    "TC004": (
        "Verify the user can open the login screen",
        "English",
        "Tap the login option on the Welcome screen.",
        "The login screen and mobile-number field are displayed.",
    ),
    "TC005": (
        "Verify the user can enter a mobile number and submit OTP",
        "Configured mobile number and SMS OTP",
        "Enter the configured mobile number and submit the received OTP.",
        "The mobile number and valid OTP are accepted.",
    ),
    "TC006": (
        "Verify the ATOM Store home screen appears after dismissing promotions",
        "Authenticated user; promotional screen if displayed",
        "Dismiss the promotional screen if displayed and wait for the home screen.",
        "The promotional screen is closed and the ATOM Store home screen appears.",
     ),
    "TC007": (
        "Complete scratch-card and KBZPay Top Up flows",
        "Configured ATOM phone number; scratch card; KBZPay amount 1,000",
        "Submit the scratch card, then complete the Other Digital Payments KBZPay confirmation flow.",
        "The expected scratch-card response is handled and the KBZPay transaction reaches a verified success state.",
    ),
    "TC008": (
        "Click on Packs Icon and verify Packages window is displayed",
        "Authenticated user on the ATOM Store Home screen",
        "Verify Home, capture its evidence, click the Packs navigation icon, and verify the Packages title.",
        "The Packages screen is displayed with visible text exactly 'Packages'.",
    ),
    "TC009": (
        "Select KyiKwar from the Packages screen",
        "Packages screen; KyiKwar option",
        "Click KyiKwar and inspect the resulting screen state.",
        "The KyiKwar option responds to the click.",
    ),
    "TC010": (
        "Select All-in-One from the Packages screen",
        "Packages screen; All-in-One option",
        "Click All-in-One and inspect the resulting screen state.",
        "The All-in-One option responds to the click.",
    ),
    "TC011": (
        "Select TikTok from the Packages screen",
        "Packages screen; TikTok option",
        "Click TikTok and inspect the resulting screen state.",
        "The TikTok option responds to the click.",
    ),
    "TC012": (
        "Select Youtube from the Packages screen",
        "Packages screen; Youtube option",
        "Click Youtube and inspect the resulting screen state.",
        "The Youtube option responds to the click.",
    ),
    "TC013": (
        "Select Telegram from the Packages screen",
        "Packages screen; Telegram option",
        "Click Telegram and inspect the resulting screen state.",
        "The Telegram option responds to the click.",
    ),
    "TC014": (
        "Select MegaPack from the Packages screen",
        "Packages screen; MegaPack option",
        "Click MegaPack and inspect the resulting screen state.",
        "The MegaPack option responds to the click.",
    ),
    "TC015": (
        "Select Super Htaw from the Packages screen",
        "Packages screen; Super Htaw option",
        "Click Super Htaw and inspect the resulting screen state.",
        "The Super Htaw option responds to the click.",
    ),
    "TC016": (
        "Select Flexiplan from the Packages screen",
        "Packages screen; Flexiplan option",
        "Return to Packages using Back or navigate from Home through Packs, then click Flexiplan.",
        "The Flexiplan option responds to the click.",
    ),
    "TC017": (
        "Open Transfer from the Home screen",
        "Authenticated Home screen; Transfer option",
        "Return to Home using the Home control or Back, then click Transfer.",
        "The Transfer destination opens after any Android permission prompt is handled.",
    ),
    "TC018": (
        "Select Point on the Transfer screen",
        "Transfer screen; Point option",
        "On the Transfer screen opened by TC017, click Point.",
        "The Point option responds to the click.",
    ),
 }


def _run_testcase(node, testcase_id, test_function, *args):
    result = node._excel_test_case_results[testcase_id]
    try:
        test_function(*args)
    except Exception as error:
        result["Result"] = "Failed"
        result["Error Message"] = str(error)
        driver = next(
            (
                argument
                for argument in args
                if hasattr(argument, "page_source")
                and hasattr(argument, "get_screenshot_as_png")
            ),
            None,
        )
        if driver is not None:
            try:
                _capture_evidence(driver, testcase_id, "failure")
            except Exception as evidence_error:
                print(f"Failure evidence capture failed: {evidence_error}")
        raise
    else:
        result["Result"] = "Passed"
        result["Error Message"] = ""
        driver = next(
            (
                argument
                for argument in args
                if hasattr(argument, "page_source")
                and hasattr(argument, "get_screenshot_as_png")
            ),
            None,
        )
        if driver is not None:
            try:
                _capture_evidence(driver, testcase_id, "completed")
            except Exception as evidence_error:
                print(f"Completion evidence capture failed: {evidence_error}")


def _save_screenshot(driver, filename):
    stem = Path(filename).stem
    match = re.match(
        r"atom_store_(tc\d+)(?:_(.+))?",
        stem,
        re.IGNORECASE,
    )
    if match:
        testcase_id, stage = match.groups()
        stage = stage or "screen"
    else:
        testcase_id, stage = "TC000", stem
    return _capture_evidence(driver, testcase_id, stage)


def _capture_evidence(driver, testcase_id, stage):
    execution_id = _get_execution_id()
    safe_testcase = re.sub(r"[^a-z0-9_]+", "", testcase_id.lower())
    safe_stage = re.sub(r"[^a-z0-9]+", "_", stage.lower()).strip("_")
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    UI_DUMP_DIR.mkdir(parents=True, exist_ok=True)

    screenshot_data = driver.get_screenshot_as_png()
    hierarchy_data = driver.page_source
    sequence = 0
    while True:
        suffix = f"_{sequence}" if sequence else ""
        stem = (
            f"atom_store_{safe_testcase}_{safe_stage}_"
            f"{execution_id}{suffix}"
        )
        screenshot_path = SCREENSHOT_DIR / f"{stem}.png"
        hierarchy_path = UI_DUMP_DIR / f"{stem}.xml"

        try:
            screenshot_file = screenshot_path.open("xb")
        except FileExistsError:
            sequence += 1
            continue

        try:
            hierarchy_file = hierarchy_path.open("x", encoding="utf-8")
        except FileExistsError:
            screenshot_file.close()
            screenshot_path.unlink()
            sequence += 1
            continue

        with screenshot_file, hierarchy_file:
            screenshot_file.write(screenshot_data)
            hierarchy_file.write(hierarchy_data)
        print(
            f"Evidence saved: {screenshot_path} and {hierarchy_path}"
        )
        return screenshot_path, hierarchy_path


@pytest.mark.sauce
def test_atom_store_tc001_to_tc006(atom_store_driver, capsys, request):
    _initialize_test_case_report(request.node)
    testcases = [
        ("TC001", _tc001_launch_latest_apk, atom_store_driver),
        ("TC002", _tc002_verify_welcome_screen, atom_store_driver),
        ("TC003", _tc003_select_english, atom_store_driver),
        ("TC004", _tc004_open_login_screen, atom_store_driver),
        ("TC005", _tc005_enter_mobile_number, atom_store_driver, capsys),
        ("TC006", _tc006_verify_store_home_screen, atom_store_driver),
        ("TC007", _tc007_click_top_up_icon, atom_store_driver),
        ("TC008", _tc008_click_packs_icon, atom_store_driver),
        ("TC009", _tc009_click_kyikwar, atom_store_driver),
        ("TC010", _tc010_click_all_in_one, atom_store_driver),
        ("TC011", _tc011_click_tiktok, atom_store_driver),
        ("TC012", _tc012_click_youtube, atom_store_driver),
        ("TC013", _tc013_click_telegram, atom_store_driver),
        ("TC014", _tc014_click_megapack, atom_store_driver),
        ("TC015", _tc015_click_super_htaw, atom_store_driver),
        ("TC016", _tc016_click_flexiplan, atom_store_driver),
        ("TC017", _tc017_click_transfer, atom_store_driver),
        ("TC018", _tc018_click_point, atom_store_driver),
    ]
    tc007_error = None
    for testcase in testcases:
        try:
            _run_testcase(
                request.node,
                testcase[0],
                testcase[1],
                *testcase[2:],
            )
        except Exception as error:
            if testcase[0] != "TC007":
                raise
            tc007_error = error

    if tc007_error is not None:
        raise AssertionError(
            f"TC007 failed; later cases were still executed: {tc007_error}"
        ) from tc007_error


def _initialize_test_case_report(node):
    node._excel_test_case_results = {}
    for testcase_id, case_details in TEST_CASES.items():
        scenario, test_data, steps, expected_result = case_details
        node._excel_test_case_results[testcase_id] = {
            "Test Case ID": testcase_id,
            "Module/Feature": "ATOM Store",
            "Test Data": test_data,
            "Pre-condition": "ATOM Store app is installed and available.",
            "Test Scenario": f"{testcase_id}: {scenario}",
            "Test Steps": steps,
            "Expected Result": expected_result,
            "Environment": "Sauce Labs",
            "Result": "Not Run",
            "Error Message": "Not executed because an earlier test case failed.",
        }


def _tc001_launch_latest_apk(driver):
    assert driver.current_package, "App package was not detected."
    assert driver.current_activity, "App activity was not detected."

    WebDriverWait(driver, 30).until(_is_welcome_screen_displayed)
    _save_screenshot(driver, "atom_store_tc001.png")


def _is_welcome_screen_displayed(driver):
    if driver.current_package != ATOM_APP_PACKAGE:
        return False

    login_options = driver.find_elements(
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().text("လော့ဂ်အင်၀င်ရန်")',
    )
    language_selectors = driver.find_elements(
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().text("မြန်မာ | English | 中文")',
    )
    return any(option.is_displayed() for option in login_options) and any(
        selector.is_displayed() for selector in language_selectors
    )


def _tc002_verify_welcome_screen(driver):
    wait = WebDriverWait(driver, 20)
    logo = wait.until(
        EC.visibility_of_element_located(
            (AppiumBy.ACCESSIBILITY_ID, "Logo")
        )
    )

    login_text = wait.until(
        EC.visibility_of_element_located(
            (
                AppiumBy.ANDROID_UIAUTOMATOR,
                'new UiSelector().text("လော့ဂ်အင်၀င်ရန်")',
            )
        )
    )

    language_text = wait.until(
        EC.visibility_of_element_located(
            (
                AppiumBy.ANDROID_UIAUTOMATOR,
                'new UiSelector().text("မြန်မာ | English | 中文")',
            )
        )
    )
    assert logo.is_displayed() and login_text.is_displayed()
    assert language_text.is_displayed()

    _save_screenshot(driver, "atom_store_tc002.png")


def _tc003_select_english(driver):
    _select_language(driver, "rdEnglish", "tc003_english")


def _select_language(driver, option_id, screenshot_name):
    wait = WebDriverWait(driver, 15)

    language_selector = wait.until(
        EC.element_to_be_clickable(
            (
                AppiumBy.ANDROID_UIAUTOMATOR,
                'new UiSelector().textContains("English")',
            )
        )
    )
    language_selector.click()

    english_option = wait.until(
        EC.element_to_be_clickable(
            (AppiumBy.ID, f"mm.com.atom.store:id/{option_id}")
        )
    )
    english_option.click()

    wait.until(
        lambda current_driver: current_driver.find_element(
            AppiumBy.ID,
            f"mm.com.atom.store:id/{option_id}",
        ).get_attribute("checked")
        == "true"
    )

    ok_button = wait.until(
        EC.element_to_be_clickable(
            (AppiumBy.ID, "mm.com.atom.store:id/btnOkLan")
        )
    )
    ok_button.click()

    time.sleep(4)
    _save_screenshot(driver, f"atom_store_{screenshot_name}.png")


def _tc004_open_login_screen(driver):
    _open_login_screen(driver, "tc004_login_screen")


def _open_login_screen(driver, screenshot_name):
    wait = WebDriverWait(driver, 20)
    login_button = wait.until(
        lambda current_driver: next(
            (
                button
                for button in current_driver.find_elements(
                    AppiumBy.CLASS_NAME,
                    "android.widget.Button",
                )
                if button.is_displayed() and button.is_enabled()
            ),
            False,
        )
    )
    login_button.click()

    wait.until(
        EC.element_to_be_clickable(
            (AppiumBy.CLASS_NAME, "android.widget.EditText")
        )
    )
    _save_screenshot(driver, f"atom_store_{screenshot_name}.png")


def _tc005_enter_mobile_number(
    driver,
    capsys,
    testcase="TC005",
    screenshot_prefix="atom_store_tc005",
):
    _enter_mobile_number(driver, capsys, testcase, screenshot_prefix)


def _enter_mobile_number(driver, capsys, testcase, screenshot_prefix):
    print(f"\n--- {testcase}: Mobile Number and SMS OTP Login ---")

    wait = WebDriverWait(driver, 20)

    phone_field = wait.until(
        EC.element_to_be_clickable(
            (AppiumBy.CLASS_NAME, "android.widget.EditText")
        )
    )
    phone_field.clear()
    phone_field.send_keys(MOBILE_NUMBER)
    print("PASS: Mobile number entered.")

    login_button = wait.until(
        lambda current_driver: max(
            (
                button
                for button in current_driver.find_elements(
                    AppiumBy.CLASS_NAME,
                    "android.widget.Button",
                )
                if button.is_displayed() and button.is_enabled()
            ),
            default=None,
            key=lambda button: button.location["y"] + button.size["height"],
        )
    )
    login_button.click()
    print("PASS: Submitted the mobile number.")

    with capsys.disabled():
        otp = input(
            "\n Please Enter the actual 6-digit OTP received by SMS: "
        ).strip()

    if not re.fullmatch(r"\d{6}", otp):
        raise AssertionError(
            f"{testcase} FAIL: OTP must contain exactly 6 digits."
        )

    otp_fields = WebDriverWait(driver, 20).until(
        lambda current_driver: [
            element
            for element in current_driver.find_elements(
                AppiumBy.CLASS_NAME,
                "android.widget.EditText",
            )
            if element.is_displayed() and element.is_enabled()
        ]
    )

    otp_labeled_fields = [
        field
        for field in otp_fields
        if any(
            marker in (field.get_attribute(attribute) or "").lower()
            for attribute in ("resource-id", "content-desc", "hint")
            for marker in ("otp", "verification", "security code")
        )
    ]
    if otp_labeled_fields:
        otp_fields = otp_labeled_fields

    if len(otp_fields) == 1:
        # Some screens draw six boxes around one underlying text field.
        otp_fields[0].send_keys(otp)
    elif len(otp_fields) == 6:
        for field, digit in zip(otp_fields, otp):
            field.send_keys(digit)
    else:
        raise AssertionError(
            f"{testcase} FAIL: Could not identify the OTP input. Expected one "
            "OTP field or six separate digit fields, but found "
            f"{len(otp_fields)} candidate fields. "
            f"Current screen XML: {driver.page_source}"
        )

    print("PASS: Entered all six OTP digits.")

    submit_labels = [
        "Verify",
        "Verify OTP",
        "Continue",
        "Submit",
        "Confirm",
        "Log in",
    ]

    submit_button = None

    for label in submit_labels:
        elements = driver.find_elements(
            AppiumBy.ANDROID_UIAUTOMATOR,
            f'new UiSelector().textMatches("(?i)^{re.escape(label)}$")'
        )

        for element in elements:
            if element.is_displayed() and element.is_enabled():
                submit_button = element
                break

        if submit_button:
            break

    if submit_button:
        submit_button.click()
        print("PASS: Tapped the OTP verification button.")
    else:
        print(
            "No separate verification button found. "
            "The app may verify the OTP automatically."
        )

    WebDriverWait(driver, 30).until(_is_ready_for_post_login_checks)
    _save_screenshot(driver, f"{screenshot_prefix}_post_otp.png")

    # print("Current activity:", driver.current_activity)
    # print("Current screen XML:")
    # print(driver.page_source)
    print(
        f"{testcase} OTP submission completed. Post-OTP screenshot "
        f"saved to reports/screenshots/{screenshot_prefix}_post_otp.png."
    )


def _tc006_verify_store_home_screen(driver):
    _verify_store_home_screen(driver, "TC006", "atom_store_tc006")


def _tc008_click_packs_icon(driver):
    if not _is_home_navigation_selected(driver):
        _capture_evidence(driver, "TC008", "008_before_home_navigation")
        _tc008_return_home(driver)

    _capture_evidence(driver, "TC008", "008_before_click_packs")
    packs_icon = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable(
            (AppiumBy.ACCESSIBILITY_ID, "Packs")
        )
    )
    packs_icon.click()
    WebDriverWait(driver, 30).until(
        lambda current_driver: any(
            element.is_displayed()
            and element.text == "Packages"
            for element in current_driver.find_elements(
                AppiumBy.ANDROID_UIAUTOMATOR,
                'new UiSelector().text("Packages")',
            )
        )
    )
    _capture_evidence(driver, "TC008", "008_packages_screen")


def _tc008_return_home(driver):
    for _ in range(5):
        if _is_home_navigation_selected(driver):
            return

        before_source = driver.page_source
        home_control = _tc007_find_accessible_clickable_parent(driver, "Home")
        if home_control is None:
            home_control = next(
                (
                    control
                    for control in driver.find_elements(
                        AppiumBy.ACCESSIBILITY_ID,
                        "Home",
                    )
                    if control.is_displayed()
                    and control.is_enabled()
                    and control.get_attribute("clickable") == "true"
                ),
                None,
            )

        if home_control is not None:
            home_control.click()
        else:
            back_bounds = _tc007_bounds_for_accessibility_label(
                before_source,
                "Back",
            )
            if back_bounds is not None:
                _tc007_click_bounds(driver, back_bounds)
            else:
                driver.back()

        try:
            WebDriverWait(driver, 6).until(
                lambda current_driver: (
                    _is_home_navigation_selected(current_driver)
                    or current_driver.page_source != before_source
                )
            )
        except TimeoutException:
            continue

    if not _is_home_navigation_selected(driver):
        raise AssertionError(
            "TC008 could not return Home after using the Home control or "
            "following up to five Back actions."
        )


def _is_home_navigation_selected(driver):
    home_controls = driver.find_elements(
        AppiumBy.ID,
        f"{ATOM_APP_PACKAGE}:id/dashboardFragment",
    )
    return any(
        control.is_displayed()
        and control.get_attribute("selected") == "true"
        for control in home_controls
    )


def _tc007_bounds_for_accessibility_label(source, label):
    root = ElementTree.fromstring(source)
    target = label.strip().casefold()
    for node in root.iter():
        if (node.get("content-desc") or "").strip().casefold() == target:
            return _tc007_parse_bounds(node.get("bounds", ""))
    return None


def _tc009_click_kyikwar(driver):
    _click_package_item(driver, "KyiKwar", "TC009")


def _tc010_click_all_in_one(driver):
    _click_package_item(driver, "All-in-One", "TC010")


def _tc011_click_tiktok(driver):
    _click_package_item(driver, "TikTok", "TC011")


def _tc012_click_youtube(driver):
    _click_package_item(driver, "Youtube", "TC012")


def _tc013_click_telegram(driver):
    _click_package_item(driver, "Telegram", "TC013")


def _tc014_click_megapack(driver):
    _click_package_item(driver, "MegaPack", "TC014")


def _tc015_click_super_htaw(driver):
    _click_package_item(driver, "Super Htaw", "TC015")


def _tc016_click_flexiplan(driver):
    _click_package_item(driver, "Flexiplan", "TC016")


def _tc017_click_transfer(driver):
    _tc008_return_home(driver)
    WebDriverWait(driver, 20).until(
        lambda current_driver: (
            _tc007_find_text_element(current_driver, "Transfer") or False
        )
    )
    before_source = driver.page_source
    _tc007_click_text(driver, "Transfer")

    try:
        WebDriverWait(driver, 15).until(
            lambda current_driver: (
                _is_android_runtime_permission_popup_visible(current_driver)
                or current_driver.page_source != before_source
            )
        )
        permission_was_visible = _is_android_runtime_permission_popup_visible(
            driver
        )
        permission_source = driver.page_source
        if permission_was_visible:
            _allow_android_runtime_permission_if_present(driver)
            WebDriverWait(driver, 30).until(
                lambda current_driver: (
                    not _is_android_runtime_permission_popup_visible(
                        current_driver
                    )
                    and current_driver.page_source != permission_source
                )
            )
    except TimeoutException as error:
        _capture_evidence(driver, "TC017", "transfer_open_failed")
        raise AssertionError(
            "TC017 clicked Transfer but the destination did not finish "
            "opening."
        ) from error

    _capture_evidence(driver, "TC017", "tc017_transfer_opened")


def _tc018_click_point(driver):
    _click_visible_item(driver, "Point", "TC018")


def _is_android_runtime_permission_popup_visible(driver):
    root = ElementTree.fromstring(driver.page_source)
    permission_packages = {
        "com.android.permissioncontroller",
        "com.google.android.permissioncontroller",
    }
    return any(
        node.get("package", "") in permission_packages
        and node.get("resource-id", "").endswith(":id/grant_dialog")
        and node.get("displayed", "true").lower() == "true"
        for node in root.iter()
    )


def _allow_android_runtime_permission_if_present(driver):
    if not _is_android_runtime_permission_popup_visible(driver):
        return False

    allow_button = next(
        (
            element
            for locator in (
                (
                    AppiumBy.ID,
                    "com.android.permissioncontroller:id/permission_allow_button",
                ),
                (
                    AppiumBy.ID,
                    "com.google.android.permissioncontroller:id/permission_allow_button",
                ),
                (
                    AppiumBy.ANDROID_UIAUTOMATOR,
                    'new UiSelector().textMatches("(?i)^allow$")',
                ),
            )
            for element in driver.find_elements(*locator)
            if element.is_displayed() and element.is_enabled()
        ),
        None,
    )
    if allow_button is None:
        raise AssertionError(
            "Android runtime permission dialog appeared without a usable "
            "Allow button."
        )
    allow_button.click()
    WebDriverWait(driver, 15).until(
        lambda current_driver: (
            not _is_android_runtime_permission_popup_visible(current_driver)
        )
    )
    return True


def _click_package_item(driver, label, testcase):
    packages_title = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("Packages")')
    if _tc007_find_text_element(driver, label) is None:
        driver.back()
        WebDriverWait(driver, 20).until(
            lambda current_driver: any(
                element.is_displayed()
                for element in current_driver.find_elements(*packages_title)
            )
        )

    WebDriverWait(driver, 20).until(
        lambda current_driver: (
            _tc007_find_text_element(current_driver, label) or False
        )
    )
    before_source = driver.page_source
    before_screenshot = driver.get_screenshot_as_png()
    clickable_bounds = _tc007_clickable_bounds_for_label(
        before_source,
        label,
    )
    if clickable_bounds is not None:
        _tc007_click_bounds(driver, clickable_bounds)
    else:
        _tc007_click_text(driver, label)
    try:
        WebDriverWait(driver, 15).until(
            lambda current_driver: (
                current_driver.page_source != before_source
                or current_driver.get_screenshot_as_png() != before_screenshot
            )
        )
    except TimeoutException as error:
        _capture_evidence(driver, testcase, "click_no_visible_response")
        raise AssertionError(
            f"Clicking {label} produced no visible screen change."
        ) from error
    _capture_evidence(driver, testcase, f"{testcase.lower()}_{label.lower().replace('-', '_')}")


def _tc007_click_top_up_icon(driver):
    if not _is_store_home_screen(driver):
        raise AssertionError(
            "TC007 requires the authenticated ATOM Store home screen."
        )

    driver.execute_script(
        "mobile: clickGesture",
        {"x": 168, "y": 644},
    )
    WebDriverWait(driver, 30).until(_tc007_is_top_up_screen)
    scratch_card_response = _tc007_scratch_card_flow(driver)
    try:
        _tc007_other_digital_payment_flow(driver)
    except Exception as error:
        if scratch_card_response:
            raise AssertionError(
                f"{error} Scratch-card application response: "
                f"{scratch_card_response}"
            ) from error
        raise
    if scratch_card_response:
        raise AssertionError(
            "Scratch-card voucher was rejected; expected a valid voucher. "
            f"Application message: {scratch_card_response}"
        )


def _tc007_scratch_card_flow(driver):
    scratch_card_number = "36885710672098262"
    wait = WebDriverWait(driver, 30)
    if not _tc007_is_top_up_screen(driver):
        raise AssertionError("TC007 could not verify the Top Up screen.")
    _capture_evidence(driver, "TC007", "00_top_up_opened")

    edit_fields = wait.until(
        lambda current_driver: (
            fields
            if len(fields := _tc007_edit_fields(current_driver)) >= 2
            else False
        )
    )
    phone_field, scratch_card_field = edit_fields[:2]
    if not MOBILE_NUMBER:
        raise AssertionError("MOBILE_NUMBER is not configured in .env.")
    phone_field.clear()
    phone_field.send_keys(MOBILE_NUMBER)
    if phone_field.get_attribute("text") != MOBILE_NUMBER:
        raise AssertionError("Configured ATOM phone number entry did not match.")

    scratch_card_field.clear()
    scratch_card_field.send_keys(scratch_card_number)
    entered_card = re.sub(r"\D", "", scratch_card_field.get_attribute("text") or "")
    if entered_card != scratch_card_number:
        raise AssertionError("Scratch card number entry did not match.")
    _capture_evidence(driver, "TC007", "01_scratch_card_entry")

    try:
        before_submit = _tc007_click_top_up_submit(driver)
    except TimeoutException as error:
        _capture_evidence(driver, "TC007", "02_scratch_submit_unavailable")
        try:
            _tc007_return_home_after_submit_failure(driver)
        except Exception as recovery_error:
            raise AssertionError(
                "The scratch-card submit control was unavailable, and the "
                "Back control could not restore Home. Voucher validation was "
                "not reached."
            ) from recovery_error
        raise AssertionError(
            "The scratch-card submit control was not present as an enabled, "
            "clickable control. Returned to Home for recovery; voucher "
            "validation was not reached, so TC007 failed."
        ) from error
    try:
        wait.until(
            lambda current_driver: (
                current_driver.page_source != before_submit
                or _tc007_has_text(current_driver, "Okay")
            )
        )
    except TimeoutException as error:
        _capture_evidence(driver, "TC007", "02_scratch_card_response_timeout")
        raise AssertionError(
            "No response appeared after submitting the scratch-card request."
        ) from error

    response_source = driver.page_source
    _capture_evidence(driver, "TC007", "02_scratch_card_response")
    okay_button = _tc007_find_text_element(driver, "Okay")
    if okay_button is None:
        _capture_evidence(driver, "TC007", "02_scratch_card_response_unrecognized")
        raise AssertionError(
            "Scratch-card response did not show the expected Okay voucher "
            "rejection, and no verified voucher-success landmark is known."
        )

    error_message = _tc007_dialog_message(response_source)
    if MOBILE_NUMBER:
        error_message = error_message.replace(MOBILE_NUMBER, "[redacted]")
    try:
        okay_button.click()
        wait.until(lambda current_driver: not _tc007_has_text(current_driver, "Okay"))
    except Exception as error:
        _capture_evidence(driver, "TC007", "02_scratch_card_dismissal_failed")
        raise AssertionError(
            "Invalid voucher dialog was displayed but Okay could not be "
            f"dismissed. Application message: {error_message}"
        ) from error

    _capture_evidence(driver, "TC007", "02_scratch_card_after_dismissal")
    if not _tc007_is_top_up_screen(driver):
        raise AssertionError(
            "Invalid voucher dialog was dismissed, but the Top Up screen is "
            "not available for the digital-payment flow. "
            f"Application message: {error_message}"
        )
    return error_message


def _tc007_other_digital_payment_flow(driver):
    if not _tc007_is_top_up_screen(driver):
        raise AssertionError(
            "Other Digital Payments cannot be selected because the Top Up "
            "screen is not displayed."
        )

    _tc007_click_text(driver, "Other Digital Payments")
    try:
        WebDriverWait(driver, 10).until(
            lambda current_driver: _tc007_label_is_selected(
                current_driver,
                "Other Digital Payments",
            )
        )
    except TimeoutException as error:
        _capture_evidence(driver, "TC007", "03_other_digital_payments_failed")
        raise AssertionError(
            "Other Digital Payments selection could not be verified."
        ) from error
    _capture_evidence(driver, "TC007", "03_other_digital_payments")

    kbz_bounds = WebDriverWait(driver, 15).until(_tc007_kbzpay_tile_bounds)
    _tc007_click_bounds(driver, kbz_bounds)
    try:
        WebDriverWait(driver, 10).until(
            lambda current_driver: _tc007_bounds_are_selected(
                current_driver,
                kbz_bounds,
            )
        )
    except TimeoutException as error:
        _capture_evidence(driver, "TC007", "04_kbzpay_selection_failed")
        raise AssertionError(
            "KBZPay selection could not be verified from the hierarchy."
        ) from error
    _capture_evidence(driver, "TC007", "04_kbzpay_selected")

    _tc007_click_text(driver, "1,000")
    try:
        WebDriverWait(driver, 10).until(
            lambda current_driver: _tc007_label_is_selected(current_driver, "1,000")
        )
    except TimeoutException as error:
        _capture_evidence(driver, "TC007", "05_amount_selection_failed")
        raise AssertionError(
            "The 1,000 amount selection could not be verified."
        ) from error
    _capture_evidence(driver, "TC007", "05_amount_selected")

    _tc007_click_text(driver, "Top Up")
    try:
        WebDriverWait(driver, 30).until(
            lambda current_driver: _tc007_has_text(current_driver, "Confirm")
        )
    except TimeoutException as error:
        _capture_evidence(driver, "TC007", "06_confirmation_not_displayed")
        raise AssertionError(
            "Confirmation dialog was not displayed after submitting KBZPay."
        ) from error

    _capture_evidence(driver, "TC007", "06_confirmation_dialog")
    before_confirm = driver.page_source
    try:
        _tc007_click_text(driver, "Confirm")
        WebDriverWait(driver, 30).until(
            lambda current_driver: (
                current_driver.page_source != before_confirm
                and not _tc007_has_text(current_driver, "Confirm")
            )
        )
    except Exception as error:
        _capture_evidence(driver, "TC007", "07_confirmation_action_failed")
        raise AssertionError("Confirmation action did not complete.") from error

    _capture_evidence(driver, "TC007", "07_confirmation_result")
    raise AssertionError(
        "Final success state not verified: the available runtime hierarchy "
        "does not identify a transaction-success landmark. Review TC007_07 "
        "confirmation-result evidence before adding a success assertion."
    )


def _tc007_edit_fields(driver):
    return sorted(
        (
            field
            for field in driver.find_elements(
                AppiumBy.CLASS_NAME,
                "android.widget.EditText",
            )
            if field.is_displayed() and field.is_enabled()
        ),
        key=lambda field: field.location["y"],
    )


def _tc007_is_top_up_screen(driver):
    top_up_content_visible = (
        _tc007_has_text(driver, "Enter or select ATOM phone number")
        or _tc007_has_text(driver, "Other Digital Payments")
        or (
            MOBILE_NUMBER
            and _tc007_has_text(driver, f"Top Up for {MOBILE_NUMBER}")
        )
    )
    return (
        driver.current_package == ATOM_APP_PACKAGE
        and _tc007_has_text(driver, "Top Up")
        and top_up_content_visible
    )


def _tc007_has_text(driver, label):
    root = ElementTree.fromstring(driver.page_source)
    target = label.strip().casefold()
    return any(
        node.get("displayed", "true").lower() == "true"
        and (
            (node.get("text") or "").strip().casefold() == target
            or (node.get("content-desc") or "").strip().casefold() == target
        )
        for node in root.iter()
    )


def _tc007_find_text_element(driver, label):
    elements = driver.find_elements(
        AppiumBy.ANDROID_UIAUTOMATOR,
        f'new UiSelector().textMatches("(?i)^{re.escape(label)}$")',
    )
    return next(
        (element for element in elements if element.is_displayed()),
        None,
    )


def _tc007_click_text(driver, text):
    wait = WebDriverWait(driver, 20)

    if text == "Other Digital Payments":
        # Locate the clickable parent containing the text
        parent = wait.until(
            EC.presence_of_element_located(
                (
                    AppiumBy.XPATH,
                    "//*[contains(@text, 'Other Digital Payments')]/.."
                )
            )
        )

        # Radio button is on the LEFT side of the text.
        rect = parent.rect

        radio_x = rect["x"] + 40
        radio_y = rect["y"] + rect["height"] // 2

        # Click radio button position
        driver.execute_script(
            "mobile: clickGesture",
            {
                "x": radio_x,
                "y": radio_y
            }
        )

        time.sleep(2)

        print("Clicked Other Digital Payments radio button.")

        return

    # Existing handling for other text elements
    element = wait.until(
        EC.presence_of_element_located(
            (
                AppiumBy.XPATH,
                f"//*[@text='{text}']"
            )
        )
    )

    element.click()


# def _tc007_click_text(driver, text):
#     wait = WebDriverWait(driver, 20)

#     if text.strip().casefold() == "top up":
#         return _tc007_click_top_up_submit(driver)

#     if text == "Other Digital Payments":
#         # Find the text element
#         text_element = wait.until(
#             EC.presence_of_element_located(
#                 (AppiumBy.XPATH,
#                  "//*[contains(@text, 'Other Digital Payments')]")
#             )
#         )

#         # Get its clickable parent View
#         parent = text_element.find_element(
#             AppiumBy.XPATH, ".."
#         )

#         # Click the parent instead of the TextView
#         driver.execute_script(
#             "mobile: clickGesture",
#             {
#                 "x": parent.rect["x"] + parent.rect["width"] // 2,
#                 "y": parent.rect["y"] + parent.rect["height"] // 2
#             }
#         )

#         time.sleep(2)
#         print("PASS: Other Digital Payments selected.")
#         return

#     # Existing handling for other text elements
#     bounds = wait.until(
#         lambda d: d.find_element(
#             AppiumBy.XPATH,
#             f"//*[@text='{text}']"
#         ).rect
#     )

#     driver.execute_script(
#         "mobile: clickGesture",
#         {
#             "x": bounds["x"] + bounds["width"] // 2,
#             "y": bounds["y"] + bounds["height"] // 2
#         }
#     )


def _tc007_click_top_up_submit(driver):
    button_label = f"Top Up for {MOBILE_NUMBER}"
    scroll_more = True
    for _ in range(10):
        clickable_parent = _tc007_find_clickable_parent(driver, button_label)
        if clickable_parent is not None:
            if not clickable_parent.is_displayed() or not clickable_parent.is_enabled():
                raise AssertionError(
                    "The visible Top Up submit control is not enabled."
                )
            _capture_evidence(driver, "TC007", "02_scratch_submit_visible")
            source_before_click = driver.page_source
            clickable_parent.click()
            return source_before_click

        bounds = _tc007_clickable_bounds_for_label(
            driver.page_source,
            button_label,
        )
        if bounds:
            _capture_evidence(driver, "TC007", "02_scratch_submit_visible")
            source_before_click = driver.page_source
            _tc007_click_bounds(driver, bounds)
            return source_before_click

        if not scroll_more:
            break
        scroll_more = _tc007_scroll_top_up_form(driver)

    clickable_target = WebDriverWait(driver, 20).until(
        lambda current_driver: (
            _tc007_find_clickable_parent(current_driver, button_label)
            or _tc007_clickable_bounds_for_label(
                current_driver.page_source,
                button_label,
            )
            or False
        )
    )
    source_before_click = driver.page_source
    if isinstance(clickable_target, tuple):
        _capture_evidence(driver, "TC007", "02_scratch_submit_visible")
        _tc007_click_bounds(driver, clickable_target)
    else:
        if not clickable_target.is_displayed() or not clickable_target.is_enabled():
            raise AssertionError(
                "The visible Top Up submit control is not enabled."
            )
        _capture_evidence(driver, "TC007", "02_scratch_submit_visible")
        clickable_target.click()
    return source_before_click


def _tc007_scroll_top_up_form(driver):
    scroll_views = driver.find_elements(
        AppiumBy.CLASS_NAME,
        "android.widget.ScrollView",
    )
    scroll_view = next(
        (
            element
            for element in scroll_views
            if element.is_displayed()
            and element.is_enabled()
            and element.get_attribute("scrollable") == "true"
        ),
        None,
    )
    if scroll_view is None:
        return False

    return bool(
        driver.execute_script(
            "mobile: scrollGesture",
            {
                "elementId": scroll_view.id,
                "direction": "down",
                "percent": 0.65,
            },
        )
    )


def _tc007_find_accessible_clickable_parent(driver, accessibility_id):
    elements = driver.find_elements(
        AppiumBy.ACCESSIBILITY_ID,
        accessibility_id,
    )
    for element in elements:
        if not element.is_displayed():
            continue
        for depth in range(1, 6):
            xpath = "/".join([".."] * depth)
            try:
                ancestor = element.find_element(AppiumBy.XPATH, xpath)
            except Exception:
                break
            if (
                ancestor.is_displayed()
                and ancestor.is_enabled()
                and ancestor.get_attribute("clickable") == "true"
            ):
                return ancestor
    return None


def _tc007_return_home_after_submit_failure(driver):
    back_control = WebDriverWait(driver, 10).until(
        lambda current_driver: (
            _tc007_find_accessible_clickable_parent(current_driver, "Back")
            or False
        )
    )
    back_control.click()
    WebDriverWait(driver, 30).until(_is_store_home_screen)
    _capture_evidence(driver, "TC007", "02_home_recovery_after_submit_failure")


def _tc007_click_text(driver, label):
    for _ in range(4):
        clickable_parent = _tc007_find_clickable_parent(driver, label)
        if clickable_parent is not None:
            clickable_parent.click()
            return

        bounds = _tc007_clickable_bounds_for_label(driver.page_source, label)
        if bounds:
            _tc007_click_bounds(driver, bounds)
            return
        scroll_bounds = _tc007_scrollable_bounds(driver.page_source)
        if scroll_bounds is None:
            break
        _tc007_scroll(driver, scroll_bounds)

    bounds = WebDriverWait(driver, 20).until(
        lambda current_driver: (
            _tc007_find_clickable_parent(current_driver, label)
            or _tc007_clickable_bounds_for_label(
                current_driver.page_source,
                label,
            )
            or False
        )
    )
    if isinstance(bounds, tuple):
        _tc007_click_bounds(driver, bounds)
    else:
        bounds.click()


def _tc007_find_clickable_parent(driver, label):
    text_elements = driver.find_elements(
        AppiumBy.ANDROID_UIAUTOMATOR,
        f'new UiSelector().textMatches("(?i)^{re.escape(label)}$")',
    )
    for text_element in text_elements:
        if not text_element.is_displayed():
            continue
        for depth in range(1, 6):
            xpath = "/".join([".."] * depth)
            try:
                ancestor = text_element.find_element(AppiumBy.XPATH, xpath)
            except Exception:
                break
            if (
                ancestor.is_displayed()
                and ancestor.is_enabled()
                and ancestor.get_attribute("clickable") == "true"
            ):
                return ancestor
    return None


def _tc007_clickable_bounds_for_label(source, label):
    root = ElementTree.fromstring(source)
    parents = {child: parent for parent in root.iter() for child in parent}
    target = label.strip().casefold()
    for node in root.iter():
        if not (
            (node.get("text") or "").strip().casefold() == target
            or (node.get("content-desc") or "").strip().casefold() == target
        ):
            continue
        ancestor = node
        while ancestor is not None:
            if (
                ancestor.get("clickable", "").lower() == "true"
                and ancestor.get("enabled", "true").lower() == "true"
                and ancestor.get("displayed", "true").lower() == "true"
            ):
                return _tc007_parse_bounds(ancestor.get("bounds", ""))
            ancestor = parents.get(ancestor)
    return None


def _tc007_parse_bounds(bounds):
    match = re.fullmatch(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds)
    return tuple(map(int, match.groups())) if match else None


def _tc007_click_bounds(driver, bounds):
    root = ElementTree.fromstring(driver.page_source)
    source_width = int(root.attrib.get("width", "0"))
    source_height = int(root.attrib.get("height", "0"))
    window = driver.get_window_size()
    left, top, right, bottom = bounds
    driver.execute_script(
        "mobile: clickGesture",
        {
            "x": round((left + right) / 2 * window["width"] / source_width),
            "y": round((top + bottom) / 2 * window["height"] / source_height),
        },
    )


def _tc007_scroll(driver, bounds):
    root = ElementTree.fromstring(driver.page_source)
    source_width = int(root.attrib.get("width", "0"))
    source_height = int(root.attrib.get("height", "0"))
    window = driver.get_window_size()
    left, top, right, bottom = bounds
    driver.execute_script(
        "mobile: scrollGesture",
        {
            "left": round(left * window["width"] / source_width),
            "top": round(top * window["height"] / source_height),
            "width": round((right - left) * window["width"] / source_width),
            "height": round((bottom - top) * window["height"] / source_height),
            "direction": "down",
            "percent": 0.65,
        },
    )


def _tc007_scrollable_bounds(source):
    root = ElementTree.fromstring(source)
    return next(
        (
            _tc007_parse_bounds(node.get("bounds", ""))
            for node in root.iter()
            if node.get("scrollable", "").lower() == "true"
            and node.get("displayed", "true").lower() == "true"
            and _tc007_parse_bounds(node.get("bounds", ""))
        ),
        None,
    )


def _tc007_kbzpay_tile_bounds(driver):
    source = driver.page_source
    other_bounds = _tc007_clickable_bounds_for_label(
        source,
        "Other Digital Payments",
    )
    if other_bounds is None:
        return False
    root = ElementTree.fromstring(source)
    tiles = []
    for node in root.iter():
        bounds = _tc007_parse_bounds(node.get("bounds", ""))
        if not (
            bounds
            and node.get("class") == "android.view.View"
            and node.get("clickable", "").lower() == "true"
            and node.get("enabled", "true").lower() == "true"
            and node.get("displayed", "true").lower() == "true"
        ):
            continue
        left, top, right, bottom = bounds
        width, height = right - left, bottom - top
        if top >= other_bounds[3] and width >= 150 and height >= 150:
            if 0.8 <= width / height <= 1.2:
                tiles.append((top, left, bounds))
    tiles.sort()
    return tiles[1][2] if len(tiles) >= 2 else False


def _tc007_bounds_are_selected(driver, bounds):
    root = ElementTree.fromstring(driver.page_source)
    return any(
        _tc007_parse_bounds(node.get("bounds", "")) == bounds
        and (
            node.get("selected", "").lower() == "true"
            or node.get("checked", "").lower() == "true"
        )
        for node in root.iter()
    )


def _tc007_label_is_selected(driver, label):
    root = ElementTree.fromstring(driver.page_source)
    parents = {child: parent for parent in root.iter() for child in parent}
    target = label.strip().casefold()
    for node in root.iter():
        if not (
            (node.get("text") or "").strip().casefold() == target
            or (node.get("content-desc") or "").strip().casefold() == target
        ):
            continue
        ancestor = node
        while ancestor is not None:
            if (
                ancestor.get("selected", "").lower() == "true"
                or ancestor.get("checked", "").lower() == "true"
            ):
                return True
            ancestor = parents.get(ancestor)
    return False


def _tc007_dialog_message(source):
    root = ElementTree.fromstring(source)
    parts = []
    for node in root.iter():
        value = (node.get("text") or "").strip()
        if value and value.casefold() != "okay" and value not in parts:
            parts.append(value)
    return " ".join(parts) or "Invalid voucher dialog displayed."

    wait = WebDriverWait(driver, 30)
    wait.until(
        EC.visibility_of_element_located(
            (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("Top Up")')
        )
    )
    _capture_evidence(driver, "TC007", "top_up")

    edit_fields = wait.until(
        lambda current_driver: sorted(
            (
                field
                for field in current_driver.find_elements(
                    AppiumBy.CLASS_NAME,
                    "android.widget.EditText",
                )
                if field.is_displayed() and field.is_enabled()
            ),
            key=lambda field: field.location["y"],
        )
        if len(
            [
                field
                for field in current_driver.find_elements(
                    AppiumBy.CLASS_NAME,
                    "android.widget.EditText",
                )
                if field.is_displayed() and field.is_enabled()
            ]
        ) >= 2
        else False
    )
    phone_field, scratch_card_field = edit_fields[:2]

    if not MOBILE_NUMBER:
        raise AssertionError("MOBILE_NUMBER is not configured in .env.")
    phone_field.clear()
    phone_field.send_keys(MOBILE_NUMBER)
    if phone_field.get_attribute("text") != MOBILE_NUMBER:
        raise AssertionError(
            "The configured ATOM phone number was not entered correctly."
        )

    scratch_card_field.clear()
    scratch_card_field.send_keys(scratch_card_number)
    if scratch_card_field.get_attribute("text") != scratch_card_number:
        raise AssertionError("The scratch card number was not entered correctly.")
    _capture_evidence(driver, "TC007", "details_entered")

    top_up_button = wait.until(
        lambda current_driver: next(
            (
                element
                for element in current_driver.find_elements(
                    AppiumBy.CLASS_NAME,
                    "android.view.View",
                )
                if element.is_displayed()
                and element.is_enabled()
                and element.get_attribute("clickable") == "true"
                and 1490 <= element.location["y"] <= 1625
            ),
            False,
        )
    )
    before_submit = driver.page_source
    top_up_button.click()

    def _okay_dialog_visible(current_driver):
        return any(
            element.is_displayed() and element.is_enabled()
            for element in current_driver.find_elements(
                AppiumBy.ANDROID_UIAUTOMATOR,
                'new UiSelector().textMatches("(?i)^okay$")',
            )
        )

    try:
        wait.until(
            lambda current_driver: (
                current_driver.page_source != before_submit
                or _okay_dialog_visible(current_driver)
            )
        )
    except TimeoutException as error:
        _capture_evidence(driver, "TC007", "response_timeout")
        raise AssertionError(
            "No application response was detected after submitting the "
            "Top Up request. Result evidence was captured."
        ) from error

    response_source = driver.page_source
    _capture_evidence(driver, "TC007", "response_received")
    okay_buttons = [
        element
        for element in driver.find_elements(
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().textMatches("(?i)^okay$")',
        )
        if element.is_displayed() and element.is_enabled()
    ]
    if okay_buttons:
        root = ElementTree.fromstring(response_source)
        message_parts = []
        for node in root.iter():
            value = (node.get("text") or "").strip()
            if value and value.casefold() != "okay" and value not in message_parts:
                message_parts.append(value)
        error_message = " ".join(message_parts) or "Invalid voucher dialog displayed."
        if MOBILE_NUMBER:
            error_message = error_message.replace(MOBILE_NUMBER, "[redacted]")

        _capture_evidence(driver, "TC007", "invalid_voucher")
        okay_buttons[0].click()
        try:
            wait.until(
                lambda current_driver: not _okay_dialog_visible(current_driver)
            )
        except Exception as dismissal_error:
            _capture_evidence(driver, "TC007", "after_dismissal_attempt")
            raise AssertionError(
                "Top Up voucher was rejected and the Okay dialog could not "
                f"be dismissed. Application message: {error_message}"
            ) from dismissal_error
        _capture_evidence(driver, "TC007", "after_dismissal")
        raise AssertionError(f"Top Up voucher was rejected: {error_message}")

    _capture_evidence(driver, "TC007", "outcome_unverified")
    raise AssertionError(
        "The Top Up response changed the screen, but no verified success "
        "landmark is defined by the captured UI evidence. Inspect "
        "the TC007 outcome_unverified XML and PNG evidence before "
        "adding a success assertion."
    )


def _is_ready_for_post_login_checks(driver):
    return _is_notification_permission_popup_visible(driver) or (
        driver.current_package == ATOM_APP_PACKAGE
        and not any(
            field.is_displayed()
            for field in driver.find_elements(
                AppiumBy.CLASS_NAME,
                "android.widget.EditText",
            )
        )
    )


def _is_store_home_screen(driver):
    if driver.current_package != ATOM_APP_PACKAGE:
        return False

    if (
        _is_home_tooltip_visible(driver)
        or _is_promotional_screen_visible(driver)
        or _is_notification_permission_popup_visible(driver)
    ):
        return False

    if any(
        field.is_displayed()
        for field in driver.find_elements(
            AppiumBy.CLASS_NAME,
            "android.widget.EditText",
        )
    ):
        return False

    home_controls = driver.find_elements(
        AppiumBy.ID,
        f"{ATOM_APP_PACKAGE}:id/dashboardFragment",
    )
    return any(control.is_displayed() for control in home_controls)


def _is_home_tooltip_visible(driver):
    root = ElementTree.fromstring(driver.page_source)
    tooltip_id = f"{ATOM_APP_PACKAGE}:id/fscv_id"
    return any(
        node.get("resource-id") == tooltip_id
        and node.get("displayed", "true").lower() == "true"
        for node in root.iter()
    )


def _is_promotional_screen_visible(driver):
    root = ElementTree.fromstring(driver.page_source)
    nodes = list(root.iter())
    promotional_ids = {
        f"{ATOM_APP_PACKAGE}:id/inapp_cover_image_frame_layout",
        f"{ATOM_APP_PACKAGE}:id/cover_image_relative_layout",
        f"{ATOM_APP_PACKAGE}:id/cover_image",
    }
    if any(
        node.get("resource-id") in promotional_ids
        and node.get("displayed", "true").lower() == "true"
        for node in nodes
    ):
        return True

    home_id = f"{ATOM_APP_PACKAGE}:id/dashboardFragment"
    if any(
        node.get("resource-id") == home_id
        and node.get("displayed", "true").lower() == "true"
        for node in nodes
    ):
        return False

    text = " ".join(
        " ".join((node.get("text", ""), node.get("content-desc", "")))
        for node in nodes
    ).casefold()
    has_offer_content = any(
        marker in text
        for marker in (
            "promotion",
            "offer",
            "special offer",
            "cashback",
            "buy now",
            "limited time",
            "lucky draw",
            "ongoing collection",
            "ticket count",
            "buy any pack",
        )
    )
    has_dismissal_option = any(
        node.get("text", "").strip().casefold()
        in {"skip", "close", "x", "×", "✕", "not now"}
        or node.get("content-desc", "").strip().casefold()
        in {"skip", "close", "x", "×", "✕", "not now"}
        for node in nodes
    )
    has_dismissal_option = (
        has_dismissal_option or _promotional_close_point(driver) is not None
    )
    return has_offer_content and has_dismissal_option


def _promotional_close_point(driver):
    root = ElementTree.fromstring(driver.page_source)
    parsed_bounds = []
    for node in root.iter():
        match = re.fullmatch(
            r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]",
            node.get("bounds", ""),
        )
        if match is not None:
            parsed_bounds.append(tuple(map(int, match.groups())))
    if not parsed_bounds:
        return None

    source_width = max(bounds[2] for bounds in parsed_bounds)
    source_height = max(bounds[3] for bounds in parsed_bounds)
    if not source_width or not source_height:
        return None

    screen = driver.get_window_size()
    candidates = []
    for node in root.iter():
        if node.get("clickable", "").lower() != "true":
            continue
        bounds_match = re.fullmatch(
            r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]",
            node.get("bounds", ""),
        )
        if bounds_match is None:
            continue

        left, top, right, bottom = map(int, bounds_match.groups())
        if (
            left >= source_width * 0.75
            and top <= source_height * 0.2
            and right > left
            and bottom > top
        ):
            candidates.append((top, -left, left, top, right, bottom))

    if not candidates:
        return None

    _, _, left, top, right, bottom = min(candidates)
    return {
        "x": round((left + right) / 2 * screen["width"] / source_width),
        "y": round((top + bottom) / 2 * screen["height"] / source_height),
    }


def _is_notification_permission_popup_visible(driver):
    root = ElementTree.fromstring(driver.page_source)
    nodes = list(root.iter())
    has_allow_button = any(
        node.get("text", "").strip().casefold() == "allow"
        or node.get("resource-id", "").endswith(
            ":id/permission_allow_button"
        )
        for node in nodes
    )
    if not has_allow_button:
        return False

    notification_text_present = any(
        "notification" in " ".join(
            (
                node.get("text", ""),
                node.get("content-desc", ""),
            )
        ).casefold()
        for node in nodes
    )
    return notification_text_present


def _is_in_app_notifications_screen(driver):
    root = ElementTree.fromstring(driver.page_source)
    has_notifications_title = any(
        node.get("text", "").strip().casefold() == "notifications"
        for node in root.iter()
    )
    has_back_control = any(
        node.get("content-desc", "").strip().casefold() == "back"
        for node in root.iter()
    )
    return has_notifications_title and has_back_control


def _dismiss_in_app_notifications_screen(driver):
    if not _is_in_app_notifications_screen(driver):
        return False

    back_button = next(
        (
            element
            for element in driver.find_elements(
                AppiumBy.ACCESSIBILITY_ID,
                "Back",
            )
            if element.is_displayed() and element.is_enabled()
        ),
        None,
    )
    if back_button is None:
        raise TimeoutException(
            "The in-app Notifications screen is visible, but its Back "
            "control could not be located."
        )

    before_source = driver.page_source
    back_button.click()
    WebDriverWait(driver, 10).until(
        lambda current_driver: (
            current_driver.page_source != before_source
            or not _is_in_app_notifications_screen(current_driver)
        )
    )
    return True


def _allow_notification_permission_if_present(driver):
    if not _is_notification_permission_popup_visible(driver):
        return False

    allow_locators = (
        (
            AppiumBy.ID,
            "com.android.permissioncontroller:id/permission_allow_button",
        ),
        (
            AppiumBy.ID,
            "com.google.android.permissioncontroller:id/permission_allow_button",
        ),
        (
            AppiumBy.ID,
            "com.android.packageinstaller:id/permission_allow_button",
        ),
        (
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().textMatches("(?i)^allow$")',
        ),
    )
    allow_button = next(
        (
            element
            for locator in allow_locators
            for element in driver.find_elements(*locator)
            if element.is_displayed() and element.is_enabled()
        ),
        None,
    )
    if allow_button is None:
        raise TimeoutException(
            "Notification permission dialog is visible, but its Allow "
            "button could not be located."
        )

    allow_button.click()
    WebDriverWait(driver, 10).until(
        lambda current_driver: (
            not _is_notification_permission_popup_visible(current_driver)
        )
    )
    print("Allowed notification permission.")
    return True


def _save_tc006_ui_hierarchy(snapshots):
    root = ElementTree.Element(
        "tc006_ui_hierarchies",
        {"package": ATOM_APP_PACKAGE},
    )
    for stage, source in snapshots:
        snapshot = ElementTree.SubElement(root, "snapshot", {"stage": stage})
        snapshot.append(ElementTree.fromstring(source))

    UI_DUMP_DIR.mkdir(parents=True, exist_ok=True)
    execution_id = _get_execution_id()
    stage = re.sub(
        r"[^a-z0-9]+", "_", snapshots[-1][0].lower()
    ).strip("_")
    sequence = 0
    while True:
        suffix = f"_{sequence}" if sequence else ""
        path = UI_DUMP_DIR / (
            f"atom_store_tc006_{stage}_{execution_id}{suffix}.xml"
        )
        try:
            with path.open("xb") as output:
                ElementTree.ElementTree(root).write(
                    output,
                    encoding="utf-8",
                    xml_declaration=True,
                )
            return path
        except FileExistsError:
            sequence += 1


def _dismiss_promotional_screen(driver):
    if not _is_promotional_screen_visible(driver):
        return False
    before_source = driver.page_source

    close_locators = (
        (AppiumBy.ACCESSIBILITY_ID, "inapp_close_btn"),
        (
            AppiumBy.ID,
            f"{ATOM_APP_PACKAGE}:id/inapp_close_btn",
        ),
        (AppiumBy.ACCESSIBILITY_ID, "Close"),
        (AppiumBy.ACCESSIBILITY_ID, "Dismiss"),
        (AppiumBy.ACCESSIBILITY_ID, "Skip"),
        (AppiumBy.ACCESSIBILITY_ID, "Not Now"),
        (
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().textMatches("(?i)^(skip|close|x|×|✕|not now)$")',
        ),
        (
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().descriptionMatches("(?i).*(skip|close|dismiss|not now).*")',
        ),
    )
    close_button = next(
        (
            element
            for locator in close_locators
            for element in driver.find_elements(*locator)
            if element.is_displayed() and element.is_enabled()
        ),
        None,
    )

    if close_button:
        close_button.click()
    else:
        close_point = _promotional_close_point(driver)
        if close_point is None:
            raise TimeoutException(
                "A promotional screen is visible, but no supported "
                "dismissal control was found."
            )
        driver.execute_script("mobile: clickGesture", close_point)

    WebDriverWait(driver, 30).until(
        lambda current_driver: (
            current_driver.page_source != before_source
            or not _is_promotional_screen_visible(current_driver)
        )
    )
    return True


def _handle_pre_home_screens(driver):
    dismissed_tooltips = 0
    dismissed_promotions = 0

    while True:
        if _allow_notification_permission_if_present(driver):
            continue

        if _dismiss_in_app_notifications_screen(driver):
            continue

        if _is_promotional_screen_visible(driver):
            if dismissed_promotions >= MAX_PROMOTIONAL_SCREENS:
                raise TimeoutException(
                    "Promotional screens remained after "
                    f"{MAX_PROMOTIONAL_SCREENS} dismissal attempts."
                )
            before_source = driver.page_source
            _dismiss_promotional_screen(driver)
            dismissed_promotions += 1
            WebDriverWait(driver, 5).until(
                lambda current_driver: (
                    current_driver.page_source != before_source
                    or _is_notification_permission_popup_visible(
                        current_driver
                    )
                    or _is_home_tooltip_visible(current_driver)
                    or _is_store_home_screen(current_driver)
                )
            )
            continue

        if _is_home_tooltip_visible(driver):
            if dismissed_tooltips >= MAX_HOME_TOOLTIPS:
                raise TimeoutException(
                    "Home onboarding tooltips remained visible after "
                    f"{MAX_HOME_TOOLTIPS} taps."
                )
            before_source = driver.page_source
            before_screenshot = driver.get_screenshot_as_png()
            tooltip_overlay = next(
                (
                    element
                    for element in driver.find_elements(
                        AppiumBy.ID,
                        f"{ATOM_APP_PACKAGE}:id/fscv_id",
                    )
                    if element.is_displayed() and element.is_enabled()
                ),
                None,
            )
            if tooltip_overlay:
                tooltip_overlay.click()
            else:
                screen = driver.get_window_size()
                driver.execute_script(
                    "mobile: clickGesture",
                    {
                        "x": screen["width"] // 2,
                        "y": screen["height"] // 2,
                    },
                )
            dismissed_tooltips += 1
            WebDriverWait(driver, 5).until(
                lambda current_driver: (
                    not _is_home_tooltip_visible(current_driver)
                    or current_driver.page_source != before_source
                    or current_driver.get_screenshot_as_png()
                    != before_screenshot
                    or _is_notification_permission_popup_visible(
                        current_driver
                    )
                )
            )
            continue

        if _is_store_home_screen(driver):
            print(
                f"Dismissed {dismissed_tooltips} home onboarding tooltip(s) "
                f"and {dismissed_promotions} promotional screen(s)."
            )
            return

        WebDriverWait(driver, 30).until(
            lambda current_driver: (
                _is_notification_permission_popup_visible(current_driver)
                or _is_in_app_notifications_screen(current_driver)
                or _is_home_tooltip_visible(current_driver)
                or _is_promotional_screen_visible(current_driver)
                or _is_store_home_screen(current_driver)
            )
        )


def _verify_store_home_screen(driver, testcase, screenshot_prefix):
    print(f"\n--- {testcase}: Verify ATOM Store home screen ---")

    wait = WebDriverWait(driver, 30)
    wait.until(_is_ready_for_post_login_checks)

    hierarchy_snapshots = [("before_dismissal", driver.page_source)]
    _capture_evidence(driver, "TC006", "before_dismissal")
    hierarchy_path = _save_tc006_ui_hierarchy(hierarchy_snapshots)

    try:
        _handle_pre_home_screens(driver)
    except TimeoutException:
        hierarchy_snapshots.append(
            ("after_dismissal_attempt", driver.page_source)
        )
        _capture_evidence(driver, "TC006", "after_dismissal_attempt")
        hierarchy_path = _save_tc006_ui_hierarchy(hierarchy_snapshots)
        screenshot_path, screenshot_hierarchy_path = _save_screenshot(
            driver,
            f"{screenshot_prefix}_dismissal_failed.png",
        )
        print(
            f"{testcase} did not reach the home screen. "
            f"Current UI hierarchy saved to {hierarchy_path}; "
            f"screenshot saved to {screenshot_path}; "
            f"screenshot hierarchy saved to {screenshot_hierarchy_path}."
        )
        raise

    hierarchy_snapshots.append(("home_screen", driver.page_source))
    _capture_evidence(driver, "TC006", "home_screen")
    hierarchy_path = _save_tc006_ui_hierarchy(hierarchy_snapshots)

    screenshot_path, screenshot_hierarchy_path = _save_screenshot(
        driver,
        f"{screenshot_prefix}_home_verified.png",
    )
    print(
        "PASS: ATOM Store home screen is displayed with the Popular control "
        "and no OTP entry fields. "
        f"Home screen evidence saved to {screenshot_path}; "
        f"screenshot hierarchy saved to {screenshot_hierarchy_path}; "
        f"TC006 snapshot hierarchy saved to {hierarchy_path}."
    )


def _restart_to_welcome_screen(driver):
    driver.terminate_app(ATOM_APP_PACKAGE)
    driver.execute_script(
        "mobile: clearApp",
        {"appId": ATOM_APP_PACKAGE},
    )
    driver.activate_app(ATOM_APP_PACKAGE)
    WebDriverWait(driver, 30).until(
        EC.visibility_of_element_located(
            (AppiumBy.ACCESSIBILITY_ID, "Logo")
        )
    )





def _start_negative_mobile_flow(driver, language_id, testcase, language):
    _restart_to_welcome_screen(driver)
    _select_language(driver, language_id, f"{testcase.lower()}_{language}")
    _open_login_screen(driver, f"{testcase.lower()}_login_screen")


def _reject_mobile_number(
    driver,
    mobile_number,
    testcase,
    check_retained_value=True,
):
    print(f"\n--- {testcase}: Reject invalid mobile number ---")

    wait = WebDriverWait(driver, 20)
    phone_field = wait.until(
        EC.element_to_be_clickable(
            (AppiumBy.CLASS_NAME, "android.widget.EditText")
        )
    )
    phone_field.clear()
    if mobile_number:
        phone_field.send_keys(mobile_number)

    submit_buttons = [
        button
        for button in driver.find_elements(
            AppiumBy.CLASS_NAME,
            "android.widget.Button",
        )
        if button.is_displayed()
    ]
    assert submit_buttons, f"{testcase} FAIL: Login button was not found."
    submit_button = max(
        submit_buttons,
        key=lambda button: button.location["y"] + button.size["height"],
    )

    if submit_button.is_enabled():
        submit_button.click()

    time.sleep(2)
    phone_fields = [
        field
        for field in driver.find_elements(
            AppiumBy.CLASS_NAME,
            "android.widget.EditText",
        )
        if field.is_displayed()
    ]
    assert phone_field in phone_fields, (
        f"{testcase} FAIL: Invalid phone submission left the phone-entry "
        "screen."
    )
    entered_value = phone_field.get_attribute("text")
    if check_retained_value:
        assert entered_value == mobile_number, (
            f"{testcase} FAIL: The phone field did not retain the rejected "
            "value."
        )

    _save_screenshot(driver, f"atom_store_{testcase.lower()}_rejected.png")
    print(
        f"PASS: {testcase} was rejected; the phone-entry screen remained "
        f"visible. Field value after input: {entered_value!r}."
    )


