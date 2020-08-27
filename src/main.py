import logging
import json
import random
import string
import aiohttp

from discord import Game, Status, Webhook, AsyncWebhookAdapter
from discord.ext import commands
from lib import *

# Load config keys
with open('config.json', 'r') as f:
    config = json.load(f)

with open('discord_secrets.json', 'r') as f:
    discord_secrets = json.load(f)

bot = commands.Bot(command_prefix=config['prefix-key'])


@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    game = Game('God')
    await bot.change_presence(status=Status.online, activity=game)


def randomword(length):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))


async def send_webook(channel, embed=None, avatar_url=None):
    webhook = await channel.create_webhook(name="week", reason="week bot")

    await webhook.send(content="_ _", avatar_url=avatar_url)
    await webhook.delete()


@bot.event
async def on_message(message):
    triggers = [
        ("what week is it", send_webook, f"https://macs-week-image.herokuapp.com/image/{randomword(7)}.png")]
    # Return if bot's own message
    if message.author == bot.user:
        return

    # Check for trigger
    for trigger, callback, url in triggers:
        if trigger in message.content.lower():
            await callback(message.channel, avatar_url=url)

    # If the message has attachments
    if message.attachments:
        await handle_attachments(message)
        return

    await bot.process_commands(message)

    return


@bot.command(name='search')
async def handle_search_command(ctx, *args):
    await search_command(ctx, args)
    return


@bot.command(name='ignore')
async def handle_ignorechannel_command(ctx, *args):
    await ignore_command(ctx, args)
    return


@bot.command(name='admin')
async def handle_admin_command(ctx, *args):
    await admin_command(ctx, args)
    return


@bot.command(name='link')
async def handle_link_command(ctx, *args):
    await link_command(ctx, args)
    return


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('discord')
logger.setLevel(logging.ERROR)
handler = logging.FileHandler(
    filename='../discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter(
    '%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

bot.run(discord_secrets['discord-token'])
