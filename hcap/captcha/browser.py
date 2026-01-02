import re
from camoufox.async_api import AsyncCamoufox

class BrowserFactory:
    @staticmethod
    async def create_browser():
        cfg = {
            "headless": True,
            "humanize": False,
            "geoip": True,
            "os": ["macos", "linux"],
        }
        return await AsyncCamoufox(**cfg).start()

    @staticmethod
    async def create_context(browser, proxy=None):
        ctx_cfg = {"locale": "nl"}

        if proxy:
            user, password, server = re.match(r'(.*?):(.*?)@(.*)', proxy).groups()
            ctx_cfg["proxy"] = {
                "server": f"http://{server}",
                "username": user,
                "password": password,
            }

        context = await browser.new_context(**ctx_cfg)
        page = await context.new_page()
        return context, page


class BrowserManager:
    def __init__(self):
        self.browser = None

    async def reset_browser(self):
        if self.browser:
            try:
                await self.browser.close()
            except Exception:
                pass
            self.browser = None

    async def create_context(self, proxy=None):
        if not self.browser:
            self.browser = await BrowserFactory.create_browser()
        context, page = await BrowserFactory.create_context(self.browser, proxy)
        return context, page
