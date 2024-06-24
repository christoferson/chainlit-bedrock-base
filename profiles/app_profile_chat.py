from __future__ import annotations
import os
import boto3
import chainlit as cl
from chainlit.element import ElementBased
from chainlit.input_widget import Select, Slider
import traceback
import logging
import app_bedrock
from io import BytesIO
import cmn.cmn_lib
import uuid


AWS_REGION = os.environ["AWS_REGION"]
AUTH_ADMIN_USR = os.environ["AUTH_ADMIN_USR"]
AUTH_ADMIN_PWD = os.environ["AUTH_ADMIN_PWD"]

AWS_BUCKET_TRANSCRIBE = os.environ["AWS_BUCKET_TRANSCRIBE"]

bedrock = boto3.client("bedrock", region_name=AWS_REGION)
bedrock_runtime = boto3.client('bedrock-runtime', region_name=AWS_REGION)
s3_client = boto3.client('s3', region_name=AWS_REGION)
transcribe_client = boto3.client("transcribe", region_name=AWS_REGION)

async def on_chat_start():
    
    model_ids = [
        "anthropic.claude-3-sonnet-20240229-v1:0",
        "anthropic.claude-3-haiku-20240307-v1:0",
        "amazon.titan-text-express-v1",
        "mistral.mistral-7b-instruct-v0:2",
        "mistral.mixtral-8x7b-instruct-v0:1",
        "cohere.command-light-text-v14",
        "cohere.command-text-v14",
        "ai21.j2-mid"
    ]

    settings = await cl.ChatSettings(
        [
            Select(
                id="Model",
                label="Amazon Bedrock - Model",
                values=model_ids,
                initial_index=model_ids.index("anthropic.claude-3-sonnet-20240229-v1:0"),
                
            ),
            Slider(
                id="Temperature",
                label="Temperature",
                initial=0.3,
                min=0,
                max=1,
                step=0.1,
            ),
            Slider(
                id = "TopP",
                label = "Top P",
                initial = 1,
                min = 0,
                max = 1,
                step = 0.1,
            ),
            Slider(
                id = "TopK",
                label = "Top K",
                initial = 250,
                min = 0,
                max = 500,
                step = 5,
            ),
            Slider(
                id="MaxTokenCount",
                label="Max Token Size",
                initial=2048,
                min=256,
                max=4096,
                step=256,
            ),
        ]
    ).send()
    await on_settings_update(settings)

    await cl.Message(
        content="Welcome to the Chainlit audio example. Press `P` to talk!"
    ).send()

#@cl.on_settings_update
async def on_settings_update(settings):

    bedrock_model_id = settings["Model"]

    application_options = dict (
        option_terse = False,
        option_strict = False
    )

    inference_parameters = dict (
        temperature = settings["Temperature"],
        top_p = float(settings["TopP"]),
        top_k = int(settings["TopK"]),
        max_tokens_to_sample = int(settings["MaxTokenCount"]),
        system_message = "You are a helpful assistant.",
        stop_sequences =  []
    )

    model_strategy = app_bedrock.BedrockModelStrategyFactory.create(bedrock_model_id)

    cl.user_session.set("bedrock_model_id", bedrock_model_id)
    cl.user_session.set("application_options", application_options)
    cl.user_session.set("inference_parameters", inference_parameters)
    cl.user_session.set("bedrock_model_strategy", model_strategy)
    

#@cl.on_message
async def on_message(message: cl.Message):

    bedrock_model_id = cl.user_session.get("bedrock_model_id")
    inference_parameters = cl.user_session.get("inference_parameters")
    application_options = cl.user_session.get("application_options")
    bedrock_model_strategy : app_bedrock.BedrockModelStrategy = cl.user_session.get("bedrock_model_strategy")

    prompt_template = bedrock_model_strategy.create_prompt(application_options, "", message.content)
    prompt = prompt_template
    print(prompt)
    #print(inference_parameters)
    request = bedrock_model_strategy.create_request(inference_parameters, prompt)
    #print(request)
    print(f"{type(request)} {request}")

    msg = cl.Message(content="")

    await msg.send()

    try:

        response = bedrock_model_strategy.send_request(request, bedrock_runtime, bedrock_model_id)

        await bedrock_model_strategy.process_response(response, msg)

    except Exception as e:
        logging.error(traceback.format_exc())
        await msg.stream_token(f"{e}")
    finally:
        await msg.send()

    print("End")


async def on_audio_chunk(chunk: cl.AudioChunk):
    print(f"on_audio_chunk chunk.isStart: {chunk.isStart}")
    if chunk.isStart:
        print(f"chunk.mimeType: {chunk.mimeType}")

        buffer = BytesIO()
        # This is required for whisper to recognize the file type
        buffer.name = f"input_audio.{chunk.mimeType.split('/')[1]}"
        # Initialize the session for a new audio stream
        cl.user_session.set("audio_buffer", buffer)
        cl.user_session.set("audio_mime_type", chunk.mimeType)

    # Write the chunks to a buffer and transcribe the whole audio at the end
    cl.user_session.get("audio_buffer").write(chunk.data)

async def on_audio_end(elements: list[ElementBased]):

    print(f"on_audio_end")

    # Get the audio buffer from the session
    audio_buffer: BytesIO = cl.user_session.get("audio_buffer")
    audio_buffer.seek(0)  # Move the file pointer to the beginning
    audio_file:bytes = audio_buffer.read()
    audio_mime_type: str = cl.user_session.get("audio_mime_type")

   # Apply Speech to Text or any other processing

    input_audio_el = cl.Audio(
        mime=audio_mime_type, content=audio_file, name=audio_buffer.name
    )
    await cl.Message(
        author="You", 
        type="user_message",
        content="",
        elements=[input_audio_el, *elements]
    ).send()

    audio_id = str(uuid.uuid4())
    bucket_name = AWS_BUCKET_TRANSCRIBE
    bucket_key = f"{audio_id}.ogg"
    audio_s3_uri = f"s3://{bucket_name}/{bucket_key}"

    saving_audio_message = f"""Saving Audio.
    audio = {audio_s3_uri}
    """
    await cl.Message(content=saving_audio_message).send()
    s3_client.put_object(Body=audio_file, Bucket=bucket_name, Key=bucket_key, ContentType=audio_mime_type)

    transcribe_start_message = f"""Transcribe Start.
    in = {audio_s3_uri}
    """
    await cl.Message(content=transcribe_start_message).send()
    transcript_file_uri = cmn.cmn_lib.transcribe_file(f"{audio_id}-job", audio_s3_uri, transcribe_client)

    transcribe_complete_message = f"""Transcribe Complete.
    in = {audio_s3_uri}
    out = [transcript_file]({transcript_file_uri})
    """
    await cl.Message(content=transcribe_complete_message).send()
