from discord.ext import commands

class Utils(commands.Cog):
    @commands.command(name='clear')
    async def clear(self, ctx: commands.Context, number: int = 15):
        await ctx.send('Deleting {} messages...'.format(number))
        await ctx.channel.delete_messages(await ctx.history(limit=number+2).flatten())