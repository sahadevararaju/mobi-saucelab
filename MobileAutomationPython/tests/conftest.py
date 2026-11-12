import pytest

from utils.driver_factory import create_android_driver
from utils.sauce_config import (
    ATOM_APP_ID,
    MOBILE_NUMBER,
)


@pytest.fixture
def atom_store_driver():
    if not MOBILE_NUMBER:
        pytest.skip("Set MOBILE_NUMBER in .env")

    driver = create_android_driver(
        test_name="ATOM Store - TC001 to TC030",
        app=ATOM_APP_ID,
    )
    yield driver
    driver.quit()


@pytest.fixture
def browser_driver():
    driver = create_android_driver(
        test_name="SauceDemo login validation",
        browser_name="Chrome",
    )
    yield driver
    driver.quit()

import re

from utils.excel_report import save_test_results


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "testcase(**metadata): Excel reporting metadata",
    )
    config._excel_test_results = []


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    reports = getattr(item, "_excel_reports", {})
    reports[report.when] = report
    item._excel_reports = reports

    if report.when != "teardown":
        return

    testcase_results = getattr(
        item,
        "_excel_test_case_results",
        None,
    )
    if testcase_results is not None:
        item.config._excel_test_results.extend(
            testcase_results.values()
        )
        return

    marker = item.get_closest_marker("testcase")
    metadata = marker.kwargs if marker else {}

    all_reports = list(reports.values())

    if any(r.failed for r in all_reports):
        status = "Failed"
    elif any(r.skipped for r in all_reports):
        status = "Skipped"
    else:
        status = "Passed"

    error_messages = [
        str(r.longrepr)
        for r in all_reports
        if r.failed and r.longrepr
    ]

    test_id = metadata.get("id")
    if not test_id:
        match = re.search(r"TC\d+", item.name, re.IGNORECASE)
        test_id = match.group(0).upper() if match else item.name

    result = {
        "Test Case ID": test_id,
        "Module/Feature": metadata.get(
            "module", item.originalname or item.name
        ),
        "Test Data": metadata.get("test_data", ""),
        "Pre-condition": metadata.get("pre_condition", ""),
        "Test Scenario": metadata.get("scenario", item.name),
        "Test Steps": metadata.get("steps", ""),
        "Expected Result": metadata.get("expected_result", ""),
        "Environment": metadata.get("environment", "Local"),
        "Result": status,
        "Error Message": "\n".join(error_messages),
    }

    item.config._excel_test_results.append(result)


def pytest_sessionfinish(session, exitstatus):
    results = getattr(
        session.config, "_excel_test_results", []
    )

    save_test_results(results)
