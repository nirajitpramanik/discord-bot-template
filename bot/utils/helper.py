"""
Helper utility functions for the Discord bot
"""

import discord
import asyncio
from datetime import datetime, timedelta
from typing import Union, List, Optional, Any
import re

def format_time(seconds: Union[int, float]) -> str:
    """Format seconds into human readable time"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes, secs = divmod(seconds, 60)
        return f"{int(minutes)}m {int(secs)}s"
    else:
        hours, remainder = divmod(seconds, 3600)
        minutes, secs = divmod(remainder, 60)
        return f"{int(hours)}h {int(minutes)}m {int(secs)}s"

def truncate_string(text: str, max_length: int = 2000, suffix: str = "...") -> str:
    """Truncate string to fit Discord's character limits"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def get_user_avatar(user: Union[discord.User, discord.Member]) -> str:
    """Get user's avatar URL with fallback to default"""
    if user.avatar:
        return user.avatar.url
    return user.default_avatar.url

def create_embed(
    title: str = None,
    description: str = None,
    color: Union[discord.Color, int] = discord.Color.blue(),
    thumbnail: str = None,
    image: str = None,
    footer: str = None,
    footer_icon: str = None,
    author: str = None,
    author_icon: str = None,
    timestamp: datetime = None,
    fields: List[dict] = None
) -> discord.Embed:
    """Create a Discord embed with common formatting"""
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=timestamp or datetime.utcnow()
    )
    
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)
    
    if image:
        embed.set_image(url=image)
    
    if footer:
        embed.set_footer(text=footer, icon_url=footer_icon)
    
    if author:
        embed.set_author(name=author, icon_url=author_icon)
    
    if fields:
        for field in fields:
            embed.add_field(
                name=field.get('name', '\u200b'),
                value=field.get('value', '\u200b'),
                inline=field.get('inline', True)
            )
    
    return embed

def paginate_text(text: str, max_length: int = 2000) -> List[str]:
    """Split text into pages that fit Discord's character limit"""
    if len(text) <= max_length:
        return [text]
    
    pages = []
    current_page = ""
    
    for line in text.split('\n'):
        if len(current_page) + len(line) + 1 <= max_length:
            current_page += line + '\n'
        else:
            if current_page:
                pages.append(current_page.rstrip())
            current_page = line + '\n'
    
    if current_page:
        pages.append(current_page.rstrip())
    
    return pages

def convert_to_bool(value: Any) -> bool:
    """Convert various inputs to boolean"""
    if isinstance(value, bool):
        return value
    
    if isinstance(value, str):
        return value.lower() in ('yes', 'true', '1', 'on', 'enable', 'enabled')
    
    if isinstance(value, (int, float)):
        return bool(value)
    
    return False

def parse_time_string(time_str: str) -> Optional[timedelta]:
    """Parse time string like '1h30m' into timedelta"""
    pattern = r'(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?'
    match = re.match(pattern, time_str.lower())
    
    if not match:
        return None
    
    days, hours, minutes, seconds = match.groups()
    
    total_seconds = 0
    if days:
        total_seconds += int(days) * 86400
    if hours:
        total_seconds += int(hours) * 3600
    if minutes:
        total_seconds += int(minutes) * 60
    if seconds:
        total_seconds += int(seconds)
    
    return timedelta(seconds=total_seconds) if total_seconds > 0 else None

def clean_mentions(text: str) -> str:
    """Remove Discord mentions from text"""
    # Remove user mentions
    text = re.sub(r'<@!?\d+>', '', text)
    # Remove role mentions
    text = re.sub(r'<@&\d+>', '', text)
    # Remove channel mentions
    text = re.sub(r'<#\d+>', '', text)
    # Remove custom emoji
    text = re.sub(r'<a?:\w+:\d+>', '', text)
    
    return text.strip()

async def wait_for_reaction(
    bot,
    message: discord.Message,
    user: Union[discord.User, discord.Member],
    emoji: Union[str, List[str]] = None,
    timeout: float = 60.0
) -> Optional[discord.Reaction]:
    """Wait for a specific reaction from a user"""
    def check(reaction, reaction_user):
        if reaction_user != user or reaction.message.id != message.id:
            return False
        
        if emoji is None:
            return True
        
        if isinstance(emoji, list):
            return str(reaction.emoji) in emoji
        
        return str(reaction.emoji) == emoji
    
    try:
        reaction, _ = await bot.wait_for('reaction_add', check=check, timeout=timeout)
        return reaction
    except asyncio.TimeoutError:
        return None

def format_user_mention(user: Union[discord.User, discord.Member]) -> str:
    """Format user mention with fallback to username"""
    try:
        return user.mention
    except:
        return f"@{user.display_name}"

def get_guild_icon(guild: discord.Guild) -> str:
    """Get guild icon URL with fallback"""
    if guild.icon:
        return guild.icon.url
    return "https://cdn.discordapp.com/embed/avatars/0.png"