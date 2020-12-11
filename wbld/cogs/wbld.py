from configparser import MissingSectionHeaderError, ParsingError

from discord import File, Embed
from discord.ext import commands

from wbld.build import Builder, BuilderCustom, CustomConfigException
from wbld.log import logger
from wbld.repository import Reference, ReferenceException, Clone


class WbldCog(commands.Cog, name="Builder"):
    """
    Commands to build and work with WLED firmware.
    """

    def __init__(self, bot):
        self.bot = bot

    async def _build_firmware(self, ctx, version, env_or_snippet, builder, clone=None):
        try:
            if not clone:
                clone = Clone(version)
                clone.clone_version()

            with builder(clone.path, env_or_snippet) as build:
                await ctx.send(f"Attempting to build environment `{build.env}`. This may take a couple minutes...")
                run = await self.bot.loop.run_in_executor(None, build.run)
                build_file = open(build.firmware_filename, "rb")
                logger.debug(f"Firmware file: {build_file}")
                if build_file:
                    file = File(build_file, filename=f"wled_{build.env}_{version}.bin")
                    await ctx.send(file=file, content=f"Looks like everything built correctly for {build.env}")
                else:
                    await ctx.send("There was a problem building the firmware.")
                    logger.error(f"Error building firmware for `{build.env}` against `{version}`.")
        except ReferenceException as error:
            await ctx.send(f"{error}: {version}")
        except (
            CustomConfigException,
            MissingSectionHeaderError,
            ParsingError,
        ) as error:
            await ctx.send(
                content=f"Config Errror:\n\n{error}\n\nCheck your configuration and see help using: `{ctx.prefix}help`"
            )

    @staticmethod
    async def _get_reference(ctx, version):
        try:
            reference = Reference(version)
        except ReferenceException:
            await ctx.send(f"Couldn't find commit, branch, or SHA for: `{version}`")
        else:
            return reference

    @staticmethod
    async def _send_ready(ctx, reference):
        logger.debug(ctx)
        logger.debug(reference)
        await logger.complete()
        embed = Embed(
            title=reference.commit.sha,
            url=reference.commit.commit.html_url,
            description=reference.commit.commit.message,
            color=0x034EFC,
        )
        embed.set_author(
            name=reference.repository.full_name,
            url=reference.repository.html_url,
            icon_url=reference.repository.owner.avatar_url,
        )
        await ctx.send(
            content="OK. Ready to build. Please paste your custom PlatformIO environment config.",
            embed=embed,
        )

    @commands.Cog.listener()
    async def on_command_error(self, ctx, exception):
        if isinstance(
            exception,
            (
                commands.errors.CommandNotFound,
                commands.errors.MissingRequiredArgument,
                commands.errors.MaxConcurrencyReached,
            ),
        ):
            await ctx.send(f"{exception}")
        if isinstance(exception, commands.errors.CommandInvokeError):
            await ctx.send(f"Something went wrong: {exception}")
        raise exception

    @commands.Cog.listener()
    async def on_command(self, ctx):
        logger.debug(f"Command {ctx.command.qualified_name} called by {str(ctx.author)}")
        await logger.complete()

    @commands.group(description="Firmware building commands.")
    async def build(self, ctx):
        if ctx.invoked_subcommand is None:
            subcommands = ", ".join([f"`{c.name}`" for c in ctx.command.commands])
            await ctx.send(f"Invalid `{ctx.command.name}` command passed. Availabe subcommands: {subcommands}")

    @commands.max_concurrency(1, per=commands.BucketType.user)
    @build.command()
    async def builtin(self, ctx, env, version="master"):
        await self._build_firmware(ctx, version, env, Builder)

    @commands.max_concurrency(1, per=commands.BucketType.user)
    @build.command()
    async def custom(self, ctx, version="master"):
        def check_author(author, channel):
            def inner_check(message):
                return message.author == author and message.channel == channel

            return inner_check

        # reference = await WbldCog._get_reference(ctx, version)

        # if reference:
        #     await WbldCog._send_ready(ctx, reference)
        try:
            clone = Clone(version)
            commit = clone.clone_version()
        except Exception as error:
            raise error
        else:
            await ctx.send(
                f"Ready to build `{version}` (`{commit.hexsha}`). Paste your custom PlatformIO environment config."
            )
            try:
                msg = await self.bot.wait_for("message", check=check_author(ctx.author, ctx.channel), timeout=30)
            except TimeoutError:
                await ctx.send("Didn't receive configuraton within 30 seconds. Try again!")
            else:
                await self._build_firmware(ctx, version, msg.content, BuilderCustom, clone=clone)
