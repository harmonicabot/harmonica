import asyncio
import collections
import logging
import multiprocessing
import os
import queue


PREFIX_COMMAND = "/"


# This global register exists so that we
# can reference callbacks from generated
# code that is being evaluated with eval().
#
map_register = dict()


# -----------------------------------------------------------------------------
FileData = collections.namedtuple(
    "FileData", ["filename", "spoiler", "description", "buffer"]
)

ButtonData = collections.namedtuple("ButtonData", ["label", "id_btn"])


# -----------------------------------------------------------------------------
def coro(cfg_bot):
    """
    Yield results for workflow coroutines sent to the OpenAI web API.

    Start the client in a separate process.

    """

    for str_key in ("str_token", "secs_sleep", "id_system", "id_node"):
        if str_key not in cfg_bot:
            raise ValueError(
                "Missing required configuration: {key}".format(key=str_key)
            )

    if not isinstance(cfg_bot["str_token"], str):
        raise ValueError('cfg_bot["str_token"] must be a string.')

    if not isinstance(cfg_bot["secs_sleep"], (int, float)):
        raise ValueError('cfg_bot["secs_sleep"] must be an integer or float value.')

    if not isinstance(cfg_bot["id_system"], (str, type(None))):
        raise ValueError('cfg_bot["id_system"] must be a string or None.')

    if not isinstance(cfg_bot["id_node"], (str, type(None))):
        raise ValueError('cfg_bot["id_node"] must be a string or None.')

    str_name_process = "discord-bot"
    fcn_bot = _discord_bot
    queue_to_bot = multiprocessing.Queue()  # system  --> discord
    queue_from_bot = multiprocessing.Queue()  # discord --> system
    tup_args = (cfg_bot, queue_to_bot, queue_from_bot)
    proc_bot = multiprocessing.Process(
        target=fcn_bot, args=tup_args, name=str_name_process, daemon=True
    )  # So we get terminated
    proc_bot.start()

    list_to_bot = list()
    list_from_bot = list()

    while True:
        list_to_bot.clear()
        (list_to_bot) = yield (list_from_bot)
        list_from_bot.clear()

        # If the rest of the system sends us
        # any system messages or new commands
        # to configure, then forward them
        # on to the discord client process
        # to either be sent to the relevant
        # DM or channel (in the case of messages),
        # or to use to configure new commands
        # (in the case of command configuration).
        #
        for item in list_to_bot:
            try:
                queue_to_bot.put(item, block=False)
            except queue.Full as err:
                list_from_bot.append(
                    dict(
                        type="log_event", content="Item dropped: queue_to_bot is full."
                    )
                )
                break

        # Retrieve any user messages, command
        # invocations or log messages from the
        # discord client and forward them to
        # the rest of the system for further
        # processing.
        #
        while True:
            try:
                list_from_bot.append(queue_from_bot.get(block=False))
            except queue.Empty:
                break


# -----------------------------------------------------------------------------
def _discord_bot(cfg_bot, queue_to_bot, queue_from_bot):
    """
    Run the discord client.

    This function is expected to be run in a separate daemon process.

    """

    import collections.abc
    import copy
    import functools
    import io
    import itertools
    import keyword
    import logging
    import os
    import textwrap
    import typing

    import discord
    import discord.app_commands
    import discord.ext
    import discord.ext.commands

    # We distinguish between event logging, metric
    # logging and data logging. Event logging is
    # primarily concerned with qualtitatively
    # recording the occurrence of significant
    # events such as errors or warnings. Metric
    # logging by contrast is primarily concerned
    # with regular quantitative measurements of
    # performance characteristics of the system.
    # Finally, data logging is primarily concerned
    # with recording functional chain inputs and
    # outputs for resimulation and regression
    # testing. We use two event loggers here.
    # One is set up by discord.py, and another
    # is set up here to handle logging in this
    # wrapper.
    #
    map_log_metric = dict()

    id_system = cfg_bot.get("id_system", None)
    id_node = cfg_bot.get("id_node", None)
    level_log_event = cfg_bot.get("level_log", logging.INFO)

    if id_system and id_node:
        id_log_event = "{id_sys}.{id_node}.bot".format(
            id_sys=id_system, id_node=id_node
        )
    else:
        id_log_event = "discord.bot"

    (log_event, handler_log_event) = fl.log.event.logger(
        str_id=id_log_event, level=level_log_event
    )

    intents = discord.Intents.default()
    intents.guilds = True
    intents.dm_messages = True
    intents.dm_reactions = True
    intents.message_content = True
    intents.messages = True
    intents.reactions = True
    intents.guild_messages = True
    bot = discord.ext.commands.Bot(command_prefix=PREFIX_COMMAND, intents=intents)

    # -------------------------------------------------------------------------
    @bot.event
    async def on_ready():
        """
        Create worker tasks once the client is ready.

        This callback is invoked once the
        client is done preparing the data
        that has been received from Discord.
        This usually happens after login
        is successful and the Client.guilds
        and similar data structures are
        filled up.

        """

        log_event.info("Discord bot is ready.")
        task_msg = bot.loop.create_task(
            coro=_service_all_queues(
                cfg_bot, handler_log_event, queue_to_bot, queue_from_bot
            )
        )

    # -------------------------------------------------------------------------
    async def _service_all_queues(
        cfg_bot, handler_log_event, queue_to_bot, queue_from_bot
    ):
        """
        Message queue servicing coroutine.

        This coroutine is intended to
        run continuously, servicing
        the multiprocessing.queue
        instance that feeds messages
        from the rest of the system to
        the discord bot.

        This coroutine is started from
        the on_ready callback - i.e as
        soon as the discord bot is
        ready.

        """

        # This is a redundant sanity check, as
        # the service task should be created in
        # the on_ready callback.
        #
        await bot.wait_until_ready()

        state = dict(
            count_log_attempt=0,
            map_channel=dict(),
            map_user=dict(),
            map_cmd=dict(),
            map_app_cmd=dict(),
        )

        while True:
            # Try to send log data from the
            # discord bot to the rest of the
            # system.
            #
            _service_queue_from_bot(handler_log_event, map_log_metric, queue_from_bot)

            # Service outbound messages from the
            # system to discord, then command
            # configuration from the system to
            # discord. Sleep only if we need to
            # wait for new data to be ready.
            #
            is_data_rx = await _service_queue_to_bot(state, queue_to_bot)
            do_wait = not is_data_rx
            if do_wait:
                await asyncio.sleep(cfg_bot["secs_sleep"])

    # -------------------------------------------------------------------------
    def _service_queue_from_bot(handler_log_event, map_log_metric, queue_from_bot):
        """
        Send log data from the discord bot to the rest of the system.

        """

        _send_event_log_to_system(handler_log_event, queue_from_bot)
        _send_metric_log_to_system(map_log_metric, queue_from_bot)

    # ---------------------------------`---------------------------------------
    def _send_event_log_to_system(handler_log_event, queue_from_bot):
        """
        Send event log data from the discord bot to the rest of the system.

        """

        while handler_log_event.list_event:
            try:
                queue_from_bot.put(handler_log_event.list_event.pop(0), block=False)
            except queue.Full:
                log_event.error(
                    "One or more log_event messages " "dropped. queue_from_bot is full."
                )
                break

    # ---------------------------------`---------------------------------------
    def _send_metric_log_to_system(map_log_metric, queue_from_bot):
        """
        Send metric log data from the discord bot to the rest of the system.

        """

        if map_log_metric:
            message = dict(type="log_metric")
            message.update(map_log_metric)
            try:
                queue_from_bot.put(message, block=False)
            except queue.Full:
                log_event.error(
                    "One or more log_metric messages "
                    "dropped. queue_from_bot is full."
                )
            finally:
                map_log_metric.clear()

    # ---------------------------------`---------------------------------------
    async def _service_queue_to_bot(state, queue_to_bot):
        """
        Recieve items being sent from the system to the discord bot.

        """

        try:
            item = queue_to_bot.get(block=False)
        except queue.Empty:
            is_data_rx = False
        else:
            is_data_rx = True
            type_item = item["type"]
            if type_item in {"cfg_msgcmd", "cfg_appcmd"}:
                await _configure_command(state=state, cfg_cmd=item)
            elif type_item in {"msg_guild", "msg_dm"}:
                await _send_message(state=state, msg=item)
            else:
                raise RuntimeError(
                    "Did not recognise item type: {type}".format(type=type_item)
                )
        return is_data_rx

    # -------------------------------------------------------------------------
    async def _configure_command(state, cfg_cmd):
        """
        Configure discord with the specified command.

        """

        _validate_command_configuration(cfg_cmd)

        # Configure message commands.
        #
        str_type = cfg_cmd["type"]
        if str_type == "cfg_msgcmd":
            str_name = cfg_cmd["name"]
            log_event.info("Configure msgcmd {name}.".format(name=str_name))

            str_desc = cfg_cmd["description"]
            obj_cmd = discord.ext.commands.Command(
                map_register["on_cmd"], name=str_name, help=str_desc
            )
            try:
                bot.add_command(obj_cmd)
            except discord.DiscordException as err:
                log_event.error("Could not add message command: {err}".format(err=err))
            else:
                state["map_cmd"][str_name] = obj_cmd

        # Configure application commands.
        #
        elif str_type == "cfg_appcmd":
            str_name = cfg_cmd["name"]
            log_event.info("Configure appcmd {name}.".format(name=str_name))

            str_desc = cfg_cmd["description"]
            map_param = cfg_cmd.get("param", dict())
            list_param = list(("interaction",))
            list_arg = list(("interaction",))
            for id_param, type_param in map_param.items():
                list_param.append("{id}: {type}".format(id=id_param, type=type_param))
                list_arg.append(id_param)
            str_generated = textwrap.dedent(
                """
                                    async def {id}({param}):
                                        await map_register['on_appcmd']({arg})
                                    """.format(
                    id=str_name, param=", ".join(list_param), arg=", ".join(list_arg)
                )
            )
            exec(str_generated, globals())
            cmd = discord.app_commands.Command(
                name=str_name, description=str_desc, callback=globals()[str_name]
            )
            try:
                bot.tree.add_command(cmd)
            except discord.DiscordException as err:
                log_event.error(
                    "Could not add application command: {err}".format(err=err)
                )
            else:
                state["map_app_cmd"][str_name] = cmd

        else:
            pass

    # -------------------------------------------------------------------------
    def _validate_command_configuration(cfg_cmd):
        """
        Validate the provided cfg_cmd dict.

        Throws a ValueError if it is not valid.

        """

        # ---------------------------------------------------------------------
        def _is_valid_name(name):
            """
            Return True iff name is valid, false otherwise.

            """
            is_identifier = name.isidentifier()
            is_keyword = keyword.iskeyword(name)
            is_valid = is_identifier and (not is_keyword)

            return is_valid

        set_key_required = set(("type", "name", "description"))
        set_key_optional = set(("param",))
        set_key_str = set(("type", "name", "description"))
        set_key_dict = set(("param",))
        set_key_allowed = set_key_required | set_key_optional
        set_key_actual = set(cfg_cmd.keys())
        set_key_missing = set_key_required - set_key_actual
        set_key_surplus = set_key_actual - set_key_allowed
        set_type_allowed = set(("cfg_msgcmd", "cfg_appcmd"))

        if set_key_missing:
            raise ValueError(
                "Command config is missing fields: "
                '"{key}".'.format(key='", "'.join(set_missing))
            )

        if set_key_surplus:
            raise ValueError(
                "Command config has extra fields: "
                '"{key}".'.format(key='", "'.join(set_key_surplus))
            )

        for key in set_key_str:
            if (key in cfg_cmd) and (not isinstance(cfg_cmd[key], str)):
                raise ValueError(
                    'Command config "{key}" value should be a string. '
                    "Got a {typ} instead.".format(
                        key=key, typ=type(cfg_cmd[key]).__name__
                    )
                )

        for key in set_key_dict:
            if (key in cfg_cmd) and (not isinstance(cfg_cmd[key], dict)):
                raise ValueError(
                    'Command config "{key}" value should be a dict. '
                    "Got a {typ} instead.".format(
                        key=key, typ=type(cfg_cmd[key]).__name__
                    )
                )

        str_type = cfg_cmd["type"]
        if str_type not in set_type_allowed:
            raise ValueError(
                'Command config "type" value should be one of '
                '"{allow}". Got "{act}" instead.'.format(
                    allow='", "'.join(set_type_allowed), act=str_type
                )
            )

        str_name = cfg_cmd["name"]
        if not _is_valid_name(str_name):
            raise ValueError(
                "Command name should be a valid Python identifier "
                'and not a reserved keyword. Got "{name}".'.format(name=str_name)
            )

        map_param = cfg_cmd.get("param", dict())
        for name_param, type_param in map_param.items():
            if not _is_valid_name(name_param):
                raise ValueError(
                    "Parameter name should be valid Python identifier "
                    'and not a reserved keyword. Got "{name}".'.format(name=name_param)
                )

    # -------------------------------------------------------------------------
    async def on_cmd(ctx):
        """
        Callback for all configured message commands.

        This callback provides a generic
        implementation for all message
        commands which are set via
        configuration.

        """

        log_event.debug('Msgcmd "{name}" invoked.'.format(name=ctx.command.name))
        if ctx.guild is None:
            map_cmd = dict(type="msgcmd_dm")
        else:
            map_cmd = dict(
                type="msgcmd",
                id_guild=ctx.guild.id,
                name_guild=ctx.guild.name,
                name_channel=ctx.channel.name,
                nick_author=ctx.author.nick,
            )
        map_cmd.update(
            dict(
                name_command=ctx.command.name,
                args=ctx.args[1:],
                id_channel=ctx.channel.id,
                id_author=ctx.author.id,
                name_author=ctx.author.name,
            )
        )
        try:
            queue_from_bot.put(map_cmd, block=False)
        except queue.Full:
            log_event.error("Command input dropped: " "queue_from_bot is full.")

    # Update the global callback register so that
    # on_cmd can be called from generated code
    # inside a call to eval().
    #
    map_register["on_cmd"] = on_cmd

    # -------------------------------------------------------------------------
    async def on_appcmd(interaction, *args):
        """
        Callback for all configured application commands.

        This callback provides a generic
        implementation for all application
        commands which are set via
        configuration.

        """

        await interaction.response.defer(ephemeral=True)
        log_event.debug(
            'Appcmd "{name}" invoked.'.format(name=interaction.command.name)
        )
        if interaction.guild is None:
            map_cmd = dict(type="appcmd_dm")
        else:
            map_cmd = dict(
                type="appcmd_guild",
                id_guild=interaction.guild.id,
                name_guild=interaction.guild.name,
                name_channel=interaction.channel.name,
                nick_user=interaction.user.nick,
            )
        map_cmd.update(
            dict(
                name_command=interaction.command.name,
                id_channel=interaction.channel.id,
                id_user=interaction.user.id,
                name_user=interaction.user.name,
                args=args,
            )
        )

        try:
            queue_from_bot.put(map_cmd, block=False)
        except queue.Full:
            log_event.error("Command input dropped: " "queue_from_bot is full.")
        await interaction.followup.send("OK", ephemeral=True)

    # Update the global callback register so that
    # on_appcmd can be called from generated code
    # inside a call to eval().
    #
    map_register["on_appcmd"] = on_appcmd

    # -------------------------------------------------------------------------
    async def on_button(interaction, *args):
        """
        Generic button press callback.

        """

        await interaction.response.defer(ephemeral=True)
        id_btn = interaction.data["custom_id"]
        log_event.debug("Button pressed: {id}".format(id=id_btn))

        map_cmd = dict(
            type="btn",
            id_btn=id_btn,
            id_user=interaction.user.id,
            name_user=interaction.user.name,
            id_channel=interaction.channel.id,
        )
        try:
            queue_from_bot.put(map_cmd, block=False)
        except queue.Full:
            log_event.error("Button input dropped: queue_from_bot is full.")

    # =========================================================================
    class ButtonView(discord.ui.View):
        """
        A view containing a single button.

        """

        # ---------------------------------------------------------------------
        def __init__(self, style, label, id_btn, callback, timeout=600):
            """
            Construct the button view.

            """

            super().__init__(timeout=timeout)
            self.button = discord.ui.Button(style=style, label=label, custom_id=id_btn)
            self.button.callback = callback
            self.add_item(self.button)

    # -------------------------------------------------------------------------
    async def _send_message(state, msg):
        """
        Send the specified message to the discord API.

        """

        _validate_message_data(msg)

        # If we have a new message to
        # handle, then simply send it
        # to the specified channel.
        #
        type_msg = msg.pop("type")
        if type_msg == "msg_dm":
            map_user = state["map_user"]
            id_user = msg.pop("id_user")
            if id_user not in map_user.keys():
                map_user[id_user] = await bot.fetch_user(id_user)

            if map_user[id_user] is None:
                map_user[id_user] = await bot.fetch_user(id_user)

            if map_user[id_user] is None:
                log_event.critical(
                    "Unable to access user: {id}. "
                    "Please check permissions.".format(id=str(id_user))
                )

            maybe_user_or_channel = map_user[id_user]

        elif type_msg == "msg_guild":
            map_channel = state["map_channel"]
            id_chan = msg.pop("id_channel")
            if id_chan not in map_channel:
                map_channel[id_chan] = await bot.fetch_channel(id_chan)

            if map_channel[id_chan] is None:
                map_channel[id_chan] = await bot.fetch_channel(id_chan)

            if map_channel[id_chan] is None:
                log_event.critical(
                    "Unable to access channel: {id}. "
                    "Please check permissions.".format(id=str(id_chan))
                )

            maybe_user_or_channel = map_channel[id_chan]

        else:
            raise RuntimeError("Unknown message type: {type}".format(type=type_msg))

        # Messages are a dict with fields
        # that correspond to the keyword
        # args of the discord channel
        # send function.
        #
        # https://discordpy.readthedocs.io/en/stable/api.html#channels
        #
        # We want to be able to send files
        # without requiring access to the
        # local filesystem, so we add
        # special handling for 'file'
        # fields to support the use of
        # a FileData named tuple, which
        # allows us to encode the file
        # in an in-memory buffer rather
        # than as a file handle.
        #
        if "file" in msg and isinstance(msg["file"], FileData):
            file_data = msg.pop("file")
            msg["file"] = discord.File(
                fp=io.BytesIO(file_data.buffer),
                filename=file_data.filename,
                spoiler=file_data.spoiler,
                description=file_data.description,
            )

        if "button" in msg and isinstance(msg["button"], ButtonData):
            button_data = msg.pop("button")
            msg["view"] = ButtonView(
                style=discord.ButtonStyle.green,
                label=button_data.label,
                id_btn=button_data.id_btn,
                callback=on_button,
            )

        if maybe_user_or_channel is not None:
            try:
                await maybe_user_or_channel.send(**msg)
            except discord.DiscordException as err:
                log_event.error("Failed to send message: {err}".format(err=err))

    # -------------------------------------------------------------------------
    def _validate_message_data(msg):
        """
        Validate the provided msg dict.

        Throws a ValueError if it is not valid.

        """

        if not isinstance(msg, collections.abc.Mapping):
            raise ValueError("Invalid message recieved: {msg}".format(msg=type(msg)))

    # -------------------------------------------------------------------------
    @bot.event
    async def on_command_error(ctx, error):
        """
        Handle errors in commands.

        """
        log_event.error('on_command_error: "{err}"'.format(err=str(error)))

        # We make some specififc errors visible
        # to the user on the client side.
        #
        if isinstance(
            error,
            (
                discord.ext.commands.CommandNotFound,
                discord.ext.commands.DisabledCommand,
                discord.ext.commands.DisabledCommand,
            ),
        ):
            await ctx.send(str(error))

        # Anything else, we send a generic error
        # message to the user and raise an
        # exception that is logged on the sever
        # so the developer can address it.
        #
        else:
            str_msg = "An error has been logged."
            await ctx.send(str_msg)

    # -------------------------------------------------------------------------
    @bot.event
    async def on_message(message):
        """
        Handle messages that are sent to the client.

        This coroutine is invoked
        whenever a message is created
        and sent.

        This coroutine is intended to
        simply forward the content of
        the message to the rest of the
        system via the queue_from_bot
        queue.

        """

        await bot.process_commands(message)

        if message.author.bot:
            return

        if message.content.startswith(PREFIX_COMMAND):
            return

        if isinstance(message.channel, discord.DMChannel):
            item = dict(
                type="msg_dm",
                id_msg=message.id,
                id_author=message.author.id,
                name_author=message.author.name,
                content=message.content,
            )
            log_event.info('DM: "{txt}"'.format(txt=message.content))
        else:
            item = dict(
                type="msg_guild",
                id_prev=None,
                id_msg=message.id,
                id_author=message.author.id,
                name_author=message.author.name,
                id_channel=message.channel.id,
                name_channel=message.channel.name,
                content=message.content,
            )
            log_event.info('Guild message: "{txt}"'.format(txt=message.content))

        try:
            queue_from_bot.put(item, block=False)
        except queue.Full:
            log_event.error("Message dropped. queue_from_bot is full.")

    # -------------------------------------------------------------------------
    @bot.event
    async def on_message_edit(msg_before, msg_after):
        """
        Handle message-edits that are sent to the client.

        This coroutine is invoked
        whenever a message receives
        an update event. If the
        message is not found in the
        internal message cache, then
        these events will not be
        called.

        Messages might not be in
        cache if the message is
        too old or the client is
        participating in high
        traffic guilds.

        This coroutine is intended to
        simply forward the content of
        the message to the rest of the
        system via the queue_from_bot
        queue.

        """

        if msg_after.author.bot:
            return

        if msg_after.content.startswith(PREFIX_COMMAND):
            return

        if isinstance(msg_before.channel, discord.DMChannel):
            item = dict(
                type="edit_dm",
                id_prev=msg_before.id,
                id_msg=msg_after.id,
                id_author=msg_after.author.id,
                name_author=msg_after.author.name,
                content=msg_after.content,
            )
            log_event.info('DM edit: "{txt}"'.format(txt=msg_after.content))
        else:
            item = dict(
                type="edit_guild",
                id_prev=msg_before.id,
                id_msg=msg_after.id,
                id_author=msg_after.author.id,
                name_author=msg_after.author.name,
                nick_author=msg_after.author.nick,
                id_channel=msg_after.channel.id,
                name_channel=msg_after.channel.name,
                content=msg_after.content,
            )
            log_event.info('Guild msg edit: "{txt}"'.format(txt=msg_after.content))

        try:
            queue_from_bot.put(item, block=False)
        except queue.Full:
            log_event.error("Message dropped. queue_from_bot is full.")

    # -------------------------------------------------------------------------
    @bot.command(name="bot_sync_commands")
    async def bot_sync_commands(
        ctx, operation: typing.Literal["global", "guild"] = "global"
    ):
        """
        Sync bot commands either globally or to a specific guild.

        """

        if not await bot.is_owner(ctx.author):
            msg = (
                "Error: Only the bot owner is permitted "
                "to use the bot_sync_commands command."
            )
            log_event.error(msg)
            await ctx.send(msg)
            return

        elif operation == "global":
            tup_cmd = bot.tree.get_commands()
            count_cmd = len(tup_cmd)
            msg = "Sync {count} commands to " "the global scope.".format(
                count=count_cmd
            )
            log_event.info(msg)
            await ctx.send(msg)
            for idx, cmd in enumerate(tup_cmd, start=1):
                msg = '{idx:02}: "{name}"'.format(idx=idx, name=cmd.name)
                log_event.info(msg)
                await ctx.send(msg)
            await bot.tree.sync()

        elif operation == "guild":
            tup_cmd = bot.tree.get_commands()
            count_cmd = len(tup_cmd)
            msg = "Sync {count} commands to " "the guild scope.".format(count=count_cmd)
            log_event.info(msg)
            await ctx.send(msg)
            for idx, cmd in enumerate(tup_cmd, start=1):
                msg = '{idx:02}: "{name}"'.format(idx=idx, name=cmd.name)
                log_event.info(msg)
                await ctx.send(msg)
            bot.tree.copy_global_to(guild=ctx.guild)
            await bot.tree.sync(guild=ctx.guild)

        else:
            msg = "Unsupported bot_sync_commands " 'operation: "{op}".'.format(
                op=operation
            )
            log_event.warning(msg)
            await ctx.send(msg)

    # -------------------------------------------------------------------------
    @bot.command(name="bot_show_commands")
    async def bot_show_commands(
        ctx, operation: typing.Literal["global", "guild"] = "global"
    ):
        """
        Sync bot commands either globally or to a specific guild.

        """

        if not await bot.is_owner(ctx.author):
            msg = (
                "Error: Only the bot owner is permitted "
                "to use the bot_show_commands command."
            )
            log_event.error(msg)
            await ctx.send(msg)
            return

        if operation == "global":
            tup_cmd = bot.tree.get_commands()
            count_cmd = len(tup_cmd)
            msg = "There are {count} commands in the " "global scope.".format(
                count=count_cmd
            )
            log_event.info(msg)
            await ctx.send(msg)
            for idx, cmd in enumerate(tup_cmd, start=1):
                msg = '{idx:02}: "{name}"'.format(idx=idx, name=cmd.name)
                log_event.info(msg)
                await ctx.send(msg)

        elif operation == "guild":
            tup_cmd = bot.tree.get_commands(guild=ctx.guild)
            count_cmd = len(tup_cmd)
            msg = "There are {count} commands in the " "guild scope.".format(
                count=count_cmd
            )
            log_event.info(msg)
            await ctx.send(msg)
            for idx, cmd in enumerate(tup_cmd, start=1):
                msg = '{idx:02}: "{name}"'.format(idx=idx, name=cmd.name)
                log_event.info(msg)
                await ctx.send(msg)

        else:
            msg = "Unsupported bot_show_commands " 'operation: "{op}".'.format(
                op=operation
            )
            log_event.warning(msg)
            await ctx.send(msg)

    # -------------------------------------------------------------------------
    @bot.command(name="bot_delete_all_messages")
    async def bot_delete_all_messages(ctx, limit: int = 100):
        """
        Delete all messages in the channel.

        Function is rate limited on the client
        side to about 1 deletion per second.

        The Discord server side rate limit is
        documented as being 5 requests per second
        per API token, but in practice is somewhat
        less than that.

        This requires the "Manage Messages" bot
        permission.

        """

        if not await bot.is_owner(ctx.author):
            msg = (
                "Error: Only the bot owner is permitted "
                "to use the bot_delete_all_messages command."
            )
            log_event.error(msg)
            await ctx.send(msg)
            return

        count = 0
        async for msg in ctx.channel.history(limit=limit):
            try:
                await msg.delete()
            except discord.Forbidden:
                pass
            except discord.HTTPException as err:
                msg = "Unable to delete message: {err}".format(err=str(err))
                log_event.error(msg)
            else:
                count += 1
            finally:
                await asyncio.sleep(1.0)

        msg = "Deleted {count} messages.".format(count=count)
        log_event.info(msg)

    # -------------------------------------------------------------------------
    # Run the client.
    #
    #   Note: bot.run is a blocking call.
    #
    for idx_retry in itertools.count(start=1, step=1):
        try:
            bot.run(
                token=cfg_bot["str_token"],
                reconnect=True,
                log_handler=handler_log_event,
                log_level=level_log_event,
                root_logger=False,
            )

        except (
            discord.app_commands.MissingApplicationID,
            discord.Forbidden,
            discord.GatewayNotFound,
            discord.InvalidData,
            discord.LoginFailure,
            discord.NotFound,
            discord.PrivilegedIntentsRequired,
        ) as err:
            log_event.error("Fatal error: {err}".format(err=str(err)))
            _send_event_log_to_system(handler_log_event, queue_from_bot)
            break

        except Exception as err:
            log_event.error("Non-fatal error: {err}".format(err=str(err)))
            log_event.warning("Restarting. ({idx}).".format(idx=idx_retry))
            _send_event_log_to_system(handler_log_event, queue_from_bot)
            continue
