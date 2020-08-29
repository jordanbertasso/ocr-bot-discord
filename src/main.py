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


async def send_webhook(channel, avatar_url: str, message: str):
    webhook = await channel.create_webhook(name="week", reason="week bot")

    await webhook.send(content=message, avatar_url=avatar_url)
    await webhook.delete()


def is_anagram(ele1, ele2):
    l1 = [c for c in ele1 if c not in string.whitespace]
    l2 = [c for c in ele2 if c not in string.whitespace]
    l1.sort()
    l2.sort()
    return l1 == l2


@bot.event
async def on_message(message):
    week_avatar_url = f"https://macs-week-image.herokuapp.com/image/{randomword(7)}.png"
    triggers = [
        ("what week is it", send_webhook, week_avatar_url, "_ _"),
        ("what week is it not", send_webhook,
         week_avatar_url, f"https://i.imgur.com/BGBvnvq.jpg"),
        ("stupid week bot", send_webhook,
         week_avatar_url, f"https://i.imgur.com/WXS93ht.jpg")
    ]

   # Return if bot's own message
    if message.author == bot.user:
        return

    # Check for trigger
    for trigger, callback, avatar_url, webhook_message in triggers:
        if is_anagram(message.content.lower(), trigger):
            await callback(message.channel, avatar_url=avatar_url, message=webhook_message)
            break

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
