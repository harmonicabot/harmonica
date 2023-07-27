import collections
import uuid

import fl.util
import fl.util.edict
import key

import fl.net.discord.bot


NOTHING = tuple()
PREFIX_JOIN = "join_"
PREFIX_SUBMIT = "submit_"
PREFIX_SUMMARY = "summary_"


# -----------------------------------------------------------------------------
def coro(runtime, cfg, inputs, state, outputs):  # pylint: disable=W0613
    """
    Transcript aggregation coroutine.

    """

    # Setup system state
    #
    #   state['session'] is a map from id_session -> info_session
    #   state['user']    is a map from id_user    -> info_user
    #   state['prompt']  is a map from id_prompt  -> str_prompt
    #
    #   info_session is { 'admin':       id_admin,
    #                     'topic':       str_topic,
    #                     'participant': set(id_user),
    #                     'contributor': set(id_user) }
    #   info_user    is { 'name':       name_user,
    #                     'session':    id_session,
    #                     'transcript': list(content) }
    #
    state = dict(session=dict(), user=dict(), prompt=dict())
    state["prompt"].update(cfg.get("prompt", dict()))

    # Main loop.
    #
    signal = fl.util.edict.init(outputs)
    while True:
        inputs = yield (outputs, signal)
        fl.util.edict.reset(outputs)

        if not inputs["ctrl"]["ena"]:
            continue
        timestamp = inputs["ctrl"]["ts"]

        list_msg_in = list()
        if inputs["discord"]["ena"]:
            list_msg_in.extend(inputs["discord"]["list"])
        if inputs["openai"]["ena"]:
            list_msg_in.extend(inputs["openai"]["list"])

        list_to_discord = list()
        list_to_openai = list()
        for msg in list_msg_in:
            (part_discord, part_openai) = _update(state, msg)
            list_to_discord += part_discord
            list_to_openai += part_openai

        if list_to_discord:
            outputs["discord"]["ena"] = True
            outputs["discord"]["ts"].update(timestamp)
            outputs["discord"]["list"][:] = list_to_discord

        if list_to_openai:
            outputs["openai"]["ena"] = True
            outputs["openai"]["ts"].update(timestamp)
            outputs["openai"]["list"][:] = list_to_openai


# -----------------------------------------------------------------------------
def _update(state, msg):
    """
    Return an update corresponding to the specified msg.

    """

    discord = list()
    openai = list()

    str_type = msg["type"]
    is_btn = str_type in {
        "btn",
    }
    is_dm = str_type in {"msg_dm", "edit_dm"}
    is_guild = str_type in {"msg_guild", "edit_guild"}
    is_appcmd = str_type in {"appcmd_dm", "appcmd_guild"}
    is_msgcmd = str_type in {"msgcmd_dm", "msgcmd_guild"}
    is_res = str_type in {
        "openai_result",
    }

    if is_appcmd and msg["name_command"] == "ask":
        discord += _on_cmd_ask(state, msg)

    if is_btn and msg["id_btn"].startswith(PREFIX_JOIN):
        discord += _on_btn_join(state, msg)

    if is_dm and msg["id_author"] in state["user"]:
        discord += _on_msg_dm(state, msg)

    if is_btn and msg["id_btn"].startswith(PREFIX_SUBMIT):
        discord += _on_btn_submit(state, msg)

    if is_btn and msg["id_btn"].startswith(PREFIX_SUMMARY):
        openai += _on_btn_summary(state, msg)

    if is_res and msg["state"]["id_prompt"] == "summary":
        discord += _on_summary(state, msg)

    if is_appcmd and msg["name_command"] == "dbg_transcript_show":
        discord += _on_cmd_dbg_transcript_show(state, msg)

    if is_appcmd and msg["name_command"] == "dbg_prompt_show":
        discord += _on_cmd_dbg_prompt_show(state, msg)

    if is_appcmd and msg["name_command"] == "dbg_prompt_set":
        discord += _on_cmd_dbg_prompt_set(state, msg)

    return (discord, openai)


# -----------------------------------------------------------------------------
def _on_cmd_ask(state, msg):
    """
    Respond to an ask command.

    """

    # Create a new session in the state.
    #
    id_user = msg["id_user"]
    str_topic = " ".join(msg["args"])
    id_session = uuid.uuid4().hex[:6]
    state["session"][id_session] = dict(
        admin=id_user,
        topic=str_topic,
        participant=set(),  # set(id_user)
        contributor=set(),
    )  # set(id_user)

    # Configure a join button for the session.
    #
    str_invite = "Join deliberation #{id}".format(id=id_session)
    cfg_button = fl.net.discord.bot.ButtonData(
        label="Join", id_btn=_id_btn(PREFIX_JOIN, id_session)
    )

    # Enqueue a message with the session join button.
    #
    msg_type = msg["type"]
    if msg_type == "appcmd_dm":
        yield dict(
            type="msg_dm", id_user=id_user, content=str_invite, button=cfg_button
        )
    if msg_type == "appcmd_guild":
        yield dict(
            type="msg_guild",
            id_channel=msg["id_channel"],
            content=str_invite,
            button=cfg_button,
        )


# -----------------------------------------------------------------------------
def _on_btn_join(state, msg):
    """
    On "Join" button press.

    """

    # Remove the user from any previous session.
    #
    id_user = msg["id_user"]
    if id_user in state["user"]:
        id_session_prev = state["user"][id_user]["session"]
        map_session_prev = state["session"][id_session_prev]

        try:
            map_session_prev["participant"].remove(id_user)
        except KeyError:
            pass

        try:
            map_session_prev["contributor"].remove(id_user)
        except KeyError:
            pass

    # Add the user to the current session.
    #
    id_session = msg["id_btn"][len(PREFIX_JOIN) :]
    map_session = state["session"][id_session]
    set_participant = map_session["participant"]
    set_participant.add(id_user)

    # Create a new transcript for the user.
    #
    name_user = msg["name_user"]
    state["user"][id_user] = dict(name=name_user, session=id_session, transcript=list())

    # Send a message to the admin.
    #
    yield dict(
        type="msg_dm",
        id_user=map_session["admin"],
        content="{name} joined session {session} "
        "as participant #{num}.".format(
            name=name_user, num=len(set_participant), session=id_session
        ),
    )

    # Send the topic and a 'Submit' button to the user.
    #
    yield dict(
        type="msg_dm",
        id_user=id_user,
        content=map_session["topic"],
        button=fl.net.discord.bot.ButtonData(
            label="Submit", id_btn=_id_btn(PREFIX_SUBMIT, id_session)
        ),
    )


# -----------------------------------------------------------------------------
def _on_msg_dm(state, msg):
    """
    On message recieved.

    """

    state["user"][msg["id_author"]]["transcript"].append(msg["content"])
    return NOTHING


# -----------------------------------------------------------------------------
def _on_btn_submit(state, msg):
    """
    On "Submit" button press.

    """

    # Mark the user as having submitted a contribution.
    #
    id_user = msg["id_user"]
    id_session = msg["id_btn"][len(PREFIX_SUBMIT) :]
    map_session = state["session"][id_session]
    map_session["contributor"].add(id_user)

    # Send a message to the admin.
    #
    set_pending = map_session["participant"] - map_session["contributor"]
    yield dict(
        type="msg_dm",
        id_user=map_session["admin"],
        content="User {name} submitted a contribution for "
        "{session}. ({count} pending)".format(
            name=msg["name_user"], session=id_session, count=len(set_pending)
        ),
        button=fl.net.discord.bot.ButtonData(
            label="Summary", id_btn=_id_btn(PREFIX_SUMMARY, id_session)
        ),
    )

    # is_last_user = (len(set_pending) == 0)
    # if is_last_user:
    #     pass  # TODO: AUTOMATICALLY SUMMARIZE


# -----------------------------------------------------------------------------
def _on_btn_summary(state, msg):
    """
    On "Summary" button press.

    """

    # Get all transcripts associated with the session.
    #
    id_session = msg["id_btn"][len(PREFIX_SUMMARY) :]
    str_transcript = ""
    for id_user, state_user in state["user"].items():
        if state_user["session"] != id_session:
            continue
        str_transcript += "\n\n{name}:\n".format(name=state_user["name"])
        for item in state_user["transcript"]:
            str_transcript += " - {item}\n".format(item=item)

    id_prompt = "summary"
    str_prompt = state["prompt"][id_prompt].format(
        str_topic=state["session"][id_session]["topic"], str_transcript=str_transcript
    )

    yield dict(
        state=dict(id_prompt=id_prompt, id_session=id_session),
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": str_prompt}],
    )


# -----------------------------------------------------------------------------
def _on_summary(state, msg):
    """
    On summary recieved.

    """

    id_session = msg["state"]["id_session"]
    str_summary = msg["response"]["choices"][0]["message"]["content"]
    for id_user, state_user in state["user"].items():
        if state_user["session"] != id_session:
            continue

        yield dict(type="msg_dm", id_user=id_user, content=str_summary)


# -----------------------------------------------------------------------------
def _on_cmd_dbg_transcript_show(state, msg):
    """
    Respond to a dbg_transcript_show command.

    """

    for id_user, state_user in state["user"].items():
        if msg["type"] == "appcmd_dm":
            yield dict(
                type="msg_dm",
                id_user=msg["id_user"],
                content='{id_user}: "{transcript}"'.format(
                    id_user=id_user, transcript=state_user["transcript"]
                ),
            )

        if msg["type"] == "appcmd_guild":
            yield dict(
                type="msg_guild",
                id_channel=msg["id_channel"],
                content='{id_user}: "{transcript}"'.format(
                    id_user=id_user, transcript=state_user["transcript"]
                ),
            )


# -----------------------------------------------------------------------------
def _on_cmd_dbg_prompt_show(state, msg):
    """
    Respond to a dbg_prompt_show command.

    """

    for id_prompt, str_prompt in state["prompt"].items():
        if msg["type"] == "appcmd_dm":
            yield dict(type="msg_dm", id_user=msg["id_user"], content=id_prompt.upper())
            yield dict(type="msg_dm", id_user=msg["id_user"], content=str_prompt)

        if msg["type"] == "appcmd_guild":
            yield dict(
                type="msg_guild",
                id_channel=msg["id_channel"],
                content=id_prompt.upper(),
            )
            yield dict(
                type="msg_guild", id_channel=msg["id_channel"], content=str_prompt
            )


# -----------------------------------------------------------------------------
def _on_cmd_dbg_prompt_set(state, msg):
    """
    Respond to a dbg_prompt_set command.

    """

    state["prompt"][msg["args"][0]] = msg["args"][1]
    return NOTHING


# -----------------------------------------------------------------------------
def _id_btn(prefix, id_session):
    """ """
    id_button = "{prefix}{id_session}".format(prefix=prefix, id_session=id_session)
    return id_button
