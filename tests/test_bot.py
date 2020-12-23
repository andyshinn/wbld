import pytest

from wbld.bot import Bot
from wbld.cogs.health import Health


def test_clone_init():
    bot = Bot(command_prefix="fake_prefix")

    assert isinstance(bot, Bot)
    assert bot.command_prefix == "fake_prefix"


def test_cogs():
    bot = Bot(command_prefix="cog_prefix")
    bot.add_cog(Health(bot, ping_url="https://fake.com"))

    assert "Health" in bot.cogs

    health = bot.cogs["Health"]

    assert health.healthcheck.minutes == 15.0


def test_health_requires_ping():
    bot = Bot(command_prefix="ping_prefix")

    with pytest.raises(TypeError):
        Health(bot)
