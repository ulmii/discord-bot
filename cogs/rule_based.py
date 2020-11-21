from discord.ext import commands
from cogs.rulebased import test
from enum import Enum

class Rules(commands.Cog):   
    @commands.command(name='rule')
    async def test(self, ctx: commands.Context):
        test()

    class RuleTypes(Enum):
        LEVENSHTEIN = 'levenshtein'
        FULL_TXT_SEARCH = 'full_text_search'