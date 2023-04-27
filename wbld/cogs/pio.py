from discord.ext import commands

from wbld.pio import PioCommand


class Pio(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pio = PioCommand()

    @commands.group(description="PlatformIO commands.")
    async def pio(self, ctx: commands.Context):
        """
        PlatformIO debug commands.

          ./pio
        """
        if ctx.invoked_subcommand is None:
            subcommands = ", ".join([f"`{c.name}`" for c in ctx.command.commands])
            await ctx.send(f"Invalid `{ctx.command.name}` command passed. Available subcommands: {subcommands}")

    @pio.group(description="PlatformIO package commands.")
    async def pkg(self, ctx: commands.Context):
        """
        PlatformIO package commands.

          ./pio pkg
        """
        if ctx.invoked_subcommand is None:
            subcommands = ", ".join([f"`{c.name}`" for c in ctx.command.commands])
            await ctx.send(f"Invalid `{ctx.command.name}` command passed. Available subcommands: {subcommands}")

    @pkg.command(description="List globally installed packages.")
    async def list(self, ctx: commands.Context, env: str = None):
        """
        List globally installed packages.

            ./pio pkg list
        """
        global_package_list = self.pio.package.list("--global")

        await ctx.send(f"```\n{global_package_list}\n```")

    @pio.group(description="PlatformIO system commands.")
    async def system(self, ctx: commands.Context):
        """
        PlatformIO system commands.

        System info:

            ./pio system info

        System prune:

            ./pio system prune
        """
        if ctx.invoked_subcommand is None:
            subcommands = ", ".join([f"`{c.name}`" for c in ctx.command.commands])
            await ctx.send(f"Invalid `{ctx.command.name}` command passed. Available subcommands: {subcommands}")

    @system.command(description="Info about PlatformIO system.")
    async def info(self, ctx: commands.Context):
        """
        Info about PlatformIO system.

            ./pio system info
        """

        system_info = self.pio.system.info()

        await ctx.send(f"```\n{system_info}\n```")

    @system.command(description="Prune PlatformIO system.")
    @commands.is_owner()
    async def prune(self, ctx: commands.Context):
        """
        Prune PlatformIO system.

            ./pio system prune
        """

        system_prune = self.pio.system.prune(f=True)

        await ctx.send(f"```\n{system_prune}\n```")
