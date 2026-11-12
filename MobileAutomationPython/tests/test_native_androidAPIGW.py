import re
import time
from pathlib import Path
from xml.etree import ElementTree

import pytest
from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from utils.sauce_config import ATOM_APP_PACKAGE, MOBILE_NUMBER


SCREENSHOT_DIR = Path("reports/screenshots")
UI_DUMP_DIR = Path("reports/ui_dumps")
MAX_HOME_TOOLTIPS = 10
MAX_PROMOTIONAL_SCREENS = 5

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
    # "TC007": (
    #     "Verify the user can open the Popular screen",
    #     "Popular",
    #     "Tap the Popular chip on the home screen.",
    #     "The displayed screen changes to the Popular content.",
    # ),
#     "TC008": (
#         "Verify the user can select Burmese",
#         "Burmese",
#         "Open the language selector and choose Burmese.",
#         "Burmese is selected and the app returns to the Welcome screen.",
#     ),
#     "TC009": (
#         "Verify the user can open the login screen in Burmese",
#         "Burmese",
#         "Tap the login option on the Welcome screen.",
#         "The login screen and mobile-number field are displayed.",
#     ),
#     "TC010": (
#         "Verify the user can log in with Burmese selected",
#         "Configured mobile number and SMS OTP",
#         "Enter the configured mobile number and submit the received OTP.",
#         "The mobile number and valid OTP are accepted.",
#     ),
#     "TC011": (
#         "Verify the ATOM Store home screen after Burmese login",
#         "Burmese; authenticated user",
#         "Wait for the home screen after OTP submission.",
#         "The app remains foregrounded and OTP fields are no longer displayed.",
#     ),
#     "TC012": (
#         "Verify the user can select Chinese",
#         "Chinese",
#         "Open the language selector and choose Chinese.",
#         "Chinese is selected and the app returns to the Welcome screen.",
#     ),
#     "TC013": (
#         "Verify the user can open the login screen in Chinese",
#         "Chinese",
#         "Tap the login option on the Welcome screen.",
#         "The login screen and mobile-number field are displayed.",
#     ),
#     "TC014": (
#         "Verify the user can log in with Chinese selected",
#         "Configured mobile number and SMS OTP",
#         "Enter the configured mobile number and submit the received OTP.",
#         "The mobile number and valid OTP are accepted.",
#     ),
#     "TC015": (
#         "Verify the ATOM Store home screen after Chinese login",
#         "Chinese; authenticated user",
#         "Wait for the home screen after OTP submission.",
#         "The app remains foregrounded and OTP fields are no longer displayed.",
#     ),
#     "TC016": (
#         "Verify an empty English mobile number is rejected",
#         "Empty mobile number",
#         "Submit the login form without entering a mobile number.",
#         "The app remains on the mobile-number entry screen.",
#     ),
#     "TC017": (
#         "Verify an invalid English mobile number is rejected",
#         "0000000000",
#         "Submit an invalid mobile number.",
#         "The app remains on the mobile-number entry screen.",
#     ),
#     "TC018": (
#         "Verify an empty Burmese mobile number is rejected",
#         "Empty mobile number; Burmese",
#         "Submit the login form without entering a mobile number.",
#         "The app remains on the mobile-number entry screen.",
#     ),
#     "TC019": (
#         "Verify an invalid Burmese mobile number is rejected",
#         "0000000000; Burmese",
#         "Submit an invalid mobile number.",
#         "The app remains on the mobile-number entry screen.",
#     ),
#     "TC020": (
#         "Verify an empty Chinese mobile number is rejected",
#         "Empty mobile number; Chinese",
#         "Submit the login form without entering a mobile number.",
#         "The app remains on the mobile-number entry screen.",
#     ),
#     "TC021": (
#         "Verify an invalid Chinese mobile number is rejected",
#         "0000000000; Chinese",
#         "Submit an invalid mobile number.",
#         "The app remains on the mobile-number entry screen.",
#     ),
#     "TC022": (
#         "Verify an overlong English mobile number is rejected",
#         "0123456789012345",
#         "Enter and submit a number longer than the maximum length.",
#         "Please type valid ATOM Number.",
#     ),
#     "TC023": (
#         "Verify special characters are rejected for English",
#         "@#$%&*",
#         "Enter and submit special characters in the mobile-number field.",
#         "Please type valid ATOM Number.",
#     ),
#     "TC024": (
#         "Verify alphabetic input is rejected for English",
#         "abcdefgh",
#         "Enter and submit alphabetic characters in the mobile-number field.",
#         "Please type valid ATOM Number.",
#     ),
#     "TC025": (
#         "Verify an overlong Burmese mobile number is rejected",
#         "0123456789012345; Burmese",
#         "Enter and submit a number longer than the maximum length.",
#         "Please type valid ATOM Number.",
#     ),
#     "TC026": (
#         "Verify special characters are rejected for Burmese",
#         "@#$%&*; Burmese",
#         "Enter and submit special characters in the mobile-number field.",
#         "Please type valid ATOM Number.",
#     ),
#     "TC027": (
#         "Verify alphabetic input is rejected for Burmese",
#         "abcdefgh; Burmese",
#         "Enter and submit alphabetic characters in the mobile-number field.",
#         "Please type valid ATOM Number.",
#     ),
#     "TC028": (
#         "Verify an overlong Chinese mobile number is rejected",
#         "0123456789012345; Chinese",
#         "Enter and submit a number longer than the maximum length.",
#         "Please type valid ATOM Number.",
#     ),
#     "TC029": (
#         "Verify special characters are rejected for Chinese",
#         "@#$%&*; Chinese",
#         "Enter and submit special characters in the mobile-number field.",
#         "Please type valid ATOM Number.",
#     ),
#     "TC030": (
#         "Verify alphabetic input is rejected for Chinese",
#         "abcdefgh; Chinese",
#         "Enter and submit alphabetic characters in the mobile-number field.",
#         "Please type valid ATOM Number.",
#     ),
 }


def _run_testcase(node, testcase_id, test_function, *args):
    result = node._excel_test_case_results[testcase_id]
    try:
        test_function(*args)
    except Exception as error:
        result["Result"] = "Failed"
        result["Error Message"] = str(error)
        raise
    else:
        result["Result"] = "Passed"
        result["Error Message"] = ""


def _save_screenshot(driver, filename):
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    driver.save_screenshot(str(SCREENSHOT_DIR / filename))


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
        # ("TC007", _tc007_open_popular_window, atom_store_driver),
        # ("TC008", _tc008_select_burmese_language, atom_store_driver),
        # ("TC009", _tc009_open_login_screen, atom_store_driver),
        # ("TC010", _tc010_enter_mobile_number, atom_store_driver, capsys),
        # ("TC011", _tc011_verify_store_home_screen, atom_store_driver),
        # ("TC012", _tc012_select_chinese_language, atom_store_driver),
        # ("TC013", _tc013_open_login_screen, atom_store_driver),
        # ("TC014", _tc014_enter_mobile_number, atom_store_driver, capsys),
        # ("TC015", _tc015_verify_store_home_screen, atom_store_driver),
        # ("TC016", _tc016_reject_empty_mobile_number, atom_store_driver),
        # ("TC017", _tc017_reject_invalid_mobile_number, atom_store_driver),
        # (
        #     "TC018",
        #     _tc018_reject_empty_burmese_mobile_number,
        #     atom_store_driver,
        # ),
        # (
        #     "TC019",
        #     _tc019_reject_invalid_burmese_mobile_number,
        #     atom_store_driver,
        # ),
        # (
        #     "TC020",
        #     _tc020_reject_empty_chinese_mobile_number,
        #     atom_store_driver,
        # ),
        # (
        #     "TC021",
        #     _tc021_reject_invalid_chinese_mobile_number,
        #     atom_store_driver,
        # ),
        # (
        #     "TC022",
        #     _tc022_reject_overlong_english_mobile_number,
        #     atom_store_driver,
        # ),
        # (
        #     "TC023",
        #     _tc023_reject_special_characters_english,
        #     atom_store_driver,
        # ),
        # (
        #     "TC024",
        #     _tc024_reject_alphabetic_english_mobile_number,
        #     atom_store_driver,
        # ),
        # (
        #     "TC025",
        #     _tc025_reject_overlong_burmese_mobile_number,
        #     atom_store_driver,
        # ),
        # (
        #     "TC026",
        #     _tc026_reject_special_characters_burmese,
        #     atom_store_driver,
        # ),
        # (
        #     "TC027",
        #     _tc027_reject_alphabetic_burmese_mobile_number,
        #     atom_store_driver,
        # ),
        # (
        #     "TC028",
        #     _tc028_reject_overlong_chinese_mobile_number,
        #     atom_store_driver,
        # ),
        # (
        #     "TC029",
        #     _tc029_reject_special_characters_chinese,
        #     atom_store_driver,
        # ),
        # (
        #     "TC030",
        #     _tc030_reject_alphabetic_chinese_mobile_number,
        #     atom_store_driver,
        # ),
    ]
    for testcase in testcases:
        _run_testcase(request.node, testcase[0], testcase[1], *testcase[2:])


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
    path = UI_DUMP_DIR / "atom_store_tc006.xml"
    ElementTree.ElementTree(root).write(
        path,
        encoding="utf-8",
        xml_declaration=True,
    )
    return path


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
    hierarchy_path = _save_tc006_ui_hierarchy(hierarchy_snapshots)

    try:
        _handle_pre_home_screens(driver)
    except TimeoutException:
        hierarchy_snapshots.append(
            ("after_dismissal_attempt", driver.page_source)
        )
        hierarchy_path = _save_tc006_ui_hierarchy(hierarchy_snapshots)
        screenshot_path = f"{screenshot_prefix}_dismissal_failed.png"
        _save_screenshot(driver, screenshot_path)
        print(
            f"{testcase} did not reach the home screen. "
            f"Current UI hierarchy saved to {hierarchy_path}; "
            f"screenshot saved to reports/screenshots/{screenshot_path}."
        )
        raise

    hierarchy_snapshots.append(("home_screen", driver.page_source))
    hierarchy_path = _save_tc006_ui_hierarchy(hierarchy_snapshots)

    _save_screenshot(
        driver,
        f"{screenshot_prefix}_home_verified.png",
    )
    print(
        "PASS: ATOM Store home screen is displayed with the Popular control "
        "and no OTP entry fields. "
        f"Home screen evidence saved to reports/screenshots/"
        f"{screenshot_prefix}_home_verified.png. "
        f"UI hierarchy saved to {hierarchy_path}."
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


# def _tc008_select_burmese_language(driver):
#     _restart_to_welcome_screen(driver)
#     _select_language(driver, "rdUnicode", "tc008_burmese")


# def _tc009_open_login_screen(driver):
#     _open_login_screen(driver, "tc009_login_screen")


# def _tc010_enter_mobile_number(driver, capsys):
#     _enter_mobile_number(
#         driver,
#         capsys,
#         "TC010",
#         "atom_store_tc010",
#     )


# def _tc011_verify_store_home_screen(driver):
#     _verify_store_home_screen(
#         driver,
#         "TC011",
#         "atom_store_tc011",
#     )
#     time.sleep(15)  # Allow time for the home screen to stabilize before proceeding to the next test case.

# def _tc012_select_chinese_language(driver):
#     _restart_to_welcome_screen(driver)
#     _select_language(driver, "rdChinese", "tc012_chinese")


# def _tc013_open_login_screen(driver):
#     _open_login_screen(driver, "tc013_login_screen")


# def _tc014_enter_mobile_number(driver, capsys):
#     _enter_mobile_number(
#         driver,
#         capsys,
#         "TC014",
#         "atom_store_tc014",
#     )


# def _tc015_verify_store_home_screen(driver):
#     _verify_store_home_screen(
#         driver,
#         "TC015",
#         "atom_store_tc015",
#     )
#     time.sleep(15)  # Allow time for the home screen to stabilize before proceeding to the next test case.


# def _tc016_reject_empty_mobile_number(driver):
#     _restart_to_welcome_screen(driver)
#     _select_language(driver, "rdEnglish", "tc016_english")
#     _open_login_screen(driver, "tc016_login_screen")
#     _reject_mobile_number(driver, "", "TC016")


# def _tc017_reject_invalid_mobile_number(driver):
#     _reject_mobile_number(driver, "0000000000", "TC017")


# def _tc018_reject_empty_burmese_mobile_number(driver):
#     _start_negative_mobile_flow(
#         driver,
#         "rdUnicode",
#         "TC018",
#         "Burmese",
#     )
#     _reject_mobile_number(driver, "", "TC018")


# def _tc019_reject_invalid_burmese_mobile_number(driver):
#     _reject_mobile_number(driver, "0000000000", "TC019")


# def _tc020_reject_empty_chinese_mobile_number(driver):
#     _start_negative_mobile_flow(
#         driver,
#         "rdChinese",
#         "TC020",
#         "Chinese",
#     )
#     _reject_mobile_number(driver, "", "TC020")


# def _tc021_reject_invalid_chinese_mobile_number(driver):
#     _reject_mobile_number(driver, "0000000000", "TC021")


# def _tc022_reject_overlong_english_mobile_number(driver):
#     _start_negative_mobile_flow(driver, "rdEnglish", "TC022", "English")
#     _reject_mobile_number(
#         driver,
#         "0123456789012345",
#         "TC022",
#         check_retained_value=False,
#     )


# def _tc023_reject_special_characters_english(driver):
#     _reject_mobile_number(
#         driver,
#         "@#$%&*",
#         "TC023",
#         check_retained_value=False,
#     )


# def _tc024_reject_alphabetic_english_mobile_number(driver):
#     _reject_mobile_number(
#         driver,
#         "abcdefgh",
#         "TC024",
#         check_retained_value=False,
#     )


# def _tc025_reject_overlong_burmese_mobile_number(driver):
#     _start_negative_mobile_flow(driver, "rdUnicode", "TC025", "Burmese")
#     _reject_mobile_number(
#         driver,
#         "0123456789012345",
#         "TC025",
#         check_retained_value=False,
#     )


# def _tc026_reject_special_characters_burmese(driver):
#     _reject_mobile_number(
#         driver,
#         "@#$%&*",
#         "TC026",
#         check_retained_value=False,
#     )


# def _tc027_reject_alphabetic_burmese_mobile_number(driver):
#     _reject_mobile_number(
#         driver,
#         "abcdefgh",
#         "TC027",
#         check_retained_value=False,
#     )


# def _tc028_reject_overlong_chinese_mobile_number(driver):
#     _start_negative_mobile_flow(driver, "rdChinese", "TC028", "Chinese")
#     _reject_mobile_number(
#         driver,
#         "0123456789012345",
#         "TC028",
#         check_retained_value=False,
#     )


# def _tc029_reject_special_characters_chinese(driver):
#     _reject_mobile_number(
#         driver,
#         "@#$%&*",
#         "TC029",
#         check_retained_value=False,
#     )


# def _tc030_reject_alphabetic_chinese_mobile_number(driver):
#     _reject_mobile_number(
#         driver,
#         "abcdefgh",
#         "TC030",
#         check_retained_value=False,
#     )


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


# def _tc007_open_popular_window(driver):
#     print("\n--- TC007: Open Popular window ---")

#     screen = driver.get_window_size()
#     popular_x = round(screen["width"] * 0.62)
#     popular_y = round(screen["height"] * 0.095)

#     # The home screen shows a five-step onboarding overlay. Taps are intercepted
#     # by that overlay until its five pages have been advanced.
#     for _ in range(5):
#         driver.execute_script(
#             "mobile: clickGesture",
#             {"x": popular_x, "y": popular_y},
#         )
#         time.sleep(0.5)

#     before_source = driver.page_source
#     before_screenshot = driver.get_screenshot_as_png()

#     popular_items = driver.find_elements(
#         AppiumBy.ANDROID_UIAUTOMATOR,
#         'new UiSelector().text("Popular")',
#     )
#     popular_button = next(
#         (
#             item
#             for item in popular_items
#             if item.is_displayed() and item.is_enabled()
#         ),
#         None,
#     )

#     if popular_button:
#         popular_button.click()
#     else:
#         driver.execute_script(
#             "mobile: clickGesture",
#             {"x": popular_x, "y": popular_y},
#         )

#     time.sleep(3)
#     after_source = driver.page_source
#     # print("POPULAR SCREEN UI HIERARCHY:")
#     # print(after_source)
#     after_screenshot = driver.get_screenshot_as_png()
#     _save_screenshot(driver, "atom_store_tc007_popular.png")

#     assert after_source != before_source or after_screenshot != before_screenshot, (
#         "TC007 FAIL: The screen did not change after tapping the Popular "
#         "chip in the top-right offers row."
#     )

#     print(
#         "PASS: Tapped the Popular chip in the top-right offers row and "
#         "the displayed screen changed. "
#         "Review reports/screenshots/atom_store_tc007_popular.png "
#         "to confirm the Popular window."
#     )