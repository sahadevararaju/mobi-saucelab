# Mobile Automation with Appium

This project runs Android app and browser tests on Sauce Labs. The ATOM Store
scenario runs TC001 through TC030 in one ordered end-to-end test because each
step depends on the screen created by the previous step.

## Project Structure

```text
MobileAutomationPython/
|-- .env                 # local Sauce Labs credentials (not committed)
|-- .env.example         # environment variable template
|-- pytest.ini
|-- requirements.txt
|-- reports/
|   `-- screenshots/     # test evidence
|-- tests/
|   |-- conftest.py      # shared pytest driver fixtures
|   |-- test_native_android.py
|   `-- test_sauce_connection.py
`-- utils/
    |-- driver_factory.py
    `-- sauce_config.py
```

## Setup

In PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

The `.env` file is ignored by Git. Provide `SAUCE_USERNAME`,
`SAUCE_ACCESS_KEY`, and a valid `SAUCE_APP` reference. All test drivers connect
to Sauce Labs; there is no local Appium endpoint fallback.

## Run

```powershell
pytest
pytest tests/test_native_android.py
pytest tests/test_sauce_connection.py
```

TC005 pauses for the SMS OTP. Run the Android test from the VS Code
integrated terminal and enter the six-digit code when prompted. The test
accepts either six separate OTP boxes or one field that displays six boxes.
For an explicit interactive run, use:

```powershell
python -m pytest -s tests/test_native_android.py
```

TC001–TC030 run sequentially in a single session. TC001–TC007 run the initial
English flow and Popular screen check. TC008–TC011 clear and relaunch the app
to run the Burmese login flow; TC012–TC015 repeat this for Chinese. Enter the
SMS OTP each time it is requested. Each language flow verifies the home screen
after OTP submission. In `test_native_androidAPIGW.py`, TC006 conditionally
handles notification permission, promotional screens, and onboarding tooltips
before validating the Home screen; its UI hierarchy is saved to
`reports/ui_dumps/atom_store_tc006.xml`. The connection test opens SauceDemo in Chrome and verifies login. Each pytest
run writes its results to a timestamped workbook in `reports/`, for example
`Test_execution_report_20261110_165954_478.xlsx`, preserving reports from
previous runs. JUnit results are written to `reports/results.xml`, and ATOM
screenshots are written to `reports/screenshots/`.

TC016–TC017 run English negative mobile-number checks; TC018–TC019 repeat
them in Burmese, and TC020–TC021 repeat them in Chinese. Each pair submits an
empty and a too-short value and verifies the app remains on the phone-entry
screen without proceeding to OTP verification.

TC022–TC024 check overlong, special-character, and alphabetic mobile-number
inputs in English. TC025–TC027 repeat these checks in Burmese, and TC028–TC030
repeat them in Chinese. These cases verify that invalid input does not advance
to OTP verification; the app may filter or truncate the entered value.

The Excel report records each step in the ATOM Store sequence as a separate
row, with its TC ID and descriptive scenario in the Test Case ID and Test
Scenario columns. If a step fails, later cases remain listed as Not Run.