from __future__ import annotations

import io
import requests
import time
import filetype
import json
import re

from google.cloud import vision
from elasticsearch_dsl import Search, Document, Index, Text, Long, Q
from discord import Embed
from hashlib import md5
from es_db import Elastic_Database, Attachment
from sql import Sqlite3_db
from discord.ext import menus


class MySource(menus.ListPageSource):
    def __init__(self, data):
        super().__init__(data['fields_data'], per_page=5)
        self.search_phrase = data['search_phrase']

    async def format_page(self, menu, entries):
        offset = menu.current_page * self.per_page

        search_phrase = self.search_phrase
        embed = Embed.from_dict({
            'title': f'Search results for \"{search_phrase[:255]}\"',
            'type': 'rich',
            'fields': entries,
            'color': 0x89c6f6
        })

        return embed


# Load config keys
with open('config.json', 'r') as f:
    config = json.load(f)

# Load Discord keys
with open('discord_secrets.json', 'r') as f:
    discord_secrets = json.load(f)

# For debugging
db_connect = config['db-connect']
# TODO - Automatic index management
index_name = config['index-name']

# Google vision client
vision_client = vision.ImageAnnotatorClient()

# SQL db for storing blacklisted channels and admins
sql_db = Sqlite3_db()


# Wait for elasticsearch to initialise before we try to run setup commands
connected = False
while not connected and db_connect:
    try:
        global db
        db = Elastic_Database(index_name)
        connected = True
        print('[ELASTICSEARCH]: Successfully connected')
    except Exception as e:
        print(e)
        print("[ELASTICSEARCH]: Elasticsearch not available yet, trying again in 10s...")
        time.sleep(10)


async def handle_attachments(message: discord.message.Message) -> None:
    """ Process attached image

    Arguments:
        message {discord.message.Message} -- discord.py
    """
    # Get the Discord CDN url
    url = message.attachments[0].url

    attachment = message.attachments[0]

    # Get the raw bytes of the attachment
    filebytes = await attachment.read()

    # Guess the filetype
    kind = filetype.guess(filebytes)

    print(f'[URL]: {url}')
    print(f'[FILETYPE]: {kind.mime}')

    # Return if it's not an image
    if not 'image' in kind.mime:
        return

    # Return if the image is larger than 10MB, this is a limit of Google's OCR API
    if attachment.size > 10000000:
        print(f'[INFO]: Image too large, size: {attachment.size}')
        return

    # Save the image if it wasn't sent in a blacklisted channel
    if str(message.channel.id) not in sql_db.get_blacklisted_channels(message.guild.id):
        await save_image_text(url, message)
    else:
        print(
            f"[BLACKLIST]: channel_id {message.channel.id} in blacklisted channels")


def search(guild_id: str, phrase="", queried_user_id="") -> str:
    """ Return matching results from elasticsearch, based on a search phrase,
        a users id and the server the message was sent in

    Arguments:
        guild_id {str} -- ID of the server to query images for

    Keyword Arguments:
        phrase {str} -- The OCR'ed text to search for (default: {""})
        queried_user_id {str} -- ID of the user who sent the image (default: {""})

    Returns:
        str -- [description]
    """
    # If debug mode
    if not db_connect:
        return ""

    search = Search()

    if not phrase and not queried_user_id:
        # Empty search command
        print(f'[SEARCH]: Empty search - returning')
        return
    elif not phrase and queried_user_id:
        # Empty phrase and non empty user id
        print(f'[SEARCH]: Searching for user: {queried_user_id}')
        q = Q('bool', must=[Q('match', author_id=int(queried_user_id)),
                            Q('match', guild_id=guild_id)])
    elif phrase and queried_user_id:
        # Non empty phrase and user id
        print(
            f'[SEARCH]: Searching for phrase: {phrase} from user: {queried_user_id}')
        q = Q('bool', must=[Q('match', text=phrase),
                            Q('match', author_id=int(queried_user_id)),
                            Q('match', guild_id=guild_id)])
    else:
        # Non empty phrase and empty user id
        print(f'[SEARCH]: Searching for phrase: {phrase}')
        q = Q('bool', must=[Q('match_phrase', text=phrase),
                            Q('match', guild_id=guild_id)])

    # Execute the query
    s = search.query(q)

    # Fields that can be used in the embed
    result = [{
        'filename': h.filename,
        'author': h.author_username,
        'url': h.url,
        'message_url': h.message_url,
        'id': h.meta.id
    } for h in s.scan()]

    return result


async def save_image_text(url: str, message: discord.message.Message) -> None:
    """ Download the image, check if it already exists in the index, run OCR on the image,
        save the info to elasticsearch

    Arguments:
        url {str} -- CDN URL for the image
        message {discord.message.Message} -- discord.py
    """
    with get_image_from_url(url) as image_file:
        hash = md5(image_file.read()).hexdigest()
        print(f'[HASH]: {hash}')

        if db_connect:
            if db.exists(str(message.guild.id), hash=hash):
                print(f"[INFO]: Image {url} already exists in index")
                return

        image_file.seek(0)
        filename = get_filename_from_url(url)
        ocr_text = detect_text(image_file)

        if not ocr_text:
            print(f'[INFO]: No text detected in {filename}')
            return

        print(f'[OCR TEXT]: {ocr_text.encode()}')

    doc = Attachment(timestamp=int(time.time()*1000), author_id=int(message.author.id),
                     author_username=message.author.name+"#"+message.author.discriminator,
                     channel=message.channel.name, category_id=message.channel.category_id,
                     guild=message.guild.name, guild_id=message.guild.id,
                     message_url=message.jump_url, url=url, text=ocr_text, hash=hash,
                     filename=filename)

    if db_connect:
        db.save_attachment(doc, index_name)
        print("[INFO]: Attachment saved")
    else:
        print("No db_connect")

    return


def get_filename_from_url(url: str) -> str:
    """ Get the files name from the CDN URL

    Arguments:
        url {str} -- CDN URL of the image

    Returns:
        str -- File name
    """
    filename = url[url.rfind("/")+1:]

    return filename


def get_image_from_url(url: str) -> io.BytesIO:
    """ Return a BytesIO object of the image

    Returns:
        io.BytesIO -- In memory file-like object
    """
    r = requests.get(url, stream=True)
    image_file = io.BytesIO(r.content)

    return image_file


def detect_text(image_file):
    # Read the bytes of the BytesIO object
    image = vision.types.Image(content=image_file.read())

    text_detection_response = vision_client.text_detection(image=image)

    annotations = text_detection_response.text_annotations

    if len(annotations) > 0:
        text = annotations[0].description
    else:
        text = ''

    return text.replace('\n', ' ')


async def send_message(message, channel):
    await channel.send(message)


def get_embed_fields(search_result):
    fields = {}
    fields['fields_data'] = []
    for i, doc in enumerate(search_result):
        filename = doc['filename']
        author = doc['author']
        url = doc['url']
        es_id = doc['id']
        try:
            message_url = doc['message_url']
        except KeyError:
            message_url = ''
        fields['fields_data'].append({
            'name': f'{i+1}. {author}',
            'value': f'[{filename}]({url}) - [jump]({message_url})'
        })

    return fields


async def search_command(ctx, args):
    # Remove the user mention string from the search phrase if it is present
    try:
        if ctx.message.mentions:
            queried_user_id = ctx.message.mentions[0].id
            search_phrase = ' '.join(args).replace(
                '<@!'+str(queried_user_id)+'>', '').strip()
        else:
            # Regex for 18 digit user id
            r = re.compile('[0-9]{18}')
            queried_user_id = list(filter(r.fullmatch, args))[0]
            search_phrase = ' '.join(args).replace(queried_user_id, '').strip()
    except IndexError:
        queried_user_id = None
        search_phrase = ' '.join(args).strip()

    search_result = search(search_phrase, ctx.guild.id,
                           queried_user_id=queried_user_id)

    fields = get_embed_fields(search_result)

    fields['search_phrase'] = search_phrase
    pages = menus.MenuPages(source=MySource(
        fields), clear_reactions_after=True, timeout=30)
    await pages.start(ctx)

    return


async def ignore_command(ctx, args):
    channel = ctx.message.channel_mentions[0]
    channel_id = str(channel.id)
    guild_id = str(ctx.guild.id)
    author_id = str(ctx.author.id)

    # TODO - global guild admins and only refresh after an update to them, might need to make a new client for every guild
    guild_admins = sql_db.get_admins(ctx.guild.id)
    guild_admins.append(discord_secrets['owner-id'])

    if author_id in guild_admins:
        # TODO - If able to blacklist by channel if, check if channel is actually in guild before adding to db
        sql_db.add_blacklist_channel(guild_id, channel_id)

        await ctx.send(f"Channel {channel.mention} ignored :)")

        print(
            f"[BLACKLIST]: Channel {channel.name} - {channel.id} blacklisted")
    # Not admin
    else:
        await ctx.send(f'You must be an admin to do that :D')
        print(
            f"[BLACKLIST]: Non admin - {author_id} tried to blacklist channel {channel.name} - {channel.id}")


async def link_command(ctx, args):
    es_id = args[0]
    jump_url = db.get_jump_url_by_id(es_id)

    # TODO - Maybe deny before we get jump_url
    if jump_url:
        await ctx.send(f"{jump_url}")
    else:
        await ctx.send(f'Document with ID: {es_id} not found.')

    return


async def admin_command(ctx, args):
    guild_admins = sql_db.get_admins(ctx.guild.id)
    guild_admins.append(discord_secrets['owner-id'])
    print(
        f"[ADMINS]: Guild admins for guild {ctx.guild.name} are {guild_admins}")

    author_id = str(ctx.author.id)
    if author_id in guild_admins:
        user = ctx.message.mentions[0]
        user_id = str(user.id)

        if not user_id in guild_admins:
            sql_db.add_admin(ctx.guild.id, user.id)
            await ctx.send(f"{user.name} is now a bot admin :)")
        else:
            sql_db.remove_admin(ctx.guild.id, user.id)
            await ctx.send(f"{user.name} is no longer a bot admin :(")
    else:
        await ctx.send(f"You must be an admin to do that :D")
        print(
            f"[ADMIN]: Non admin - {ctx.author.id} tried to use admin command on {user.name}")
