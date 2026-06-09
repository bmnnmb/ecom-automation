import asyncio
import importlib
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


class QrLoginTests(unittest.TestCase):
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

    def test_start_qr_login_uses_saved_storage_state_and_captures_screenshot(self):
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
                    self.goto_calls = []
                    self.screenshot_calls = []

                async def goto(self, url, wait_until=None):
                    self.goto_calls.append((url, wait_until))

                async def screenshot(self, path=None, full_page=None):
                    self.screenshot_calls.append((path, full_page))
                    Path(path).write_bytes(b"png")

            class FakeContext:
                def __init__(self):
                    self.page = FakePage()

                async def new_page(self):
                    return self.page

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
                result_path = asyncio.run(bot.start_qr_login())

            self.assertEqual(result_path, str(Path(tmp_dir) / "pdd_login.png"))
            self.assertEqual(fake_playwright.browser.kwargs["storage_state"], str(storage_state_path))
            self.assertEqual(
                fake_playwright.browser.context.page.goto_calls,
                [("https://example.com/workbench", "networkidle")],
            )
            self.assertEqual(
                fake_playwright.browser.context.page.screenshot_calls,
                [(str(Path(tmp_dir) / "pdd_login.png"), True)],
            )

    def test_start_login_route_returns_screenshot_url(self):
        os.environ["PDD_CLIENT_ID"] = ""
        os.environ["PDD_CLIENT_SECRET"] = ""
        os.environ["PDD_ACCESS_TOKEN"] = ""

        route_module = load_module("routes.system_routes")

        class FakeBot:
            async def start_qr_login(self):
                return "/tmp/pdd_login.png"

        sys.modules["playwright_bot"] = types.SimpleNamespace(playwright_bot=FakeBot())
        try:
            result = asyncio.run(route_module.start_pdd_login())
        finally:
            sys.modules.pop("playwright_bot", None)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["screenshot_url"], "/api/v1/system/pdd-login/screenshot")

    def test_login_status_route_returns_logged_in_state(self):
        os.environ["PDD_CLIENT_ID"] = ""
        os.environ["PDD_CLIENT_SECRET"] = ""
        os.environ["PDD_ACCESS_TOKEN"] = ""

        route_module = load_module("routes.system_routes")

        class FakeBot:
            async def check_login_status(self):
                return True

        sys.modules["playwright_bot"] = types.SimpleNamespace(playwright_bot=FakeBot())
        try:
            result = asyncio.run(route_module.get_pdd_login_status())
        finally:
            sys.modules.pop("playwright_bot", None)

        self.assertTrue(result["logged_in"])
        self.assertEqual(result["message"], "已登录")

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

            def __init__(self):
                self.screenshot_calls = []

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

            async def screenshot(self, path=None, full_page=None):
                self.screenshot_calls.append((path, full_page))
                Path(path).write_bytes(b"png")

        bot.page = FakePage()

        with tempfile.TemporaryDirectory() as tmp_dir:
            bot.data_dir = Path(tmp_dir)
            bot.login_screenshot_path = bot.data_dir / "pdd_login.png"
            logged_in = asyncio.run(bot.check_login_status())

        self.assertFalse(logged_in)
        self.assertFalse(bot.is_logged_in)


if __name__ == "__main__":
    unittest.main()
