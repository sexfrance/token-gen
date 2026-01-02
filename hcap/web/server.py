import asyncio
import threading
import random
import string

from flask import Flask, request
from ..captcha.solver import HCaptchaSolver
from ..captcha.browser import BrowserManager
from ..captcha.storage import TaskStore


class APIServer:
    def __init__(self):
        self.app = Flask(__name__)
        self.store = TaskStore()
        self.solver = HCaptchaSolver(self.store)
        self.manager = BrowserManager()

        self.loop = asyncio.new_event_loop()
        threading.Thread(target=self.loop.run_forever, daemon=True).start()

        self.solve_count = 0
        self.max_solves_per_browser = 25
        self.browser_lock = asyncio.Lock()

        self._routes()

    def _routes(self):
        @self.app.route("/solve")
        def solve():
            taskid = "".join(
                random.choices(string.ascii_lowercase + string.digits, k=5)
            )
            self.store.create(taskid)

            asyncio.run_coroutine_threadsafe(
                self._solve_wrapper(
                    taskid=taskid,
                    url=request.args["url"],
                    sitekey=request.args["sitekey"],
                    rqdata=request.args.get("rqdata"),
                    proxy=request.args.get("proxy"),
                ),
                self.loop,
            )

            return {"taskid": taskid}

        @self.app.route("/task/<taskid>")
        def task(taskid):
            return self.store.get(taskid)

    async def _solve_wrapper(self, **kwargs):
        async with self.browser_lock:
            self.solve_count += 1

            if self.solve_count >= self.max_solves_per_browser:
                print("[*] Rotating browser")
                await self.manager.reset_browser()
                self.solve_count = 0

        await self.solver.solve(**kwargs)

    def run(self):
        self.app.run(
            "0.0.0.0",
            5001,
            debug=False,
            use_reloader=False,
            threaded=True,
        )
