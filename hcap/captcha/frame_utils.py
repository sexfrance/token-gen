import asyncio
import time

class FrameUtils:
    @staticmethod
    async def find_frame(page, selector_checker, timeout=30):
        start = time.time()
        while time.time() - start < timeout:
            for iframe in await page.query_selector_all("iframe"):
                src = await iframe.get_attribute("src")
                if not src or "hcaptcha.com" not in src:
                    continue
                frame = await iframe.content_frame()
                if not frame:
                    continue
                if await selector_checker(frame):
                    return frame
            await asyncio.sleep(0.2)
        return None

    @staticmethod
    async def click_checkbox(page):
        async def checker(frame):
            return await frame.evaluate(
                "() => !!document.querySelector('div#checkbox')"
            )

        frame = await FrameUtils.find_frame(page, checker)
        if not frame:
            return False

        await frame.evaluate("""
            const cb = document.querySelector('div#checkbox');
            if (cb && cb.getAttribute('aria-checked') === 'false') {
                cb.click();
            }
        """)
        return True

    @staticmethod
    async def find_challenge_frame(page):
        async def checker(frame):
            return await frame.evaluate(
                "() => !!document.querySelector('#menu-info')"
            )

        return await FrameUtils.find_frame(page, checker)

    @staticmethod
    async def solve_accessibility(frame, ai):
        await frame.wait_for_selector("#menu-info", timeout=20_000)
        await frame.locator("#menu-info").click()
        await asyncio.sleep(0.3)
        try:
            await frame.locator("#text_challenge").click()
        except Exception:
            pass

        last_question = None
        start_time = time.time()

        while True:
            if frame.is_detached():
                break

            try:
                question_el = await frame.query_selector('[id^="prompt-text"]')
                if not question_el:
                    await asyncio.sleep(0.2)
                    continue

                question = (await question_el.inner_text()).strip()
                if not question or question == last_question:
                    await asyncio.sleep(0.2)
                    continue

                last_question = question
                answer = await ai.answer(question)

                input_el = await frame.query_selector("div.challenge-input input")
                if input_el:
                    await input_el.fill(answer)
                    await asyncio.sleep(0.2)

                submit = await frame.query_selector(".button-submit")
                if submit:
                    await submit.click()
            except Exception:
                break

        return time.time() - start_time
