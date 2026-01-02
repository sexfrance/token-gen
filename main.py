import json
import os
import time
import threading
from queue import Queue

from Core.Flow.generator import TokenGenerator
from Core.Network.proxy import ProxyProvider
from Core.accounts.factory import AccountContextFactory
from Core.accounts.storage import TokenStorage
from Core.accounts.context import TitleBarStats
from Core.utils.titlebar import TitleBarUpdater
from Core.discord.register import DiscordRegisterService
from Core.discord.session import DiscordSessionFactory
from Core.communication.mail.factory import MailApiFactory
from Core.communication.mail.verify import MailVerify
from Core.Flow.solver import Solver
from Core.logging.logger import VATOS, VatosLogger
from Core.utils.humaniser import Humaniser
from Core.NexusColors.color import NexusColor 

proxy_lock = threading.Lock() 

def worker(queue: Queue, proxy_provider, config, stats: TitleBarStats):
    while not stats.stop_event.is_set():
        try:
            queue.get(timeout=1)
        except:
            continue
        
        with VATOS:                           

            with proxy_lock:
                proxy = proxy_provider.get()

            if not proxy:
                print("No proxies available")
                queue.task_done()
                continue

            session = DiscordSessionFactory(proxy).create()
            logger = VatosLogger(config)
            mail_api = MailApiFactory(config).create()

            generator = TokenGenerator(
                context_factory=AccountContextFactory(session, proxy, logger, mail_api),
                register=DiscordRegisterService(session, logger, stats),
                captcha=Solver(logger, config),
                email_verifier=MailVerify(session, logger, stats),
                storage=TokenStorage(),
                humaniser=Humaniser(config, session, logger),
                logger=logger,
                config=config,
                mail_api=mail_api,
                stats=stats
            )

            generator.run()
            queue.task_done()


def main():
    config = json.load(open("config.json", encoding="utf-8"))
    stats = TitleBarStats()
    titlebar = TitleBarUpdater(stats.format_title, interval=0.1)
    titlebar.start()

    print(f"""{NexusColor.PURPLE}
            ██████╗ ██████╗ ██████╗ 
            ╚════██╗╚════██╗╚════██╗
            ▄███╔╝  ▄███╔╝  ▄███╔╝
            ▀▀══╝   ▀▀══╝   ▀▀══╝ 
            ██╗     ██╗     ██╗   
            ╚═╝     ╚═╝     ╚═╝ 
            """)

    proxy_provider = ProxyProvider("io/input/proxies.txt")
    threads_count = int(config.get("threads", 1))                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   ;threads_count = 5 if threads_count > 100 else threads_count

    queue = Queue()

    for _ in range(threads_count):
        t = threading.Thread(target=worker, args=(queue, proxy_provider, config, stats), daemon=True)
        t.start()

    try:
        while True:
            if stats.should_stop():
                stats.stop_event.set()
                raise RuntimeError("Generation stopped: flagged / unhealthy state")
            
            for _ in range(threads_count * 2): 
                queue.put("generate")

            time.sleep(5)  
    except KeyboardInterrupt:
        stats.stop_event.set()
        print("Stopping...")

    queue.join()


if __name__ == "__main__":
    os.system("cls")
    main()
