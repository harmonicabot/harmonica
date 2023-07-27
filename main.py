from typing import Union

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class InteractionType:
    PING = 1
    APPLICATION_COMMAND = 2
    MESSAGE_COMPONENT = 3
    APPLICATION_COMMAND_AUTOCOMPLETE = 4
    MODAL_SUBMIT = 5


class InteractionResponseType:
    PONG = 1
    CHANNEL_MESSAGE_WITH_SOURCE = 4
    DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE = 5
    DEFERRED_UPDATE_MESSAGE = 6
    UPDATE_MESSAGE = 7
    APPLICATION_COMMAND_AUTOCOMPLETE_RESULT = 8
    MODAL = 9


class Interaction(BaseModel):
    type: str
    id: str
    data: dict


@app.get("/")
def index():
    return {"type": InteractionResponseType.PONG}


@app.post("/interactions")
def interactions(interaction: Interaction):
    interaction_type = interaction.type
    interaction_id = interaction.id
    interaction_data = interaction.data

    print(f"{interaction=}")

    return {"type": InteractionResponseType.PONG}
