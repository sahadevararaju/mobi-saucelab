from xml.etree import ElementTree

import pytest
from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import TimeoutException

from tests import test_native_androidAPIGW as apigw


class _FakeElement:
    def __init__(self, on_click=None):
        self._on_click = on_click

    def is_displayed(self):
        return True

    def is_enabled(self):
        return True

    def click(self):
        if self._on_click:
            self._on_click()


class _FakeTextWithParent:
    def __init__(self, parent):
        self.parent = parent

    def is_displayed(self):
        return True

    def find_element(self, by, xpath):
        assert by == AppiumBy.XPATH
        current = self
        for _ in xpath.split("/"):
            current = current.parent
            if current is None:
                raise LookupError("No parent element")
        return current


class _FakeClickableParent:
    def __init__(self, clickable, enabled=True):
        self.clickable = clickable
        self.enabled = enabled
        self.clicked = False
        self.parent = None

    def is_displayed(self):
        return True

    def is_enabled(self):
        return self.enabled

    def get_attribute(self, name):
        return "true" if name == "clickable" and self.clickable else "false"

    def click(self):
        self.clicked = True


class _FakeTopUpLocatorDriver:
    def __init__(self, text_elements):
        self.text_elements = text_elements
        self.page_source = "<hierarchy />"

    def find_elements(self, by, value):
        assert by == AppiumBy.ANDROID_UIAUTOMATOR
        return self.text_elements


class _FakeBackLocatorDriver:
    def __init__(self, back_element):
        self.back_element = back_element

    def find_elements(self, by, value):
        assert by == AppiumBy.ACCESSIBILITY_ID
        return [self.back_element] if value == "Back" else []


class _FakeDriver:
    current_package = apigw.ATOM_APP_PACKAGE

    def __init__(
        self,
        page_source,
        home_visible=False,
        tooltip_count=0,
        keep_tooltip=False,
        notification_permission=False,
        promotional_screens=0,
        promotions_before_tooltips=0,
        unlabeled_draw_promotion=False,
        notifications_after_promotion=False,
    ):
        self.page_source = page_source
        self.home_visible = home_visible
        self.click_gestures = []
        self.tooltip_count = tooltip_count
        self.tooltip_taps = 0
        self.keep_tooltip = keep_tooltip
        self.notification_permission = notification_permission
        self.promotional_screens = promotional_screens
        self.promotions_before_tooltips = promotions_before_tooltips
        self.unlabeled_draw_promotion = unlabeled_draw_promotion
        self.notifications_after_promotion = notifications_after_promotion
        self.promotional_dismissals = 0
        self.visual_frame = 0
        self.close_button = _FakeElement(self._dismiss_promotion)
        self.allow_button = _FakeElement(self._allow_notification)
        self.tooltip_overlay = _FakeElement(self._advance_tooltip)

    def find_elements(self, by, value):
        if (by, value) == (
            AppiumBy.CLASS_NAME,
            "android.widget.EditText",
        ):
            return []
        if (
            by,
            value,
        ) == (
            AppiumBy.ACCESSIBILITY_ID,
            "Back",
        ) and apigw._is_in_app_notifications_screen(self):
            return [_FakeElement(self._return_from_notifications)]
        if (by, value) == (
            AppiumBy.ID,
            f"{apigw.ATOM_APP_PACKAGE}:id/dashboardFragment",
        ):
            return [_FakeElement()] if self.home_visible else []
        if (by, value) == (
            AppiumBy.ID,
            f"{apigw.ATOM_APP_PACKAGE}:id/fscv_id",
        ) and apigw._is_home_tooltip_visible(self):
            return [self.tooltip_overlay]
        if self.close_button and apigw._is_promotional_screen_visible(
            self
        ) and "inapp_close_btn" in self.page_source and (by, value) in (
            (AppiumBy.ACCESSIBILITY_ID, "inapp_close_btn"),
            (
                AppiumBy.ID,
                f"{apigw.ATOM_APP_PACKAGE}:id/inapp_close_btn",
            ),
        ):
            return [self.close_button]
        if (
            by,
            value,
        ) in (
            (
                AppiumBy.ID,
                f"{apigw.ATOM_APP_PACKAGE}:id/skip_button",
            ),
            (
                AppiumBy.ANDROID_UIAUTOMATOR,
                'new UiSelector().textMatches("(?i)^(skip|close|x|×|✕|not now)$")',
            ),
        ) and apigw._is_promotional_screen_visible(self) and (
            "skip_button" in self.page_source
            or any(
                f'text="{label}"' in self.page_source
                for label in ("Skip", "Close", "X", "×", "✕", "Not Now")
            )
        ):
            return [self.close_button] if self.close_button else []
        if self.allow_button and (
            by,
            value,
        ) in (
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
        ):
            return [self.allow_button]
        return []

    def get_window_size(self):
        return {"width": 316, "height": 686}

    def get_screenshot_as_png(self):
        return f"screen-frame-{self.visual_frame}".encode()

    def execute_script(self, script, coordinates):
        self.click_gestures.append((script, coordinates))
        self.visual_frame += 1
        if self.keep_tooltip:
            return
        if (
            script == "mobile: clickGesture"
            and apigw._is_promotional_screen_visible(self)
            and coordinates == apigw._promotional_close_point(self)
        ):
            self._dismiss_promotion()
            return
        if (
            script == "mobile: clickGesture"
            and apigw._is_home_tooltip_visible(self)
        ):
            self.tooltip_taps += 1
            if self.tooltip_taps < self.tooltip_count:
                self._show_tooltip()
            else:
                self._show_next_screen()

    def _advance_tooltip(self):
        self.visual_frame += 1
        self.tooltip_taps += 1
        if self.keep_tooltip:
            return
        if self.tooltip_taps < self.tooltip_count:
            self._show_tooltip()
        else:
            self._show_next_screen()

    def _show_home(self):
        self.home_visible = True
        home_id = f"{apigw.ATOM_APP_PACKAGE}:id/dashboardFragment"
        self.page_source = (
            f'<hierarchy><node resource-id="{home_id}" displayed="true" />'
            "</hierarchy>"
        )

    def _show_promotion(self):
        if self.unlabeled_draw_promotion and self.promotional_dismissals:
            self._show_unlabeled_draw_promotion()
            return

        self.home_visible = True
        promo_id = (
            f"{apigw.ATOM_APP_PACKAGE}:id/"
            "inapp_cover_image_frame_layout"
        )
        close_id = f"{apigw.ATOM_APP_PACKAGE}:id/inapp_close_btn"
        self.page_source = (
            f'<hierarchy><node resource-id="{promo_id}" displayed="true">'
            f'<node resource-id="{close_id}" content-desc="inapp_close_btn" '
            'displayed="true" /></node></hierarchy>'
        )

    def _show_unlabeled_draw_promotion(self):
        self.home_visible = True
        self.page_source = (
            '<hierarchy><node class="android.widget.FrameLayout" '
            'resource-id="android:id/content" bounds="[0,136][1080,2274]">'
            '<node class="android.view.View" clickable="true" '
            'bounds="[912,172][1044,304]" />'
            '<node class="android.widget.TextView" '
            'text="For November Lucky Draw" />'
            '<node class="android.widget.TextView" '
            'text="(Ongoing Collection)" />'
            '<node class="android.widget.TextView" text="Ticket Count" />'
            "</node><node class=\"android.view.View\" "
            'bounds="[0,2274][1080,2340]" /></hierarchy>'
        )

    def _show_tooltip(self):
        self.home_visible = True
        tooltip_id = f"{apigw.ATOM_APP_PACKAGE}:id/fscv_id"
        home_id = f"{apigw.ATOM_APP_PACKAGE}:id/dashboardFragment"
        self.page_source = (
            f'<hierarchy><node resource-id="{tooltip_id}" displayed="true" />'
            f'<node resource-id="{home_id}" displayed="true" /></hierarchy>'
        )

    def _show_next_screen(self):
        promotions_pending = (
            self.promotional_dismissals < self.promotional_screens
        )
        if self.promotional_dismissals < self.promotions_before_tooltips:
            self._show_promotion()
        elif self.tooltip_taps < self.tooltip_count:
            self._show_tooltip()
        elif promotions_pending:
            self._show_promotion()
        else:
            self._show_home()

    def _dismiss_promotion(self):
        self.promotional_dismissals += 1
        if self.notifications_after_promotion:
            self._show_notifications_page()
        else:
            self._show_next_screen()

    def _allow_notification(self):
        self.notification_permission = False
        self._show_next_screen()

    def _show_notifications_page(self):
        self.page_source = (
            '<hierarchy><node text="Notifications" />'
            '<node content-desc="Back" /></hierarchy>'
        )

    def _return_from_notifications(self):
        self._show_home()

    def show_notification_permission(self):
        self.notification_permission = True
        self.page_source = (
            '<hierarchy><node package="com.android.permissioncontroller" '
            'text="Allow ATOM Store to send you notifications?" />'
            '<node package="com.android.permissioncontroller" '
            'resource-id="com.android.permissioncontroller:id/'
            'permission_allow_button" text="Allow" /></hierarchy>'
        )


def test_promotion_is_dismissed_until_home_landmark_is_visible():
    driver = _FakeDriver("<hierarchy />", promotional_screens=1)
    driver._show_promotion()

    assert not apigw._is_store_home_screen(driver)
    assert apigw._dismiss_promotional_screen(driver)

    assert driver.promotional_dismissals == 1
    assert apigw._is_store_home_screen(driver)


def test_welcome_screen_detection_waits_for_login_and_language_controls():
    class _WelcomeDriver:
        current_package = apigw.ATOM_APP_PACKAGE

        def __init__(self, visible_text):
            self.visible_text = visible_text

        def find_elements(self, by, value):
            if by != AppiumBy.ANDROID_UIAUTOMATOR:
                return []
            if 'text("လော့ဂ်အင်၀င်ရန်")' in value:
                return (
                    [_FakeElement()]
                    if "login" in self.visible_text
                    else []
                )
            if 'text("မြန်မာ | English | 中文")' in value:
                return (
                    [_FakeElement()]
                    if "language" in self.visible_text
                    else []
                )
            return []

    assert not apigw._is_welcome_screen_displayed(_WelcomeDriver(set()))
    assert apigw._is_welcome_screen_displayed(
        _WelcomeDriver({"login", "language"})
    )


def test_handles_permission_promotions_and_tooltips_in_interleaved_sequence():
    tooltip_id = f"{apigw.ATOM_APP_PACKAGE}:id/fscv_id"
    driver = _FakeDriver(
        f'<hierarchy><node resource-id="{tooltip_id}" displayed="true" />'
        "</hierarchy>",
        tooltip_count=3,
        promotional_screens=2,
        promotions_before_tooltips=1,
    )
    driver.show_notification_permission()

    apigw._handle_pre_home_screens(driver)

    assert not driver.notification_permission
    assert driver.promotional_dismissals == 2
    assert driver.tooltip_taps == 3
    assert apigw._is_store_home_screen(driver)


def test_returns_from_in_app_notifications_page_after_closing_promotion():
    driver = _FakeDriver(
        "<hierarchy />",
        promotional_screens=1,
        notifications_after_promotion=True,
    )
    driver._show_promotion()

    apigw._handle_pre_home_screens(driver)

    assert driver.promotional_dismissals == 1
    assert not apigw._is_in_app_notifications_screen(driver)
    assert apigw._is_store_home_screen(driver)


def test_home_screen_passes_without_tapping_when_optional_screens_absent():
    home_id = f"{apigw.ATOM_APP_PACKAGE}:id/dashboardFragment"
    driver = _FakeDriver(
        f'<hierarchy><node resource-id="{home_id}" displayed="true" />'
        "</hierarchy>",
        home_visible=True,
    )

    apigw._handle_pre_home_screens(driver)

    assert apigw._is_store_home_screen(driver)
    assert driver.click_gestures == []


def test_home_offer_and_notification_icon_are_not_mistaken_for_promotion():
    home_id = f"{apigw.ATOM_APP_PACKAGE}:id/dashboardFragment"
    driver = _FakeDriver(
        f'<hierarchy><node bounds="[0,0][1080,2408]">'
        '<node clickable="true" bounds="[934,82][1069,217]" />'
        '<node text="Best Offer" />'
        f'<node resource-id="{home_id}" displayed="true" />'
        "</node></hierarchy>",
        home_visible=True,
    )

    apigw._handle_pre_home_screens(driver)

    assert not apigw._is_promotional_screen_visible(driver)
    assert apigw._is_store_home_screen(driver)
    assert driver.click_gestures == []


def test_post_login_readiness_accepts_home_or_notification_but_not_otp():
    home_driver = _FakeDriver("<hierarchy />", home_visible=True)
    home_driver._show_home()
    assert apigw._is_ready_for_post_login_checks(home_driver)

    notification_driver = _FakeDriver("<hierarchy />")
    notification_driver.show_notification_permission()
    assert apigw._is_ready_for_post_login_checks(notification_driver)

    class _OtpDriver(_FakeDriver):
        def find_elements(self, by, value):
            if (by, value) == (
                AppiumBy.CLASS_NAME,
                "android.widget.EditText",
            ):
                return [_FakeElement()]
            return super().find_elements(by, value)

    otp_driver = _OtpDriver("<hierarchy />")
    assert not apigw._is_ready_for_post_login_checks(otp_driver)


def test_allows_notification_permission_when_popup_is_present():
    home_id = f"{apigw.ATOM_APP_PACKAGE}:id/dashboardFragment"
    driver = _FakeDriver(
        f'<hierarchy><node resource-id="{home_id}" displayed="true" />'
        "</hierarchy>",
        home_visible=True,
    )
    driver.show_notification_permission()

    assert apigw._allow_notification_permission_if_present(driver)
    assert not driver.notification_permission
    assert apigw._is_store_home_screen(driver)


def test_notification_permission_handler_is_noop_when_popup_is_absent():
    home_id = f"{apigw.ATOM_APP_PACKAGE}:id/dashboardFragment"
    driver = _FakeDriver(
        f'<hierarchy><node resource-id="{home_id}" displayed="true" />'
        "</hierarchy>",
        home_visible=True,
    )

    assert not apigw._allow_notification_permission_if_present(driver)
    assert driver.click_gestures == []


def test_does_not_allow_unrelated_permission_or_app_button():
    driver = _FakeDriver(
        '<hierarchy><node package="com.android.permissioncontroller" '
        'text="Allow access to location?" />'
        '<node package="com.android.permissioncontroller" '
        'resource-id="com.android.permissioncontroller:id/'
        'permission_allow_button" text="Allow" /></hierarchy>'
    )
    driver.allow_button = _FakeElement()

    assert not apigw._allow_notification_permission_if_present(driver)
    assert driver.click_gestures == []


def test_tooltip_dismissal_stops_at_safety_limit():
    tooltip_id = f"{apigw.ATOM_APP_PACKAGE}:id/fscv_id"
    driver = _FakeDriver(
        f'<hierarchy><node resource-id="{tooltip_id}" displayed="true" />'
        "</hierarchy>",
        tooltip_count=apigw.MAX_HOME_TOOLTIPS + 1,
    )

    with pytest.raises(TimeoutException, match="remained visible"):
        apigw._handle_pre_home_screens(driver)

    assert driver.tooltip_taps == apigw.MAX_HOME_TOOLTIPS


def test_uses_close_locator_from_observed_appium_hierarchy():
    driver = _FakeDriver("<hierarchy />", promotional_screens=1)
    driver._show_promotion()
    apigw._dismiss_promotional_screen(driver)

    assert driver.click_gestures == []
    assert driver.promotional_dismissals == 1


def test_dismisses_lucky_draw_promotion_with_unlabeled_top_right_close():
    driver = _FakeDriver(
        "<hierarchy />",
        promotional_screens=2,
        unlabeled_draw_promotion=True,
    )
    driver.show_notification_permission()

    apigw._handle_pre_home_screens(driver)

    assert not driver.notification_permission
    assert driver.promotional_dismissals == 2
    assert driver.click_gestures == [
        ("mobile: clickGesture", {"x": 286, "y": 70})
    ]
    assert apigw._is_store_home_screen(driver)


def test_does_not_tap_when_home_landmark_is_already_visible():
    home_id = f"{apigw.ATOM_APP_PACKAGE}:id/dashboardFragment"
    driver = _FakeDriver(
        f'<hierarchy><node resource-id="{home_id}" displayed="true" />'
        "</hierarchy>",
        home_visible=True,
    )

    assert not apigw._dismiss_promotional_screen(driver)


def test_writes_before_and_after_hierarchies_to_one_xml_file(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(apigw, "UI_DUMP_DIR", tmp_path)
    monkeypatch.setattr(apigw, "EXECUTION_ID", "20261112_114750")
    before = '<hierarchy><node class="ImageView" /></hierarchy>'
    after = '<hierarchy><node text="Popular" /></hierarchy>'

    path = apigw._save_tc006_ui_hierarchy(
        [("before_dismissal", before), ("home_screen", after)]
    )

    root = ElementTree.parse(path).getroot()
    assert path.name == "atom_store_tc006_home_screen_20261112_114750.xml"
    assert [snapshot.get("stage") for snapshot in root] == [
        "before_dismissal",
        "home_screen",
    ]
    assert root.find(".//node[@class='ImageView']") is not None
    assert root.find(".//node[@text='Popular']") is not None


def test_evidence_capture_uses_shared_id_and_never_overwrites(
    tmp_path, monkeypatch
):
    screenshots = tmp_path / "screenshots"
    ui_dumps = tmp_path / "ui_dumps"
    monkeypatch.setattr(apigw, "SCREENSHOT_DIR", screenshots)
    monkeypatch.setattr(apigw, "UI_DUMP_DIR", ui_dumps)
    monkeypatch.setattr(apigw, "EXECUTION_ID", "20261112_114750")
    driver = _FakeDriver('<hierarchy><node text="Top Up" /></hierarchy>')

    first_png, first_xml = apigw._capture_evidence(
        driver,
        "TC007",
        "03_other_digital_payments",
    )
    driver.visual_frame += 1
    second_png, second_xml = apigw._capture_evidence(
        driver,
        "TC007",
        "03_other_digital_payments",
    )

    assert first_png.name == (
        "atom_store_tc007_03_other_digital_payments_20261112_114750.png"
    )
    assert first_xml.name == first_png.with_suffix(".xml").name
    assert second_png.name.endswith("20261112_114750_1.png")
    assert second_xml.name.endswith("20261112_114750_1.xml")
    assert first_png.read_bytes() == b"screen-frame-0"
    assert second_png.read_bytes() == b"screen-frame-1"
    assert "Top Up" in first_xml.read_text(encoding="utf-8")


def test_other_digital_payments_uses_observed_clickable_parent_bounds():
    source = (
        '<hierarchy width="1080" height="2340">'
        '<node class="android.view.View" clickable="true" enabled="true" '
        'displayed="true" bounds="[45,1417][515,1552]">'
        '<node class="android.widget.TextView" text="Other Digital Payments" '
        'clickable="false" bounds="[102,1457][515,1512]" />'
        '</node></hierarchy>'
    )

    assert apigw._tc007_clickable_bounds_for_label(
        source,
        "Other Digital Payments",
    ) == (45, 1417, 515, 1552)


def test_kbzpay_tile_is_second_tile_in_observed_first_icon_row():
    source = (
        '<hierarchy width="1080" height="2340">'
        '<node class="android.view.View" clickable="true" enabled="true" '
        'displayed="true" bounds="[45,1417][515,1552]">'
        '<node class="android.widget.TextView" text="Other Digital Payments" '
        'clickable="false" bounds="[102,1457][515,1512]" />'
        '</node>'
        '<node class="android.view.View" clickable="true" enabled="true" '
        'displayed="true" bounds="[45,1571][254,1780]" />'
        '<node class="android.view.View" clickable="true" enabled="true" '
        'displayed="true" bounds="[299,1571][508,1780]" />'
        '</hierarchy>'
    )
    driver = _FakeDriver(source)

    assert apigw._tc007_kbzpay_tile_bounds(driver) == (299, 1571, 508, 1780)


def test_top_up_text_clicks_enabled_clickable_parent_and_skips_header():
    header_parent = _FakeClickableParent(clickable=False)
    disabled_parent = _FakeClickableParent(clickable=True, enabled=False)
    submit_parent = _FakeClickableParent(clickable=True, enabled=True)
    header = _FakeTextWithParent(header_parent)
    disabled_submit = _FakeTextWithParent(disabled_parent)
    submit = _FakeTextWithParent(submit_parent)
    driver = _FakeTopUpLocatorDriver([header, disabled_submit, submit])

    apigw._tc007_click_text(driver, "Top Up")

    assert not header_parent.clicked
    assert not disabled_parent.clicked
    assert submit_parent.clicked


def test_back_accessibility_control_resolves_clickable_parent():
    back_parent = _FakeClickableParent(clickable=True, enabled=True)
    back_element = _FakeTextWithParent(back_parent)
    driver = _FakeBackLocatorDriver(back_element)

    parent = apigw._tc007_find_accessible_clickable_parent(driver, "Back")

    assert parent is back_parent
