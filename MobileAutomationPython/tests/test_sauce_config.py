from utils import driver_factory
from utils.sauce_config import ATOM_APP_ID, SAUCE_URL


def test_android_driver_always_uses_sauce_labs(monkeypatch):
    captured = {}

    def fake_remote(*, command_executor, options):
        captured["command_executor"] = command_executor
        captured["capabilities"] = options.to_capabilities()
        return object()

    monkeypatch.setattr(driver_factory.webdriver, "Remote", fake_remote)
    monkeypatch.setattr(
        driver_factory,
        "get_sauce_capabilities",
        lambda test_name: {"name": test_name},
    )

    driver_factory.create_android_driver(
        "Sauce Android test",
        app=ATOM_APP_ID,
    )

    assert captured["command_executor"] == SAUCE_URL
    assert captured["capabilities"]["appium:app"] == ATOM_APP_ID
    assert captured["capabilities"]["sauce:options"] == {
        "name": "Sauce Android test"
    }


def test_browser_driver_always_uses_sauce_labs(monkeypatch):
    captured = {}

    def fake_remote(*, command_executor, options):
        captured["command_executor"] = command_executor
        captured["capabilities"] = options.to_capabilities()
        return object()

    monkeypatch.setattr(driver_factory.webdriver, "Remote", fake_remote)
    monkeypatch.setattr(
        driver_factory,
        "get_sauce_capabilities",
        lambda test_name: {"name": test_name},
    )

    driver_factory.create_android_driver(
        "Sauce browser test",
        browser_name="Chrome",
    )

    assert captured["command_executor"] == SAUCE_URL
    assert captured["capabilities"]["browserName"] == "Chrome"
    assert captured["capabilities"]["sauce:options"] == {
        "name": "Sauce browser test"
    }
