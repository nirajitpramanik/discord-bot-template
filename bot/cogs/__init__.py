"""
Cogs Package - Bot command modules
"""

import os
import logging
from discord.ext import commands

logger = logging.getLogger(__name__)

async def load_cogs(bot: commands.Bot):
    """Load all cogs from the cogs directory"""
    cogs_dir = os.path.dirname(__file__)
    
    for filename in os.listdir(cogs_dir):
        if filename.endswith('.py') and not filename.startswith('_'):
            cog_name = f"bot.cogs.{filename[:-3]}"
            try:
                await bot.load_extension(cog_name)
                logger.info(f"Loaded cog: {cog_name}")
            except Exception as e:
                logger.error(f"Failed to load cog {cog_name}: {e}")

__all__ = ['load_cogs']