import httpx

APP_ID = "xxx"
DISCORD_ENDPOINT = f"applications/{APP_ID}/commands"
DISCORD_TOKEN = "xxx"

COMMAND_LIST = [
    {
        "name": "test",
        "description": "Basic command",
        "type": 1,
    },
    {
        "name": "challenge",
        "description": "Challenge to a match of rock paper scissors",
        "options": [
            {
                "type": 3,
                "name": "object",
                "description": "Pick your object",
                "required": True,
                "choices": [
                    {
                        "name": "paper",
                        "value": "paper",
                    },
                    {
                        "name": "sword",
                        "value": "sword",
                    },
                ],
            },
        ],
        "type": 1,
    },
]


def reg_command():
    url = "https://discord.com/api/v10/" + DISCORD_ENDPOINT
    print(url)
    headers = {
        "Authorization": f"Bot {DISCORD_TOKEN}",
        "Content-Type": "application/json; charset=UTF-8",
        "User-Agent": "DiscordBot (https://github.com/discord/discord-example-app, 1.0.0)",
    }
    print(headers)
    request = httpx.put(url, headers=headers, json=COMMAND_LIST)

    print(f"{request.status_code=}")
    print(f"{request.headers['content-type']=}")
    print(f"{request.text=}")


reg_command()
