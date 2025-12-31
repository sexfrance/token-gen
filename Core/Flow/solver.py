import time
import requests

from Core.NexusColors.color import NexusColor

class Solver:
    
    def __init__(self, logger, config):
        self.logger = logger
        self.config = config
        
    def start_solve(self, rqdata: str, proxy: str) -> str:
        params = {
            "url": "https://discord.com/register",
            "sitekey": "a9b5fb07-92ff-493f-86fe-352a2803b3df",
            "rqdata": rqdata,
            "proxy": proxy,
        }

        r = requests.get(
            "http://127.0.0.1:5001/solve",
            params=params,
            timeout=10,
        )
        r.raise_for_status()
        return r.json()["taskid"]

    def wait_for_result(self, taskid: str, timeout: int = 100):
        if self.config["captcha_timeout"]:
            timeout = self.config["captcha_timeout"]
            
        start = time.time()

        while True:
            r = requests.get(
                f"http://127.0.0.1:5001/task/{taskid}",
                timeout=10,
            )
            r.raise_for_status()
            data = r.json()

            status = data.get("status")

            if status == "success":
                elapsed = time.time() - start
                uuid_str = data["uuid"][:64]
                self.logger.log(f"Captcha Solved in {NexusColor.PURPLE}{elapsed:.1f}s {NexusColor.LIGHTBLACK}({NexusColor.PURPLE}{uuid_str}{NexusColor.LIGHTBLACK})")
                return data
            
            if status == "error":
                raise RuntimeError("Captcha solve failed")

            if time.time() - start > timeout:
                 raise TimeoutError("Captcha solve timed out")

            time.sleep(1)

    def solve(self, ctx):
        if not hasattr(ctx, "captcha_rqdata"):
            raise ValueError("Context missing captcha_rqdata")

        self.logger.log("Solving Captcha...")

        task_id = self.start_solve(
            rqdata=ctx.captcha_rqdata,
            proxy=ctx.proxy,
        )

        result = self.wait_for_result(task_id)
        if result:
            ctx.captcha_key = result["uuid"]
