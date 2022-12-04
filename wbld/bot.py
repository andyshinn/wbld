import os

from discord import Intents
from discord.ext import commands

from wbld.cogs.health import Health
from wbld.cogs.wbld import WbldCog
from wbld.log import logger

BASE_URL = os.getenv("BASE_URL", "https://wbld.app")
TOKEN = os.getenv("DISCORD_TOKEN")
PING_URL = os.getenv("PING_URL")
PREFIXES = [os.getenv("DISCORD_PREFIX", "./")]
DEFAULT_BRANCH = os.getenv("DEFAULT_BRANCH", "main")


class Bot(commands.Bot):
    def __init__(self, **kwargs):
        intents = Intents.default()
        intents.message_content = True
        intents.members = True
        super(Bot, self).__init__(**kwargs, intents=intents)

    async def on_ready(self):
        logger.info("{} has connected to Discord!", self.user)

        async def register_cog(cog, *args, **kwargs):
            logger.info("Registering cog: {}", cog.__name__, args, kwargs)
            await self.add_cog(cog(self, *args, **kwargs))

        if PING_URL:
            await register_cog(Health, PING_URL)

        await register_cog(WbldCog, BASE_URL, DEFAULT_BRANCH)
        await logger.complete()


bot = Bot(
    command_prefix=PREFIXES,
    case_insensitive=True,
    description="A WLED firmware Discord bot.",
    shard_id=0,
    owner_id=206914075391688704,
)


if __name__ == "__main__":
    if TOKEN:
        bot.run(TOKEN)
    else:
        logger.error("Please set your DISCORD_TOKEN.")
