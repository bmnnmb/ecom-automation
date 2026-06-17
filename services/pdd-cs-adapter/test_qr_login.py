import asyncio
import importlib
import json
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch


SERVICE_DIR = Path(__file__).resolve().parent


def load_module(name: str):
    sys.path.insert(0, str(SERVICE_DIR))
    try:
        sys.modules.pop(name, None)
        return importlib.import_module(name)
    finally:
        if sys.path and sys.path[0] == str(SERVICE_DIR):
            sys.path.pop(0)


class PddLoginTests(unittest.TestCase):
    def setUp(self):
        self._modules = ["config", "playwright_bot", "routes.system_routes", "routes"]
        self._env_backup = os.environ.copy()
        for name in self._modules:
            sys.modules.pop(name, None)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._env_backup)
        for name in self._modules:
            sys.modules.pop(name, None)

    def test_settings_load_without_open_platform_credentials(self):
        os.environ.pop("PDD_CLIENT_ID", None)
        os.environ.pop("PDD_CLIENT_SECRET", None)
        os.environ.pop("PDD_ACCESS_TOKEN", None)
        os.environ.pop("PDD_USERNAME", None)
        os.environ.pop("PDD_PASSWORD", None)

        module = load_module("config")

        self.assertIsNone(module.settings.PDD_CLIENT_ID)
        self.assertIsNone(module.settings.PDD_CLIENT_SECRET)
        self.assertIsNone(module.settings.PDD_ACCESS_TOKEN)

    def test_start_password_login_uses_saved_storage_state_and_opens_workbench(self):
        os.environ["PDD_CLIENT_ID"] = ""
        os.environ["PDD_CLIENT_SECRET"] = ""
        os.environ["PDD_ACCESS_TOKEN"] = ""
        os.environ["PDD_WORKBENCH_URL"] = "https://example.com/workbench"

        with tempfile.TemporaryDirectory() as tmp_dir:
            os.environ["PDD_DATA_DIR"] = tmp_dir
            module = load_module("playwright_bot")
            bot = module.PlaywrightBot()

            storage_state_path = Path(tmp_dir) / "pdd_storage_state.json"
            storage_state_path.write_text("{}", encoding="utf-8")

            class FakePage:
                def __init__(self):
                    self.url = "https://example.com/workbench"
                    self.goto_calls = []

                def is_closed(self):
                    return False

                async def goto(self, url, wait_until=None):
                    self.goto_calls.append((url, wait_until))

                def locator(self, selector):
                    class FakeLocator:
                        async def count(self):
                            return 0

                    return FakeLocator()

                async def wait_for_selector(self, selector, timeout=None, state=None):
                    return None

                async def wait_for_timeout(self, timeout):
                    return None

            class FakeContext:
                def __init__(self):
                    self.page = FakePage()

                async def new_page(self):
                    return self.page

                async def cookies(self):
                    return [{"name": "PASS_ID", "domain": ".pinduoduo.com"}]

                async def storage_state(self, path=None):
                    Path(path).write_text(
                        json.dumps({"cookies": [{"name": "PASS_ID", "domain": ".pinduoduo.com"}]}),
                        encoding="utf-8",
                    )
                    return {}

            class FakeBrowser:
                def __init__(self):
                    self.kwargs = None
                    self.context = FakeContext()
                    self.launch_kwargs = None

                async def new_context(self, **kwargs):
                    self.kwargs = kwargs
                    return self.context

            class FakeChromium:
                def __init__(self, browser):
                    self.browser = browser

                async def launch(self, **kwargs):
                    self.browser.launch_kwargs = kwargs
                    return self.browser

            class FakePlaywright:
                def __init__(self):
                    self.browser = FakeBrowser()
                    self.chromium = FakeChromium(self.browser)

                async def stop(self):
                    return None

            class FakeAsyncPlaywright:
                def __init__(self, playwright):
                    self.playwright = playwright

                async def start(self):
                    return self.playwright

            fake_playwright = FakePlaywright()

            with patch.object(module, "async_playwright", lambda: FakeAsyncPlaywright(fake_playwright)):
                result = asyncio.run(bot.start_password_login())

            self.assertTrue(result["is_logged_in"])
            self.assertEqual(result["login_url"], "https://example.com/workbench")
            self.assertEqual(fake_playwright.browser.kwargs["storage_state"], str(storage_state_path))
            self.assertEqual(
                fake_playwright.browser.context.page.goto_calls,
                [("https://example.com/workbench", "domcontentloaded")],
            )

    def test_start_login_route_returns_manual_login_status(self):
        os.environ["PDD_CLIENT_ID"] = ""
        os.environ["PDD_CLIENT_SECRET"] = ""
        os.environ["PDD_ACCESS_TOKEN"] = ""
        os.environ["BROWSER_CONTROL_URL"] = "http://localhost:6080/vnc.html"

        route_module = load_module("routes.system_routes")

        class FakeBot:
            async def start_password_login(self):
                return {
                    "is_logged_in": False,
                    "status": "waiting_verification",
                    "verification_required": True,
                    "credentials_filled": True,
                    "message": "请在浏览器中完成滑块/短信等验证",
                    "login_url": "https://mms.pinduoduo.com/",
                }

        sys.modules["playwright_bot"] = types.SimpleNamespace(playwright_bot=FakeBot())
        try:
            result = asyncio.run(route_module.start_pdd_login())
        finally:
            sys.modules.pop("playwright_bot", None)

        self.assertTrue(result["success"])
        self.assertEqual(result["data"]["status"], "waiting_verification")
        self.assertEqual(result["data"]["auth_info_url"], "/api/v1/system/pdd-auth/page")
        self.assertEqual(result["data"]["browser_control_url"], "http://localhost:6080/vnc.html")

    def test_login_status_route_returns_logged_in_state_and_closes_browser(self):
        os.environ["PDD_CLIENT_ID"] = ""
        os.environ["PDD_CLIENT_SECRET"] = ""
        os.environ["PDD_ACCESS_TOKEN"] = ""

        route_module = load_module("routes.system_routes")

        class FakeBot:
            def __init__(self):
                self.page = object()
                self.closed = False

            async def check_login_status(self):
                return True

            async def continue_password_login(self):
                return None

            async def has_verification_challenge(self):
                return False

            def get_auth_info(self):
                return {"is_authorized": True, "status": "authorized", "message": "已授权"}

            async def close(self):
                self.closed = True
                self.page = None

        fake_bot = FakeBot()
        sys.modules["playwright_bot"] = types.SimpleNamespace(playwright_bot=fake_bot)
        try:
            result = asyncio.run(route_module.get_pdd_login_status())
        finally:
            sys.modules.pop("playwright_bot", None)

        self.assertTrue(result["success"])
        self.assertTrue(result["data"]["is_logged_in"])
        self.assertEqual(result["data"]["status"], "logged_in")
        self.assertTrue(fake_bot.closed)

    def test_login_status_route_does_not_trust_saved_auth_info(self):
        os.environ["PDD_CLIENT_ID"] = ""
        os.environ["PDD_CLIENT_SECRET"] = ""
        os.environ["PDD_ACCESS_TOKEN"] = ""

        route_module = load_module("routes.system_routes")

        class FakeBot:
            page = None
            password_login_filled = False

            async def check_login_status(self):
                return False

            async def continue_password_login(self):
                return None

            def get_auth_info(self):
                return {"is_authorized": True, "status": "authorized", "message": "已授权"}

        sys.modules["playwright_bot"] = types.SimpleNamespace(playwright_bot=FakeBot())
        try:
            result = asyncio.run(route_module.get_pdd_login_status())
        finally:
            sys.modules.pop("playwright_bot", None)

        self.assertTrue(result["success"])
        self.assertFalse(result["data"]["is_logged_in"])
        self.assertEqual(result["data"]["status"], "waiting_login")

    def test_get_auth_info_reads_saved_session_without_cookie_values(self):
        os.environ["PDD_CLIENT_ID"] = ""
        os.environ["PDD_CLIENT_SECRET"] = ""
        os.environ["PDD_ACCESS_TOKEN"] = ""

        with tempfile.TemporaryDirectory() as tmp_dir:
            os.environ["PDD_DATA_DIR"] = tmp_dir
            module = load_module("playwright_bot")
            bot = module.PlaywrightBot()
            secret_value = "secret-cookie-value"
            bot.storage_state_path.write_text(
                json.dumps({
                    "cookies": [
                        {
                            "name": "PASS_ID",
                            "value": secret_value,
                            "domain": ".pinduoduo.com",
                            "path": "/",
                            "expires": 1893456000,
                        }
                    ],
                    "origins": [],
                }),
                encoding="utf-8",
            )

            info = bot.get_auth_info()

        self.assertTrue(info["is_authorized"])
        self.assertEqual(info["status"], "authorized")
        self.assertEqual(info["cookie_names"], ["PASS_ID"])
        self.assertNotIn(secret_value, str(info))

    def test_get_auth_info_rejects_expired_auth_cookie(self):
        os.environ["PDD_CLIENT_ID"] = ""
        os.environ["PDD_CLIENT_SECRET"] = ""
        os.environ["PDD_ACCESS_TOKEN"] = ""

        with tempfile.TemporaryDirectory() as tmp_dir:
            os.environ["PDD_DATA_DIR"] = tmp_dir
            module = load_module("playwright_bot")
            bot = module.PlaywrightBot()
            bot.storage_state_path.write_text(
                json.dumps({
                    "cookies": [
                        {
                            "name": "PASS_ID",
                            "value": "expired",
                            "domain": ".pinduoduo.com",
                            "path": "/",
                            "expires": 1,
                        }
                    ],
                    "origins": [],
                }),
                encoding="utf-8",
            )

            info = bot.get_auth_info()

        self.assertFalse(info["is_authorized"])
        self.assertEqual(info["status"], "invalid")
        self.assertEqual(info["expired_auth_cookie_names"], ["PASS_ID"])

    def test_close_clears_browser_state_even_if_one_resource_fails(self):
        os.environ["PDD_CLIENT_ID"] = ""
        os.environ["PDD_CLIENT_SECRET"] = ""
        os.environ["PDD_ACCESS_TOKEN"] = ""

        module = load_module("playwright_bot")
        bot = module.PlaywrightBot()

        class FakePage:
            async def close(self):
                return None

        class FakeContext:
            async def close(self):
                raise RuntimeError("context already closed")

        class FakeBrowser:
            async def close(self):
                return None

        class FakePlaywright:
            async def stop(self):
                return None

        bot.page = FakePage()
        bot.context = FakeContext()
        bot.browser = FakeBrowser()
        bot.playwright = FakePlaywright()
        bot.is_logged_in = True

        asyncio.run(bot.close())

        self.assertIsNone(bot.page)
        self.assertIsNone(bot.context)
        self.assertIsNone(bot.browser)
        self.assertIsNone(bot.playwright)
        self.assertFalse(bot.is_logged_in)

    def test_check_login_status_stays_false_on_login_page_text(self):
        os.environ["PDD_CLIENT_ID"] = ""
        os.environ["PDD_CLIENT_SECRET"] = ""
        os.environ["PDD_ACCESS_TOKEN"] = ""

        module = load_module("playwright_bot")
        bot = module.PlaywrightBot()

        class FakeLocator:
            def __init__(self, count):
                self._count = count

            async def count(self):
                return self._count

        class FakePage:
            url = "https://mms.pinduoduo.com/"

            def is_closed(self):
                return False

            def locator(self, selector):
                counts = {
                    ".user-avatar": 0,
                    '[data-testid=\"user-avatar\"]': 0,
                    "text=店铺概况": 0,
                    "text=消息中心": 0,
                    "text=多多客服": 0,
                    "text=账号登录": 1,
                    "text=验证码登录": 1,
                    "text=扫码登录": 1,
                    "text=店铺": 1,
                }
                return FakeLocator(counts.get(selector, 0))

        bot.page = FakePage()

        with tempfile.TemporaryDirectory() as tmp_dir:
            bot.data_dir = Path(tmp_dir)
            logged_in = asyncio.run(bot.check_login_status())

        self.assertFalse(logged_in)
        self.assertFalse(bot.is_logged_in)


if __name__ == "__main__":
    unittest.main()
