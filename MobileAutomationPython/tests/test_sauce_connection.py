import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


@pytest.mark.sauce
def test_saucedemo_login(browser_driver):
    browser_driver.get("https://www.saucedemo.com/")

    assert "Swag Labs" in browser_driver.title

    username_field = browser_driver.find_element(By.CSS_SELECTOR, "#user-name")
    password_field = browser_driver.find_element(By.CSS_SELECTOR, "#password")
    login_button = browser_driver.find_element(By.CSS_SELECTOR, "#login-button")

    assert username_field.is_displayed()
    assert password_field.is_displayed()
    assert login_button.is_displayed()

    username_field.send_keys("standard_user")
    password_field.send_keys("secret_sauce")
    login_button.click()

    products_title = WebDriverWait(browser_driver, 20).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, ".title"))
    )

    assert products_title.text == "Products"
    assert "inventory.html" in browser_driver.current_url