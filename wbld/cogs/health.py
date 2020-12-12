from aiohttp import ClientSession, ClientError
from discord.ext import tasks, commands

from wbld.log import logger


class Health(commands.Cog):
    def __init__(self, bot, ping_url):
        self.bot = bot
        self.ping_url = ping_url
        self.healthcheck.start()  # pylint: disable=no-member

    def cog_unload(self):
        self.healthcheck.cancel()  # pylint: disable=no-member

    @tasks.loop(minutes=15.0)
    async def healthcheck(self):
        try:
            async with ClientSession(raise_for_status=True) as session:
                await session.get(self.ping_url)
        except ClientError as error:
            logger.error(f"Health check error: {error}")
        else:
            logger.debug(f"Submitted healthcheck ping to: {self.ping_url}")

        logger.complete()

    @healthcheck.before_loop
    async def before_healthcheck(self):
        await self.bot.wait_until_ready()
