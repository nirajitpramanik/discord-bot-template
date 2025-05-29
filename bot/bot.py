"""
Main Discord Bot Class
"""

import discord
from discord.ext import commands
import os
import logging
from typing import Optional

from config.settings import Settings
from database.database import Database
from .cogs import load_cogs
from .listeners import setup_listeners

logger = logging.getLogger(__name__)

class DiscordBot(commands.Bot):
    def __init__(self):
        self.settings = Settings()
        self.database = Database()
        
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.members = True
        
        super().__init__(
            command_prefix=self.get_prefix,
            intents=intents,
            help_command=None,
            case_insensitive=True
        )
    
    async def get_prefix(self, message: discord.Message) -> str:
        """Get the command prefix for a guild"""
        if message.guild:
            # You can implement per-guild prefixes here
            return self.settings.DEFAULT_PREFIX
        return self.settings.DEFAULT_PREFIX
    
    async def setup_hook(self):
        """Called when the bot is starting up"""
        logger.info("Setting up bot...")
        
        # Initialize database
        await self.database.initialize()
        
        # Load cogs
        await load_cogs(self)
        
        # Setup event listeners
        setup_listeners(self)
        
        # Sync slash commands
        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} slash commands")
        except Exception as e:
            logger.error(f"Failed to sync slash commands: {e}")
    
    async def on_ready(self):
        """Called when the bot is ready"""
        logger.info(f"Bot is ready! Logged in as {self.user}")
        logger.info(f"Bot is in {len(self.guilds)} guilds")
        
        # Set bot status
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{len(self.guilds)} servers"
        )
        await self.change_presence(activity=activity, status=discord.Status.online)
    
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        """Global command error handler"""
        if isinstance(error, commands.CommandNotFound):
            return
        
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You don't have permission to use this command.")
            return
        
        if isinstance(error, commands.BotMissingPermissions):
            await ctx.send("❌ I don't have the required permissions to execute this command.")
            return
        
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏱️ Command is on cooldown. Try again in {error.retry_after:.1f} seconds.")
            return
        
        logger.error(f"Unhandled command error: {error}", exc_info=error)
        await ctx.send("❌ An error occurred while processing your command.")
    
    async def start(self):
        """Start the bot"""
        token = os.getenv('DISCORD_TOKEN')
        if not token:
            raise ValueError("DISCORD_TOKEN environment variable not set")
        
        await super().start(token)
    
    async def close(self):
        """Clean shutdown"""
        logger.info("Shutting down bot...")
        await self.database.close()
        await super().close()