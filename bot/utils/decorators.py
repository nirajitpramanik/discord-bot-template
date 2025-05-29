"""
Custom decorators for Discord bot commands
"""

import discord
from discord.ext import commands
from functools import wraps
from typing import Union, List

def has_permissions(**permissions):
    """Check if user has specific permissions"""
    def predicate(ctx):
        if ctx.guild is None:
            return False
        
        user_permissions = ctx.author.guild_permissions
        return all(getattr(user_permissions, perm, False) for perm in permissions)
    
    return commands.check(predicate)

def bot_has_permissions(**permissions):
    """Check if bot has specific permissions"""
    def predicate(ctx):
        if ctx.guild is None:
            return False
        
        bot_permissions = ctx.guild.me.guild_permissions
        return all(getattr(bot_permissions, perm, False) for perm in permissions)
    
    return commands.check(predicate)

def is_owner_or_admin():
    """Check if user is bot owner or server admin"""
    async def predicate(ctx):
        if await ctx.bot.is_owner(ctx.author):
            return True
        
        if ctx.guild and ctx.author.guild_permissions.administrator:
            return True
        
        return False
    
    return commands.check(predicate)

def cooldown_per_guild(rate: int, per: float):
    """Apply cooldown per guild instead of per user"""
    def decorator(func):
        @wraps(func)
        async def wrapper(self, ctx, *args, **kwargs):
            bucket = commands.CooldownMapping.from_cooldown(
                rate, per, commands.BucketType.guild
            ).get_bucket(ctx.message)
            
            retry_after = bucket.update_rate_limit()
            if retry_after:
                raise commands.CommandOnCooldown(bucket, retry_after, commands.BucketType.guild)
            
            return await func(self, ctx, *args, **kwargs)
        return wrapper
    return decorator

def requires_database():
    """Ensure database connection is available"""
    def predicate(ctx):
        return hasattr(ctx.bot, 'database') and ctx.bot.database.is_connected()
    
    return commands.check(predicate)

def guild_only_command():
    """Ensure command is only used in guilds"""
    def predicate(ctx):
        return ctx.guild is not None
    
    return commands.check(predicate)