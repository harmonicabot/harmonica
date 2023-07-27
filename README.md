# harmonica

LLM-powered chatbot for superfast sensemaking and deliberation.

Majority of code is inside `[experiments/](experiments)` folder. Includes
harmonica code taken from an integration with another platform.

New development should take place starting with [main.py](./main.py).

## Development

Setup a virtual env:

```sh
python3 -m venv venv
```

Run dev server with:

```sh
make dev
```

Linting:

```sh
make lint
```

Testing:

```sh
make test
```

## Discord

### Creating a discord bot account

Before writing code for the bot, you need to create a bot account from the
Discord developer portal.

1. Go to the Discord Developer Portal (https://discord.com/developers/applications)
1. Click on the "New Application" button.
1. Give a name to the application and click on "Create".
1. Click on the "Bot" tab and then click "Add Bot". Confirm the popup.
1. Copy the token under the "Bot" tab and keep it somewhere safe. If you lose it
    you can generate a new one by clicking on ``Reset Token``

### Configuring the discord bot

In the "Bot" tab, make sure the following are selected by clicking the grey
button on the right (blue means selected):

* PUBLIC BOT
* PRESENCE INTENT
* SERVER MEMBERS INTENT
* MESSAGE CONTENT INTENT

Now save the changes made to the Bot tab.

### Inviting the bot to a server

To interact with your bot, it needs to be added to a server.

1. Open the 'OAuth2' tab, then click on the 'URL Generator'
1. Under `SCOPES` click 'bot'
1. Under 'Bot Permissions', enable each of the following permissions:

    * Read Messages/View Channels
    * Send Messages
    * Manage Messages
    * Embed Links
    * Attach Files
    * Read Message History
    * Add Reactions

1. Copy the generated URL and open it in your web browser to add your bot to a
server.

## LICENSE

Apache License 2.0
