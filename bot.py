from cogs.utils import Utils
from cogs.music import Music
from cogs.rule_based import Rules

from discord.ext import commands

from dotenv import load_dotenv
import os

# Credentials
load_dotenv('.env')

# discord api TOKEN
TOKEN = os.getenv('DISCORD_TOKEN')

class MyBot(commands.Bot):
    async def on_ready(self):
        print('Logged in as {0} ({0.id})'.format(bot.user))
        print('------')
    
bot = MyBot(command_prefix=commands.when_mentioned_or("!"),
                   description='Python Music Bot');

bot.add_cog(Music(bot))
bot.add_cog(Utils(bot))

bot.run(TOKEN)