from Core.accounts.context import AccountContext
from Core.utils.utils import Utils
from Core.discord.utils import DiscordUtils
from Core.discord.headers import HeaderBuilder
from Core.NexusColors.color import NexusColor

class AccountContextFactory:
    def __init__(self, session, proxy, logger, mail_api):
        self.session = session
        self.proxy = proxy
        self.logger = logger
        self.mail_api = mail_api

    def create(self) -> AccountContext:
        dcfduid, sdcfduid = DiscordUtils.fetch_cookies(self.session)
        fingerprint = DiscordUtils.get_fingerprint(
            dcfduid, sdcfduid, self.session
        )

        username = Utils.random_string()
        self.logger.log(f"Got Username -> {NexusColor.PURPLE}{username}")
        password = Utils.random_password()
        self.logger.log(f"Got Password -> {NexusColor.PURPLE}{password}")
        email = self.mail_api.create_account(username, password)
        self.logger.log(f"Got Mail -> {NexusColor.PURPLE}{email}")
        birthday = Utils.random_birthday()
        y, m, d = birthday
        self.logger.log(f"Got Birthday -> {NexusColor.PURPLE}{f'{y}-{m:02d}-{d:02d}'}")
        

        headers = HeaderBuilder(self.session).build(fp=fingerprint)
        self.session.headers.update(headers)

        return AccountContext(
            fingerprint=fingerprint,
            username=username,
            password=password,
            email=email,
            birthday=birthday,
            proxy=self.proxy
        )
