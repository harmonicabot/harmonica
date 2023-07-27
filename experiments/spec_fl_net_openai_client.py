import copy
import inspect
import logging
import time

import pytest


WORKFLOW_LOGIC = """

import itertools

def coro(cfg):

    list_out = [{template},{param}]

    for idx in itertools.count():

        if idx == 1:
            list_in = yield (list_out)
        else:
            list_in = yield ([])

"""

IS_ASYNC = False
TESTRUNNER_MAXITER = 100
TESTRUNNER_DELAY_SECS = 0.03


# -----------------------------------------------------------------------------
@pytest.fixture
def testvector_completions_valid_bit():
    """
    Return a valid template data structure for the completions endpoint.

    Sets the built-in-test flag to true so no
    actual call to the OpenAI server is made.

    """
    import fl.net.openai.client

    id_endpoint = "completions"
    uid_workflow = "e6150ce3-8ebc-4553-9a9a-b1ebdc038f7e"
    uid_template = "e2cb431c-a709-4e7e-a9d1-dfb51d8dc4e2"
    uid_variant = "5b8c0cfb-b4fb-4d9a-a839-4eef8bdd36d3"
    uid_params = "de678e1f-bc1b-402a-bfe8-d2705cb9a5ce"
    id_model = "text-davinci-003"
    prompt_test = "completions_test_prompt_text"

    cfg_valid = {
        "api_key": "test_api_key",
        "secs_interval": 0.01,
        "is_bit": True,
        "is_async": IS_ASYNC,
        "default": {"id_endpoint": id_endpoint, "model": id_model},
        "id_system": "test",
        "id_node": "openai-client",
        "level_log": logging.INFO,
    }

    template_valid = {
        "id_endpoint": id_endpoint,
        "type": {"id": "prompt_template", "ver": "1.0"},
        "uid_variant": uid_variant,  # Improvement.
        "uid_template": uid_template,  # Process step.
        "uid_workflow": uid_workflow,  # Process id.
        "kwargs_req": {"model": id_model},
        "prompt": prompt_test,
    }

    param_valid = {
        "type": {"id": "prompt_params", "ver": "1.0"},
        "uid_params": uid_params,
        "uid_template": uid_template,
        "uid_workflow": uid_workflow,
        "kwargs_tmpl": dict(),  # <-- Args for template
        "kwargs_req": dict(),  # <-- Args for OpenAI request
        "state": dict(),
    }  # <-- Process state

    workflow_valid = {
        "uid_workflow": uid_workflow,
        "type": {"id": "prompt_workflow", "ver": "1.0"},
        "spec": WORKFLOW_LOGIC.format(template=template_valid, param=param_valid),
        "coroutine": None,
    }

    request_valid = {"model": id_model, "prompt": prompt_test}

    output_valid = [
        {
            "type": "openai_result",
            "error": None,
            "request": copy.deepcopy(request_valid),
            "response": fl.net.openai.client.built_in_test_response(id_endpoint),
            "state": {},
        }
    ]

    return (
        cfg_valid,
        workflow_valid,
        template_valid,
        param_valid,
        request_valid,
        output_valid,
    )


# -----------------------------------------------------------------------------
@pytest.fixture
def testvector_chat_completions_valid_bit():
    """
    Return a valid template data structure for the chat completions endpoint.

    Sets the built-in-test flag to true so no
    actual call to the OpenAI server is made.

    """
    import fl.net.openai.client

    id_endpoint = "chat_completions"
    uid_workflow = "e6150ce3-8ebc-4553-9a9a-b1ebdc038f7e"
    uid_template = "e2cb431c-a709-4e7e-a9d1-dfb51d8dc4e2"
    uid_variant = "5b8c0cfb-b4fb-4d9a-a839-4eef8bdd36d3"
    uid_params = "de678e1f-bc1b-402a-bfe8-d2705cb9a5ce"
    id_model = "gpt-3.5-turbo-0301"
    messages_test = [{"role": "system", "content": "chat_completions_test_msg_content"}]

    cfg_valid = {
        "api_key": "test_api_key",
        "secs_interval": 0.01,
        "is_bit": True,
        "is_async": IS_ASYNC,
        "default": {"id_endpoint": id_endpoint, "model": id_model},
        "id_system": "test",
        "id_node": "openai-client",
        "level_log": logging.INFO,
    }

    template_valid = {
        "id_endpoint": id_endpoint,
        "type": {"id": "prompt_template", "ver": "1.0"},
        "uid_variant": uid_variant,  # Improvement.
        "uid_template": uid_template,  # Process step.
        "uid_workflow": uid_workflow,  # Process id.
        "kwargs_req": {"model": id_model},
        "messages": messages_test,
    }

    param_valid = {
        "type": {"id": "prompt_params", "ver": "1.0"},
        "uid_params": uid_params,
        "uid_template": uid_template,
        "uid_workflow": uid_workflow,
        "kwargs_tmpl": dict(),  # <-- Args for template
        "kwargs_req": dict(),  # <-- Args for OpenAI request
        "state": dict(),
    }  # <-- Process state

    workflow_valid = {
        "uid_workflow": uid_workflow,
        "type": {"id": "prompt_workflow", "ver": "1.0"},
        "spec": WORKFLOW_LOGIC.format(template=template_valid, param=param_valid),
        "coroutine": None,
    }

    request_valid = {"model": id_model, "messages": messages_test}

    output_valid = [
        {
            "type": "openai_result",
            "error": None,
            "request": copy.deepcopy(request_valid),
            "response": fl.net.openai.client.built_in_test_response(id_endpoint),
            "state": {},
        }
    ]

    return (
        cfg_valid,
        workflow_valid,
        template_valid,
        param_valid,
        request_valid,
        output_valid,
    )


# -----------------------------------------------------------------------------
@pytest.fixture
def testvector_edits_valid_bit():
    """
    Return a valid template data structure for the edits endpoint.

    Sets the built-in-test flag to true so no
    actual call to the OpenAI server is made.

    """
    import fl.net.openai.client

    id_endpoint = "edits"
    uid_workflow = "e6150ce3-8ebc-4553-9a9a-b1ebdc038f7e"
    uid_template = "e2cb431c-a709-4e7e-a9d1-dfb51d8dc4e2"
    uid_variant = "5b8c0cfb-b4fb-4d9a-a839-4eef8bdd36d3"
    uid_params = "de678e1f-bc1b-402a-bfe8-d2705cb9a5ce"
    id_model = "text-davinci-edit-001"
    input_test = "edits_test_input_text"
    instruction_test = "edits_test_instruction_text"

    cfg_valid = {
        "api_key": "test_api_key",
        "secs_interval": 0.01,
        "is_bit": True,
        "is_async": IS_ASYNC,
        "default": {"id_endpoint": id_endpoint, "model": id_model},
        "id_system": "test",
        "id_node": "openai-client",
        "level_log": logging.INFO,
    }

    template_valid = {
        "id_endpoint": id_endpoint,
        "type": {"id": "prompt_template", "ver": "1.0"},
        "uid_variant": uid_variant,  # Improvement.
        "uid_template": uid_template,  # Process step.
        "uid_workflow": uid_workflow,  # Process id.
        "kwargs_req": {"model": id_model},
        "input": input_test,
        "instruction": instruction_test,
    }

    param_valid = {
        "type": {"id": "prompt_params", "ver": "1.0"},
        "uid_params": uid_params,
        "uid_template": uid_template,
        "uid_workflow": uid_workflow,
        "kwargs_tmpl": dict(),  # <-- Args for template
        "kwargs_req": dict(),  # <-- Args for OpenAI request
        "state": dict(),
    }  # <-- Process state

    workflow_valid = {
        "uid_workflow": uid_workflow,
        "type": {"id": "prompt_workflow", "ver": "1.0"},
        "spec": WORKFLOW_LOGIC.format(template=template_valid, param=param_valid),
        "coroutine": None,
    }

    request_valid = {
        "model": id_model,
        "input": input_test,
        "instruction": instruction_test,
    }

    output_valid = [
        {
            "type": "openai_result",
            "error": None,
            "request": copy.deepcopy(request_valid),
            "response": fl.net.openai.client.built_in_test_response(id_endpoint),
            "state": {},
        }
    ]

    return (
        cfg_valid,
        workflow_valid,
        template_valid,
        param_valid,
        request_valid,
        output_valid,
    )


# -----------------------------------------------------------------------------
@pytest.fixture
def testvector_images_generations_valid_bit():
    """
    Return a valid template data structure for the images_generations endpoint.

    Sets the built-in-test flag to true so no
    actual call to the OpenAI server is made.

    """
    import fl.net.openai.client

    id_endpoint = "images_generations"
    uid_workflow = "e6150ce3-8ebc-4553-9a9a-b1ebdc038f7e"
    uid_template = "e2cb431c-a709-4e7e-a9d1-dfb51d8dc4e2"
    uid_variant = "5b8c0cfb-b4fb-4d9a-a839-4eef8bdd36d3"
    uid_params = "de678e1f-bc1b-402a-bfe8-d2705cb9a5ce"
    prompt_test = "images_generations_test_prompt_text"

    cfg_valid = {
        "api_key": "test_api_key",
        "secs_interval": 0.01,
        "is_bit": True,
        "is_async": IS_ASYNC,
        "default": {"id_endpoint": id_endpoint},
        "id_system": "test",
        "id_node": "openai-client",
        "level_log": logging.INFO,
    }

    template_valid = {
        "id_endpoint": id_endpoint,
        "type": {"id": "prompt_template", "ver": "1.0"},
        "uid_variant": uid_variant,  # Improvement.
        "uid_template": uid_template,  # Process step.
        "uid_workflow": uid_workflow,  # Process id.
        "kwargs_req": {},
        "prompt": prompt_test,
    }

    param_valid = {
        "type": {"id": "prompt_params", "ver": "1.0"},
        "uid_params": uid_params,
        "uid_template": uid_template,
        "uid_workflow": uid_workflow,
        "kwargs_tmpl": dict(),  # <-- Args for template
        "kwargs_req": dict(),  # <-- Args for OpenAI request
        "state": dict(),
    }  # <-- Process state

    workflow_valid = {
        "uid_workflow": uid_workflow,
        "type": {"id": "prompt_workflow", "ver": "1.0"},
        "spec": WORKFLOW_LOGIC.format(template=template_valid, param=param_valid),
        "coroutine": None,
    }

    request_valid = {"prompt": prompt_test}

    output_valid = [
        {
            "type": "openai_result",
            "error": None,
            "request": copy.deepcopy(request_valid),
            "response": fl.net.openai.client.built_in_test_response(id_endpoint),
            "state": {},
        }
    ]

    return (
        cfg_valid,
        workflow_valid,
        template_valid,
        param_valid,
        request_valid,
        output_valid,
    )


# -----------------------------------------------------------------------------
@pytest.fixture
def testvector_images_edits_valid_bit():
    """
    Return a valid template data structure for the images_edits endpoint.

    Sets the built-in-test flag to true so no
    actual call to the OpenAI server is made.

    """
    import fl.net.openai.client

    id_endpoint = "images_edits"
    uid_workflow = "e6150ce3-8ebc-4553-9a9a-b1ebdc038f7e"
    uid_template = "e2cb431c-a709-4e7e-a9d1-dfb51d8dc4e2"
    uid_variant = "5b8c0cfb-b4fb-4d9a-a839-4eef8bdd36d3"
    uid_params = "de678e1f-bc1b-402a-bfe8-d2705cb9a5ce"
    image_test = "images_edits_test_image_data"
    prompt_test = "images_edits_test_prompt_text"

    cfg_valid = {
        "api_key": "test_api_key",
        "secs_interval": 0.01,
        "is_bit": True,
        "is_async": IS_ASYNC,
        "default": {"id_endpoint": id_endpoint},
        "id_system": "test",
        "id_node": "openai-client",
        "level_log": logging.INFO,
    }

    template_valid = {
        "id_endpoint": id_endpoint,
        "type": {"id": "prompt_template", "ver": "1.0"},
        "uid_variant": uid_variant,  # Improvement.
        "uid_template": uid_template,  # Process step.
        "uid_workflow": uid_workflow,  # Process id.
        "kwargs_req": {"image": image_test},
        "prompt": prompt_test,
    }

    param_valid = {
        "type": {"id": "prompt_params", "ver": "1.0"},
        "uid_params": uid_params,
        "uid_template": uid_template,
        "uid_workflow": uid_workflow,
        "kwargs_tmpl": dict(),  # <-- Args for template
        "kwargs_req": dict(),  # <-- Args for OpenAI request
        "state": dict(),
    }  # <-- Process state

    workflow_valid = {
        "uid_workflow": uid_workflow,
        "type": {"id": "prompt_workflow", "ver": "1.0"},
        "spec": WORKFLOW_LOGIC.format(template=template_valid, param=param_valid),
        "coroutine": None,
    }

    request_valid = {"image": image_test, "prompt": prompt_test}

    output_valid = [
        {
            "type": "openai_result",
            "error": None,
            "request": copy.deepcopy(request_valid),
            "response": fl.net.openai.client.built_in_test_response(id_endpoint),
            "state": {},
        }
    ]

    return (
        cfg_valid,
        workflow_valid,
        template_valid,
        param_valid,
        request_valid,
        output_valid,
    )


# -----------------------------------------------------------------------------
@pytest.fixture
def testvector_images_variations_valid_bit():
    """
    Return a valid template data structure for the images_variations endpoint.

    Sets the built-in-test flag to true so no
    actual call to the OpenAI server is made.

    """
    import fl.net.openai.client

    id_endpoint = "images_variations"
    uid_workflow = "e6150ce3-8ebc-4553-9a9a-b1ebdc038f7e"
    uid_template = "e2cb431c-a709-4e7e-a9d1-dfb51d8dc4e2"
    uid_variant = "5b8c0cfb-b4fb-4d9a-a839-4eef8bdd36d3"
    uid_params = "de678e1f-bc1b-402a-bfe8-d2705cb9a5ce"
    image_test = "images_variations_test_image_data"

    cfg_valid = {
        "api_key": "test_api_key",
        "secs_interval": 0.01,
        "is_bit": True,
        "is_async": IS_ASYNC,
        "default": {"id_endpoint": id_endpoint},
        "id_system": "test",
        "id_node": "openai-client",
        "level_log": logging.INFO,
    }

    template_valid = {
        "id_endpoint": id_endpoint,
        "type": {"id": "prompt_template", "ver": "1.0"},
        "uid_variant": uid_variant,  # Improvement.
        "uid_template": uid_template,  # Process step.
        "uid_workflow": uid_workflow,  # Process id.
        "kwargs_req": {"image": image_test},
    }

    param_valid = {
        "type": {"id": "prompt_params", "ver": "1.0"},
        "uid_params": uid_params,
        "uid_template": uid_template,
        "uid_workflow": uid_workflow,
        "kwargs_tmpl": dict(),  # <-- Args for template
        "kwargs_req": dict(),  # <-- Args for OpenAI request
        "state": dict(),
    }  # <-- Process state

    workflow_valid = {
        "uid_workflow": uid_workflow,
        "type": {"id": "prompt_workflow", "ver": "1.0"},
        "spec": WORKFLOW_LOGIC.format(template=template_valid, param=param_valid),
        "coroutine": None,
    }

    request_valid = {"image": image_test}

    output_valid = [
        {
            "type": "openai_result",
            "error": None,
            "request": copy.deepcopy(request_valid),
            "response": fl.net.openai.client.built_in_test_response(id_endpoint),
            "state": {},
        }
    ]

    return (
        cfg_valid,
        workflow_valid,
        template_valid,
        param_valid,
        request_valid,
        output_valid,
    )


# -----------------------------------------------------------------------------
@pytest.fixture
def testvector_embeddings_valid_bit():
    """
    Return a valid template data structure for the embeddings endpoint.

    Sets the built-in-test flag to true so no
    actual call to the OpenAI server is made.

    """
    import fl.net.openai.client

    id_endpoint = "embeddings"
    uid_workflow = "e6150ce3-8ebc-4553-9a9a-b1ebdc038f7e"
    uid_template = "e2cb431c-a709-4e7e-a9d1-dfb51d8dc4e2"
    uid_variant = "5b8c0cfb-b4fb-4d9a-a839-4eef8bdd36d3"
    uid_params = "de678e1f-bc1b-402a-bfe8-d2705cb9a5ce"
    id_model = "text-embedding-ada-002"
    input_test = "embeddings_test_input_text"

    cfg_valid = {
        "api_key": "test_api_key",
        "secs_interval": 0.01,
        "is_bit": True,
        "is_async": IS_ASYNC,
        "default": {"id_endpoint": id_endpoint, "model": id_model},
        "id_system": "test",
        "id_node": "openai-client",
        "level_log": logging.INFO,
    }

    template_valid = {
        "id_endpoint": id_endpoint,
        "type": {"id": "prompt_template", "ver": "1.0"},
        "uid_variant": uid_variant,  # Improvement.
        "uid_template": uid_template,  # Process step.
        "uid_workflow": uid_workflow,  # Process id.
        "kwargs_req": {"model": id_model},
        "input": input_test,
    }

    param_valid = {
        "type": {"id": "prompt_params", "ver": "1.0"},
        "uid_params": uid_params,
        "uid_template": uid_template,
        "uid_workflow": uid_workflow,
        "kwargs_tmpl": dict(),  # <-- Args for template
        "kwargs_req": dict(),  # <-- Args for OpenAI request
        "state": dict(),
    }  # <-- Process state

    workflow_valid = {
        "uid_workflow": uid_workflow,
        "type": {"id": "prompt_workflow", "ver": "1.0"},
        "spec": WORKFLOW_LOGIC.format(template=template_valid, param=param_valid),
        "coroutine": None,
    }

    request_valid = {"model": id_model, "input": input_test}

    output_valid = [
        {
            "type": "openai_result",
            "error": None,
            "request": copy.deepcopy(request_valid),
            "response": fl.net.openai.client.built_in_test_response(id_endpoint),
            "state": {},
        }
    ]

    return (
        cfg_valid,
        workflow_valid,
        template_valid,
        param_valid,
        request_valid,
        output_valid,
    )


# -----------------------------------------------------------------------------
@pytest.fixture
def testvector_audio_transcriptions_valid_bit():
    """
    Return valid template data structure for the audio_transcriptions endpoint.

    Sets the built-in-test flag to true so no
    actual call to the OpenAI server is made.

    """
    import fl.net.openai.client

    id_endpoint = "audio_transcriptions"
    uid_workflow = "e6150ce3-8ebc-4553-9a9a-b1ebdc038f7e"
    uid_template = "e2cb431c-a709-4e7e-a9d1-dfb51d8dc4e2"
    uid_variant = "5b8c0cfb-b4fb-4d9a-a839-4eef8bdd36d3"
    uid_params = "de678e1f-bc1b-402a-bfe8-d2705cb9a5ce"
    id_model = "whisper-1"
    audio_file_test = "audio_transcriptions_test_audio_file_data"
    prompt_test = "audio_transcriptions_test_prompt_text"

    cfg_valid = {
        "api_key": "test_api_key",
        "secs_interval": 0.01,
        "is_bit": True,
        "is_async": IS_ASYNC,
        "default": {"id_endpoint": id_endpoint, "model": id_model},
        "id_system": "test",
        "id_node": "openai-client",
        "level_log": logging.INFO,
    }

    template_valid = {
        "id_endpoint": id_endpoint,
        "type": {"id": "prompt_template", "ver": "1.0"},
        "uid_variant": uid_variant,  # Improvement.
        "uid_template": uid_template,  # Process step.
        "uid_workflow": uid_workflow,  # Process id.
        "kwargs_req": {"file": audio_file_test, "model": id_model},
        "prompt": prompt_test,
    }

    param_valid = {
        "type": {"id": "prompt_params", "ver": "1.0"},
        "uid_params": uid_params,
        "uid_template": uid_template,
        "uid_workflow": uid_workflow,
        "kwargs_tmpl": dict(),  # <-- Args for template
        "kwargs_req": dict(),  # <-- Args for OpenAI request
        "state": dict(),
    }  # <-- Process state

    workflow_valid = {
        "uid_workflow": uid_workflow,
        "type": {"id": "prompt_workflow", "ver": "1.0"},
        "spec": WORKFLOW_LOGIC.format(template=template_valid, param=param_valid),
        "coroutine": None,
    }

    request_valid = {"file": audio_file_test, "model": id_model, "prompt": prompt_test}

    output_valid = [
        {
            "type": "openai_result",
            "error": None,
            "request": copy.deepcopy(request_valid),
            "response": fl.net.openai.client.built_in_test_response(id_endpoint),
            "state": {},
        }
    ]

    return (
        cfg_valid,
        workflow_valid,
        template_valid,
        param_valid,
        request_valid,
        output_valid,
    )


# -----------------------------------------------------------------------------
@pytest.fixture
def testvector_audio_translations_valid_bit():
    """
    Return a valid template data structure for the audio_translations endpoint.

    Sets the built-in-test flag to true so no
    actual call to the OpenAI server is made.

    """
    import fl.net.openai.client

    id_endpoint = "audio_translations"
    uid_workflow = "e6150ce3-8ebc-4553-9a9a-b1ebdc038f7e"
    uid_template = "e2cb431c-a709-4e7e-a9d1-dfb51d8dc4e2"
    uid_variant = "5b8c0cfb-b4fb-4d9a-a839-4eef8bdd36d3"
    uid_params = "de678e1f-bc1b-402a-bfe8-d2705cb9a5ce"
    id_model = "whisper-1"
    audio_file_test = "audio_translations_test_audio_file_data"
    prompt_test = "audio_translations_test_prompt_text"

    cfg_valid = {
        "api_key": "test_api_key",
        "secs_interval": 0.01,
        "is_bit": True,
        "is_async": IS_ASYNC,
        "default": {"id_endpoint": id_endpoint, "model": id_model},
        "id_system": "test",
        "id_node": "openai-client",
        "level_log": logging.INFO,
    }

    template_valid = {
        "id_endpoint": id_endpoint,
        "type": {"id": "prompt_template", "ver": "1.0"},
        "uid_variant": uid_variant,  # Improvement.
        "uid_template": uid_template,  # Process step.
        "uid_workflow": uid_workflow,  # Process id.
        "kwargs_req": {"file": audio_file_test, "model": id_model},
        "prompt": prompt_test,
    }

    param_valid = {
        "type": {"id": "prompt_params", "ver": "1.0"},
        "uid_params": uid_params,
        "uid_template": uid_template,
        "uid_workflow": uid_workflow,
        "kwargs_tmpl": dict(),  # <-- Args for template
        "kwargs_req": dict(),  # <-- Args for OpenAI request
        "state": dict(),
    }  # <-- Process state

    workflow_valid = {
        "type": {"id": "prompt_workflow", "ver": "1.0"},
        "uid_workflow": uid_workflow,
        "spec": WORKFLOW_LOGIC.format(template=template_valid, param=param_valid),
        "coroutine": None,
    }

    request_valid = {"file": audio_file_test, "model": id_model, "prompt": prompt_test}

    output_valid = [
        {
            "type": "openai_result",
            "error": None,
            "request": copy.deepcopy(request_valid),
            "response": fl.net.openai.client.built_in_test_response(id_endpoint),
            "state": {},
        }
    ]

    return (
        cfg_valid,
        workflow_valid,
        template_valid,
        param_valid,
        request_valid,
        output_valid,
    )


# -----------------------------------------------------------------------------
@pytest.fixture
def testrunner_coro_request_handler_singleshot():
    """
    Return a single-shot test runner fixture for coro_request_handler.

    """

    # -------------------------------------------------------------------------
    def _get_result_singleshot(
        cfg,
        list_list_input,
        maxiter=TESTRUNNER_MAXITER,
        delay_secs=TESTRUNNER_DELAY_SECS,
    ):
        """
        Run the openAI client and wait for the first set of responses.

        """
        import fl.net.openai.client

        unix_time = 0
        client = fl.net.openai.client.coro_request_handler(cfg=cfg)

        for _ in range(maxiter):
            if list_list_input:
                list_input = list_list_input.pop()
            else:
                list_input = []

            (list_output) = client.send((list_input, unix_time))
            if len(list_output) > 0:
                return list_output

            time.sleep(delay_secs)

        return []

    return _get_result_singleshot


# -----------------------------------------------------------------------------
@pytest.fixture
def testrunner_coro_template_handler_singleshot():
    """
    Return a single-shot test runner fixture for coro_template_handler.

    """

    # -------------------------------------------------------------------------
    def _get_result_singleshot(
        cfg,
        list_list_input,
        maxiter=TESTRUNNER_MAXITER,
        delay_secs=TESTRUNNER_DELAY_SECS,
    ):
        """
        Run the openAI client and wait for the first set of responses.

        """
        import fl.net.openai.client

        unix_time = 0
        request_handler = fl.net.openai.client.coro_request_handler(cfg=cfg)
        template_handler = fl.net.openai.client.coro_template_handler(
            cfg=cfg, request_handler=request_handler
        )

        for _ in range(maxiter):
            if list_list_input:
                list_input = list_list_input.pop()
            else:
                list_input = []

            list_output = template_handler.send((list_input, unix_time))
            if len(list_output) > 0:
                return list_output

            time.sleep(delay_secs)

        return []

    return _get_result_singleshot


# -----------------------------------------------------------------------------
@pytest.fixture
def testrunner_coro_workflow_handler_singleshot():
    """
    Return a single-shot test runner fixture for coro_workflow_handler.

    """

    # -------------------------------------------------------------------------
    def _get_result_singleshot(
        cfg,
        list_list_input,
        maxiter=TESTRUNNER_MAXITER,
        delay_secs=TESTRUNNER_DELAY_SECS,
    ):
        """
        Run the openAI client and wait for the first set of responses.

        """
        import fl.net.openai.client

        unix_time = 0
        request_handler = fl.net.openai.client.coro_request_handler(cfg=cfg)
        template_handler = fl.net.openai.client.coro_template_handler(
            cfg=cfg, request_handler=request_handler
        )
        workflow_handler = fl.net.openai.client.coro_workflow_handler(
            cfg=cfg, request_handler=request_handler, template_handler=template_handler
        )

        for _ in range(maxiter):
            if list_list_input:
                list_input = list_list_input.pop()
            else:
                list_input = []

            list_output = workflow_handler.send((list_input, unix_time))
            if len(list_output) > 0:
                return list_output

            time.sleep(delay_secs)

        return []

    return _get_result_singleshot


# =============================================================================
class SpecifyFlNetOpenAiClient:
    """
    Spec for the fl.net.openai.client package.

    """

    # -------------------------------------------------------------------------
    @pytest.mark.e002_general_research
    @pytest.mark.e003_discord
    def it_supports_import_of_fl_net_openai_client(self):
        """
        fl.net.openai.client can be imported.

        """
        import fl.net.openai.client

    # -------------------------------------------------------------------------
    @pytest.mark.e002_general_research
    @pytest.mark.e003_discord
    def it_supports_creation_of_the_request_handler_coroutine(
        self, testvector_completions_valid_bit
    ):
        """
        fl.net.openai.client coro_request_handler() can be created.

        """
        import fl.net.openai.client

        tup_valid = testvector_completions_valid_bit
        cfg_valid = tup_valid[0]
        request_handler = fl.net.openai.client.coro_request_handler(cfg=cfg_valid)
        assert inspect.isgenerator(request_handler)

    # -------------------------------------------------------------------------
    @pytest.mark.e002_general_research
    @pytest.mark.e003_discord
    def it_supports_creation_of_the_template_handler_coroutine(
        self, testvector_completions_valid_bit
    ):
        """
        fl.net.openai.client coro_template_handler() can be created.

        """
        import fl.net.openai.client

        tup_valid = testvector_completions_valid_bit
        cfg_valid = tup_valid[0]
        request_handler = fl.net.openai.client.coro_request_handler(cfg=cfg_valid)
        template_handler = fl.net.openai.client.coro_template_handler(
            cfg=cfg_valid, request_handler=request_handler
        )
        assert inspect.isgenerator(template_handler)

    # -------------------------------------------------------------------------
    @pytest.mark.e002_general_research
    @pytest.mark.e003_discord
    def it_supports_creation_of_the_workflow_handler_coroutine(
        self, testvector_completions_valid_bit
    ):
        """
        fl.net.openai.client coro_workflow_handler() can be created.

        """
        import fl.net.openai.client

        tup_valid = testvector_completions_valid_bit
        cfg_valid = tup_valid[0]
        request_handler = fl.net.openai.client.coro_request_handler(cfg=cfg_valid)
        template_handler = fl.net.openai.client.coro_template_handler(
            cfg=cfg_valid, request_handler=request_handler
        )
        workflow_handler = fl.net.openai.client.coro_workflow_handler(
            cfg=cfg_valid,
            request_handler=request_handler,
            template_handler=template_handler,
        )
        assert inspect.isgenerator(workflow_handler)

    # -------------------------------------------------------------------------
    @pytest.mark.e002_general_research
    @pytest.mark.e003_discord
    def it_validates_provided_configuration(self):
        """
        All fl.net.openai.client.coro_request_handler validates config.

        """
        import fl.net.openai.client

        with pytest.raises(RuntimeError):
            fl.net.openai.client.coro_request_handler(cfg={})

    # -------------------------------------------------------------------------
    @pytest.mark.e002_general_research
    @pytest.mark.e003_discord
    def it_yields_expected_bit_response_for_valid_completions_input(
        self,
        testvector_completions_valid_bit,
        testrunner_coro_workflow_handler_singleshot,
        testrunner_coro_template_handler_singleshot,
        testrunner_coro_request_handler_singleshot,
    ):
        """
        When valid completions input sent, valid bit output yielded.

        """
        (
            cfg_valid,
            workflow_valid,
            template_valid,
            param_valid,
            request_valid,
            list_output_expected,
        ) = testvector_completions_valid_bit

        # Check that the low-level request
        # handler coroutine also works when
        # given valid input.
        #
        list_output_1 = testrunner_coro_request_handler_singleshot(
            cfg=cfg_valid, list_list_input=[[request_valid]]
        )
        assert list_output_1 == list_output_expected

        # Check that the mid-level string and
        # template handler coroutine works when
        # given valid input.
        #
        list_output_2 = testrunner_coro_template_handler_singleshot(
            cfg=cfg_valid, list_list_input=[[template_valid, param_valid]]
        )
        assert list_output_2 == list_output_expected

        # Check that the high-level workflow
        # handler coroutine works when given
        # valid input.
        #
        list_output_3 = testrunner_coro_workflow_handler_singleshot(
            cfg=cfg_valid, list_list_input=[[workflow_valid, param_valid]]
        )
        assert list_output_3 == list_output_expected

    # -------------------------------------------------------------------------
    @pytest.mark.e002_general_research
    @pytest.mark.e003_discord
    def it_yields_expected_bit_response_for_valid_chat_completions_input(
        self,
        testvector_chat_completions_valid_bit,
        testrunner_coro_workflow_handler_singleshot,
        testrunner_coro_template_handler_singleshot,
        testrunner_coro_request_handler_singleshot,
    ):
        """
        When valid chat_completions input sent, valid bit output yielded.

        """
        (
            cfg_valid,
            workflow_valid,
            template_valid,
            param_valid,
            request_valid,
            list_output_expected,
        ) = testvector_chat_completions_valid_bit

        # Check that the low-level request
        # handler coroutine also works when
        # given valid input.
        #
        list_output_1 = testrunner_coro_request_handler_singleshot(
            cfg=cfg_valid, list_list_input=[[request_valid]]
        )
        assert list_output_1 == list_output_expected

        # Check that the mid-level string and
        # template handler coroutine works when
        # given valid input.
        #
        list_output_2 = testrunner_coro_template_handler_singleshot(
            cfg=cfg_valid, list_list_input=[[template_valid, param_valid]]
        )
        assert list_output_2 == list_output_expected

        # Check that the high-level workflow
        # handler coroutine works when given
        # valid input.
        #
        list_output_3 = testrunner_coro_workflow_handler_singleshot(
            cfg=cfg_valid, list_list_input=[[workflow_valid, param_valid]]
        )
        assert list_output_3 == list_output_expected

    # -------------------------------------------------------------------------
    @pytest.mark.e002_general_research
    @pytest.mark.e003_discord
    def it_yields_expected_bit_response_for_valid_edits_input(
        self,
        testvector_edits_valid_bit,
        testrunner_coro_workflow_handler_singleshot,
        testrunner_coro_template_handler_singleshot,
        testrunner_coro_request_handler_singleshot,
    ):
        """
        When valid edits input sent, valid bit output yielded.

        """
        (
            cfg_valid,
            workflow_valid,
            template_valid,
            param_valid,
            request_valid,
            list_output_expected,
        ) = testvector_edits_valid_bit

        # Check that the low-level request
        # handler coroutine also works when
        # given valid input.
        #
        list_output_1 = testrunner_coro_request_handler_singleshot(
            cfg=cfg_valid, list_list_input=[[request_valid]]
        )
        assert list_output_1 == list_output_expected

        # Check that the mid-level string and
        # template handler coroutine works when
        # given valid input.
        #
        list_output_2 = testrunner_coro_template_handler_singleshot(
            cfg=cfg_valid, list_list_input=[[template_valid, param_valid]]
        )
        assert list_output_2 == list_output_expected

        # Check that the high-level workflow
        # handler coroutine works when given
        # valid input.
        #
        list_output_3 = testrunner_coro_workflow_handler_singleshot(
            cfg=cfg_valid, list_list_input=[[workflow_valid, param_valid]]
        )
        assert list_output_3 == list_output_expected

    # -------------------------------------------------------------------------
    @pytest.mark.e002_general_research
    @pytest.mark.e003_discord
    def it_yields_expected_bit_response_for_valid_images_generations_input(
        self,
        testvector_images_generations_valid_bit,
        testrunner_coro_workflow_handler_singleshot,
        testrunner_coro_template_handler_singleshot,
        testrunner_coro_request_handler_singleshot,
    ):
        """
        When valid images_generations input sent, valid bit output yielded.

        """
        (
            cfg_valid,
            workflow_valid,
            template_valid,
            param_valid,
            request_valid,
            list_output_expected,
        ) = testvector_images_generations_valid_bit

        # Check that the low-level request
        # handler coroutine also works when
        # given valid input.
        #
        list_output_1 = testrunner_coro_request_handler_singleshot(
            cfg=cfg_valid, list_list_input=[[request_valid]]
        )
        assert list_output_1 == list_output_expected

        # Check that the mid-level string and
        # template handler coroutine works when
        # given valid input.
        #
        list_output_2 = testrunner_coro_template_handler_singleshot(
            cfg=cfg_valid, list_list_input=[[template_valid, param_valid]]
        )
        assert list_output_2 == list_output_expected

        # Check that the high-level workflow
        # handler coroutine works when given
        # valid input.
        #
        list_output_3 = testrunner_coro_workflow_handler_singleshot(
            cfg=cfg_valid, list_list_input=[[workflow_valid, param_valid]]
        )
        assert list_output_3 == list_output_expected

    # -------------------------------------------------------------------------
    @pytest.mark.e002_general_research
    @pytest.mark.e003_discord
    def it_yields_expected_bit_response_for_valid_images_edits_input(
        self,
        testvector_images_edits_valid_bit,
        testrunner_coro_workflow_handler_singleshot,
        testrunner_coro_template_handler_singleshot,
        testrunner_coro_request_handler_singleshot,
    ):
        """
        When valid images_edits input sent, valid bit output yielded.

        """
        (
            cfg_valid,
            workflow_valid,
            template_valid,
            param_valid,
            request_valid,
            list_output_expected,
        ) = testvector_images_edits_valid_bit

        # Check that the low-level request
        # handler coroutine also works when
        # given valid input.
        #
        list_output_1 = testrunner_coro_request_handler_singleshot(
            cfg=cfg_valid, list_list_input=[[request_valid]]
        )
        assert list_output_1 == list_output_expected

        # Check that the mid-level string and
        # template handler coroutine works when
        # given valid input.
        #
        list_output_2 = testrunner_coro_template_handler_singleshot(
            cfg=cfg_valid, list_list_input=[[template_valid, param_valid]]
        )
        assert list_output_2 == list_output_expected

        # Check that the high-level workflow
        # handler coroutine works when given
        # valid input.
        #
        list_output_3 = testrunner_coro_workflow_handler_singleshot(
            cfg=cfg_valid, list_list_input=[[workflow_valid, param_valid]]
        )
        assert list_output_3 == list_output_expected

    # -------------------------------------------------------------------------
    @pytest.mark.e002_general_research
    @pytest.mark.e003_discord
    def it_yields_expected_bit_response_for_valid_images_variations_input(
        self,
        testvector_images_variations_valid_bit,
        testrunner_coro_workflow_handler_singleshot,
        testrunner_coro_template_handler_singleshot,
        testrunner_coro_request_handler_singleshot,
    ):
        """
        When valid images_variations input sent, valid bit output yielded.

        """
        (
            cfg_valid,
            workflow_valid,
            template_valid,
            param_valid,
            request_valid,
            list_output_expected,
        ) = testvector_images_variations_valid_bit

        # Check that the low-level request
        # handler coroutine also works when
        # given valid input.
        #
        list_output_1 = testrunner_coro_request_handler_singleshot(
            cfg=cfg_valid, list_list_input=[[request_valid]]
        )
        assert list_output_1 == list_output_expected

        # Check that the mid-level string and
        # template handler coroutine works when
        # given valid input.
        #
        list_output_2 = testrunner_coro_template_handler_singleshot(
            cfg=cfg_valid, list_list_input=[[template_valid, param_valid]]
        )
        assert list_output_2 == list_output_expected

        # Check that the high-level workflow
        # handler coroutine works when given
        # valid input.
        #
        list_output_3 = testrunner_coro_workflow_handler_singleshot(
            cfg=cfg_valid, list_list_input=[[workflow_valid, param_valid]]
        )
        assert list_output_3 == list_output_expected

    # -------------------------------------------------------------------------
    @pytest.mark.e002_general_research
    @pytest.mark.e003_discord
    def it_yields_expected_bit_response_for_valid_embeddings_input(
        self,
        testvector_embeddings_valid_bit,
        testrunner_coro_workflow_handler_singleshot,
        testrunner_coro_template_handler_singleshot,
        testrunner_coro_request_handler_singleshot,
    ):
        """
        When valid embeddings input sent, valid bit output yielded.

        """
        (
            cfg_valid,
            workflow_valid,
            template_valid,
            param_valid,
            request_valid,
            list_output_expected,
        ) = testvector_embeddings_valid_bit

        # Check that the low-level request
        # handler coroutine also works when
        # given valid input.
        #
        list_output_1 = testrunner_coro_request_handler_singleshot(
            cfg=cfg_valid, list_list_input=[[request_valid]]
        )
        assert list_output_1 == list_output_expected

        # Check that the mid-level string and
        # template handler coroutine works when
        # given valid input.
        #
        list_output_2 = testrunner_coro_template_handler_singleshot(
            cfg=cfg_valid, list_list_input=[[template_valid, param_valid]]
        )
        assert list_output_2 == list_output_expected

        # Check that the high-level workflow
        # handler coroutine works when given
        # valid input.
        #
        list_output_3 = testrunner_coro_workflow_handler_singleshot(
            cfg=cfg_valid, list_list_input=[[workflow_valid, param_valid]]
        )
        assert list_output_3 == list_output_expected

    # -------------------------------------------------------------------------
    @pytest.mark.e002_general_research
    @pytest.mark.e003_discord
    def it_yields_expected_bit_response_for_valid_audio_transcriptions_input(
        self,
        testvector_audio_transcriptions_valid_bit,
        testrunner_coro_workflow_handler_singleshot,
        testrunner_coro_template_handler_singleshot,
        testrunner_coro_request_handler_singleshot,
    ):
        """
        When valid audio_transcriptions input sent, valid bit output yielded.

        """
        (
            cfg_valid,
            workflow_valid,
            template_valid,
            param_valid,
            request_valid,
            list_output_expected,
        ) = testvector_audio_transcriptions_valid_bit

        # Check that the low-level request
        # handler coroutine also works when
        # given valid input.
        #
        list_output_1 = testrunner_coro_request_handler_singleshot(
            cfg=cfg_valid, list_list_input=[[request_valid]]
        )
        assert list_output_1 == list_output_expected

        # Check that the mid-level string and
        # template handler coroutine works when
        # given valid input.
        #
        list_output_2 = testrunner_coro_template_handler_singleshot(
            cfg=cfg_valid, list_list_input=[[template_valid, param_valid]]
        )
        assert list_output_2 == list_output_expected

        # Check that the high-level workflow
        # handler coroutine works when given
        # valid input.
        #
        list_output_3 = testrunner_coro_workflow_handler_singleshot(
            cfg=cfg_valid, list_list_input=[[workflow_valid, param_valid]]
        )
        assert list_output_3 == list_output_expected

    # -------------------------------------------------------------------------
    @pytest.mark.e002_general_research
    @pytest.mark.e003_discord
    def it_yields_expected_bit_response_for_valid_audio_translations_input(
        self,
        testvector_audio_translations_valid_bit,
        testrunner_coro_workflow_handler_singleshot,
        testrunner_coro_template_handler_singleshot,
        testrunner_coro_request_handler_singleshot,
    ):
        """
        When valid audio_translations input sent, valid bit output yielded.

        """
        (
            cfg_valid,
            workflow_valid,
            template_valid,
            param_valid,
            request_valid,
            list_output_expected,
        ) = testvector_audio_translations_valid_bit

        # Check that the low-level request
        # handler coroutine also works when
        # given valid input.
        #
        list_output_1 = testrunner_coro_request_handler_singleshot(
            cfg=cfg_valid, list_list_input=[[request_valid]]
        )
        assert list_output_1 == list_output_expected

        # Check that the mid-level string and
        # template handler coroutine works when
        # given valid input.
        #
        list_output_2 = testrunner_coro_template_handler_singleshot(
            cfg=cfg_valid, list_list_input=[[template_valid, param_valid]]
        )
        assert list_output_2 == list_output_expected

        # Check that the high-level workflow
        # handler coroutine works when given
        # valid input.
        #
        list_output_3 = testrunner_coro_workflow_handler_singleshot(
            cfg=cfg_valid, list_list_input=[[workflow_valid, param_valid]]
        )
        assert list_output_3 == list_output_expected
