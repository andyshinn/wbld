import asyncio
import os

from discord import Intents
from discord.errors import PrivilegedIntentsRequired
from discord.ext import commands

from wbld.cogs.health import Health
from wbld.cogs.pio import Pio
from wbld.cogs.wbld import WbldCog
from wbld.log import logger

BASE_URL = os.getenv("BASE_URL", "https://wbld.app")
TOKEN = os.getenv("DISCORD_TOKEN")
PING_URL = os.getenv("PING_URL")
PREFIXES = [os.getenv("DISCORD_PREFIX", "./")]
DEFAULT_BRANCH = os.getenv("DEFAULT_BRANCH", "main")
OWNER_ID = os.getenv("OWNER_ID", 206914075391688704)


class Bot(commands.Bot):
    def __init__(self, **kwargs):
        intents = Intents.default()
        intents.message_content = True
        intents.messages = True
        intents.reactions = True
        intents.dm_messages = True
        intents.members = False  # Do we need this?
        super(Bot, self).__init__(**kwargs, intents=intents, help_command=commands.DefaultHelpCommand())

    async def on_ready(self):
        logger.info("{} has connected to Discord!", self.user)

        async def register_cog(cog, *args, **kwargs):
            logger.info("Registering cog: {}", cog.__name__, args, kwargs)
            await self.add_cog(cog(self, *args, **kwargs))

        if PING_URL:
            await register_cog(Health, PING_URL)

        await register_cog(Pio)

        await register_cog(WbldCog, BASE_URL, DEFAULT_BRANCH)
        await logger.complete()


bot = Bot(
    command_prefix=PREFIXES,
    case_insensitive=True,
    description="A WLED firmware Discord bot.",
    shard_id=0,
    owner_id=OWNER_ID,
)


async def main():
    try:
        if TOKEN:
            if PING_URL:
                await bot.add_cog(Health(bot, PING_URL))
            await bot.add_cog(WbldCog(bot, BASE_URL, DEFAULT_BRANCH))
            await bot.start(TOKEN)
        else:
            logger.error("Please set your DISCORD_TOKEN.")
    except PrivilegedIntentsRequired as e:
        logger.error("Please enable the privileged intents. Error: {}", e)
    except Exception as e:
        logger.exception("Error: {}", e)
    finally:
        await bot.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        asyncio.run(bot.close())
