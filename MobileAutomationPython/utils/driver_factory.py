from appium import webdriver
from appium.options.android import UiAutomator2Options

from utils.sauce_config import (
    ATOM_APP_ACTIVITY,
    ATOM_APP_PACKAGE,
    SAUCE_URL,
    get_sauce_capabilities,
)


def create_android_driver(test_name, app=None, browser_name=None):
    options = UiAutomator2Options()
    options.set_capability("platformName", "Android")
    options.set_capability("appium:automationName", "UiAutomator2")

    if app:
        options.set_capability("appium:app", app)
        options.set_capability("appium:appPackage", ATOM_APP_PACKAGE)
        options.set_capability("appium:appActivity", ATOM_APP_ACTIVITY)
        options.set_capability("appium:appWaitActivity", "*")
        options.set_capability("appium:appWaitDuration", 30000)

    if browser_name:
        options.set_capability("browserName", browser_name)

    options.set_capability(
        "sauce:options",
        get_sauce_capabilities(test_name),
    )

    return webdriver.Remote(
        command_executor=SAUCE_URL,
        options=options,
    )