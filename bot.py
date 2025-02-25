import discord
from discord.ext import commands
import aiohttp
import os
from datetime import datetime
import xml.etree.ElementTree as ET
from git import Repo
import asyncio

# Bot setup
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Configuration
CHANNEL_ID = 1342892359242743850  # Replace with your channel ID (integer)
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GITHUB_TOKEN = os.getenv('GIT_TOKEN')
REPO_PATH = './repo'  # Local path for repository
RSS_FILE = 'rss.xml'

async def update_rss(messages):
    # Clone or open repository
    if not os.path.exists(REPO_PATH):
        repo_url = f'https://{GITHUB_TOKEN}@github.com/b4h4w/discordxrss.git'
        repo = Repo.clone_from(repo_url, REPO_PATH)
    else:
        repo = Repo(REPO_PATH)

    # Create or update RSS feed
    if not os.path.exists(os.path.join(REPO_PATH, RSS_FILE)):
        rss = ET.Element('rss', version='2.0')
        channel = ET.SubElement(rss, 'channel')
        ET.SubElement(channel, 'title').text = 'Discord Channel Feed'
        ET.SubElement(channel, 'description').text = 'Latest messages from Discord channel'
    else:
        tree = ET.parse(os.path.join(REPO_PATH, RSS_FILE))
        rss = tree.getroot()
        channel = rss.find('channel')

    # Add new messages
    for message in messages:
        item = ET.SubElement(channel, 'item')
        ET.SubElement(item, 'title').text = f'Message from {message.author}'
        ET.SubElement(item, 'description').text = message.content
        ET.SubElement(item, 'pubDate').text = message.created_at.strftime('%a, %d %b %Y %H:%M:%S GMT')
        ET.SubElement(item, 'guid').text = str(message.id)

    # Write RSS file
    tree = ET.ElementTree(rss)
    tree.write(os.path.join(REPO_PATH, RSS_FILE), encoding='utf-8', xml_declaration=True)

    # Git operations
    repo.git.add(RSS_FILE)
    if repo.is_dirty():
        repo.git.commit(m=f'Update RSS feed - {datetime.now()}')
        repo.git.push()

@bot.event
async def on_ready():
    print(f'Bot connected as {bot.user}')
    while True:
        channel = bot.get_channel(CHANNEL_ID)
        if channel:
            # Get last 100 messages (Discord limit)
            messages = [message async for message in channel.history(limit=100)]
            await update_rss(messages)
        await asyncio.sleep(300)  # Wait 5 minutes

# Run the bot
bot.run(DISCORD_TOKEN)
