import asyncio
import time
import json

from ..captcha.browser import BrowserManager
from ..web.templates import TemplateCache
from ..captcha.ai import AIAssistant
from .frame_utils import FrameUtils

class HCaptchaSolver:
    def __init__(self, store):
        self.store = store
        self.templates = TemplateCache()

        self.config = json.load(open("config.json", encoding="utf-8"))
        self.api_key = self.config["solver"]["ai_api_key"]
        if not self.api_key:
            raise RuntimeError("No AI API Key")

        self.ai = AIAssistant(self.api_key)
        self.browser_manager = BrowserManager()

    async def _monitor_token(self, page, context, taskid):
        while True:
            if page.is_closed():
                return
            try:
                token = await page.evaluate("""
                    () => document.querySelector(
                        'iframe[data-hcaptcha-response]'
                    )?.getAttribute('data-hcaptcha-response')
                """)
                if token and "_" in token:
                    cookies = await context.cookies()
                    self.store.set_result(
                        taskid,
                        "success",
                        token,
                        {c["name"]: c["value"] for c in cookies},
                    )
                    await context.close()
                    return
            except Exception:
                return
            await asyncio.sleep(0.25)

    async def solve(self, taskid, url, sitekey, rqdata, proxy):
        start = time.time()
        context = None

        try:
            context, page = await self.browser_manager.create_context(proxy)

            async def route_main(route):
                await route.fulfill(
                    body=self.templates.render_main(sitekey),
                    content_type="text/html",
                )

            async def route_hcaptcha(route):
                await route.fulfill(
                    body=self.templates.render_hcaptcha(rqdata),
                    content_type="text/html",
                )

            async def route_api(route):
                await route.fulfill(
                    body=self.templates.api_js,
                    content_type="application/javascript",
                )

            await page.route(url, route_main)
            await page.route("**/static/hcaptcha.html", route_hcaptcha)
            await page.route("**/assets/api.js**", route_api)

            await page.goto(url, wait_until="commit")
            await page.wait_for_selector("iframe")

            token_task = asyncio.create_task(
                self._monitor_token(page, context, taskid)
            )

            if not await FrameUtils.click_checkbox(page):
                raise RuntimeError("Checkbox iframe not found")

            frame = await FrameUtils.find_challenge_frame(page)
            if not frame:
                raise RuntimeError("Challenge iframe not found")
            await FrameUtils.solve_accessibility(frame, self.ai)

            await asyncio.wait_for(token_task, timeout=120)

        except asyncio.TimeoutError:
            self.store.set_result(taskid, "error")
            if context:
                await context.close()
        except Exception as e:
            print("Solve error:", e)
            self.store.set_result(taskid, "error")
            if context:
                await context.close()

        return time.time() - start
