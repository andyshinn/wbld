from configparser import MissingSectionHeaderError, ParsingError

from discord import File, Embed
from discord.ext import commands

from wbld.build import Builder, BuilderCustom, CustomConfigException, Build
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
                await ctx.send(
                    f"Building environment `{build.env}` as UUID `{build.uuid}`. This will take a couple minutes..."
                )
                finished_build = await self.bot.loop.run_in_executor(None, build.run)
                build_file = finished_build.firmware
                logger.debug(f"Firmware file: {build_file}")
                if build_file:
                    file = File(build_file, filename=f"wled_{build.env}_{version}_{build.uuid}.bin")
                    await ctx.send(file=file, content=f"Build `{build.uuid}` completed for `{build.env}`.")
                else:
                    await ctx.send(
                        f"There was a problem building the firmware. See logs with `{ctx.prefix}build log <uuid>`"
                    )
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
        """
        See help for builtin firmware:

          ./help build builtin

        See help for custom firmware:

          ./help build custom

        """
        if ctx.invoked_subcommand is None:
            subcommands = ", ".join([f"`{c.name}`" for c in ctx.command.commands])
            await ctx.send(f"Invalid `{ctx.command.name}` command passed. Available subcommands: {subcommands}")

    @commands.max_concurrency(1, per=commands.BucketType.user)
    @build.command()
    async def builtin(self, ctx, env, version="master"):
        """
        Builds and returns a firmware file for an environment which already exists in the WLED PlatformIO configuration.

        Example:

          ./build builtin d1_mini
        """
        await self._build_firmware(ctx, version, env, Builder)

    @commands.max_concurrency(1, per=commands.BucketType.user)
    @build.command()
    async def custom(self, ctx, version="master"):
        """
        Builds and returns firmware for a custom configuration snippet that you provide.

        Example custom build for version 0.11.2:

          ./build custom v0.11.1

        The bot will then ask for a configuration snippet. Example for custom APA102 ESP32 build:

          [env:apaesp32]
          board = esp32dev
          platform = espressif32@2.1.0
          build_unflags = ${common.build_unflags}
          build_flags = ${common.build_flags_esp32} -D USE_APA102 -D CLKPIN=2 -D DATAPIN=3
          lib_ignore =
            ESPAsyncTCP
            ESPAsyncUDP
        """

        def check_author(author, channel):
            def inner_check(message):
                return message.author == author and message.channel == channel

            return inner_check

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

    @build.command()
    async def log(self, ctx, uuid):
        """
        Returns the log file containing stdout and stderr of the PlatformIO build.
        """

        try:
            build = Build(uuid)
        except FileNotFoundError:
            await ctx.send(
                # pylint: disable=line-too-long
                f"Couldn't find UUID: `{uuid}`. It either doesn't exist, has already been cleaned up, or had an error before we could write logs."
            )
        else:
            file_send = File(build.log, filename=f"wled_build_{uuid}.log")
            await ctx.send(file=file_send, content=f"Log file for build UUID: `{uuid}`")
