"""
Event Listeners Package
"""

import logging
from discord.ext import commands

logger = logging.getLogger(__name__)

def setup_listeners(bot: commands.Bot):
    """Setup event listeners for the bot"""
    
    @bot.event
    async def on_guild_join(guild):
        """Called when the bot joins a guild"""
        logger.info(f"Joined guild: {guild.name} (ID: {guild.id})")
        # Add any guild setup logic here
    
    @bot.event
    async def on_guild_remove(guild):
        """Called when the bot leaves a guild"""
        logger.info(f"Left guild: {guild.name} (ID: {guild.id})")
        # Add any guild cleanup logic here
    
    @bot.event
    async def on_member_join(member):
        """Called when a member joins a guild"""
        logger.info(f"Member joined {member.guild.name}: {member}")
        # Add welcome message logic here
    
    @bot.event
    async def on_member_remove(member):
        """Called when a member leaves a guild"""
        logger.info(f"Member left {member.guild.name}: {member}")
        # Add farewell message logic here
    
    @bot.event
    async def on_message(message):
        """Called when a message is sent"""
        if message.author.bot:
            return
        
        # Process commands
        await bot.process_commands(message)
    
    logger.info("Event listeners setup complete")

__all__ = ['setup_listeners']