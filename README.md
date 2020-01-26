# ocr-bot-discord
Make images in your server searchable

# Installation

## Requirements
* docker
* docker-compose
* Discord bot account
* gcloud project - vision API enabled
* gcloud service account

----------------------------
```
git clone https://github.com/jordanbertasso/ocr-bot-discord.git
cd ocr-bot-discord
```

edit and rename `src/discord_secrets.json.example` and `src/gcloud_keys.json.example` using the keyfile from your gcloud service account.

```
docker-compose build && docker-compose up && docker-compose logs -f
```

Invite bot to your server.
