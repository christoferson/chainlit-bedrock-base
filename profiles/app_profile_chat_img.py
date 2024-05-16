import os
import boto3
import chainlit as cl
from chainlit.input_widget import Select, Slider
import traceback
import logging
import app_bedrock
import base64
import json
from PIL import Image
import io

AWS_REGION = os.environ["AWS_REGION"]
AUTH_ADMIN_USR = os.environ["AUTH_ADMIN_USR"]
AUTH_ADMIN_PWD = os.environ["AUTH_ADMIN_PWD"]

bedrock = boto3.client("bedrock", region_name=AWS_REGION)
bedrock_runtime = boto3.client('bedrock-runtime', region_name=AWS_REGION)

async def on_chat_start():
    
    model_ids = [
        "anthropic.claude-3-sonnet-20240229-v1:0",
        "anthropic.claude-3-haiku-20240307-v1:0",
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

    mime_mapping = {
        "image/png": "PNG",
        "image/jpeg": "JPEG"
    }

    bedrock_model_id = cl.user_session.get("bedrock_model_id")
    inference_parameters = cl.user_session.get("inference_parameters")
    application_options = cl.user_session.get("application_options")
    bedrock_model_strategy : app_bedrock.BedrockModelStrategy = cl.user_session.get("bedrock_model_strategy")

    text_file = cl.user_session.get("text_file")
    text_file_text = cl.user_session.get("text_file_text")
    text_file_mime = cl.user_session.get("text_file_mime")

    if text_file is None:
        if not message.elements:
            await cl.Message(content="No file attached").send()
            return

    if message.elements:
        text_file = message.elements[0]
        print(f"MIME: {text_file.mime}") # application/vnd.ms-excel #text/plain
        image = Image.open(text_file.path)
        input_image_b64 = image_to_base64(image, mime_mapping[text_file.mime]) #.resize((size, size)
        text_file_text = input_image_b64
        text_file_mime = text_file.mime

        cl.user_session.set("text_file", text_file)
        cl.user_session.set("text_file_text", text_file_text)
        cl.user_session.set("text_file_mime", text_file_mime)

    prompt_template = bedrock_model_strategy.create_prompt(application_options, "", message.content)
    prompt = prompt_template
    #print(prompt)
    await cl.Message(content=f"mime={text_file_mime}").send()

    request = {
        "anthropic_version": "bedrock-2023-05-31",
        #"prompt": prompt,
        "temperature": inference_parameters.get("temperature"),
        "top_p": inference_parameters.get("top_p"), #0.5,
        "top_k": inference_parameters.get("top_k"), #300,
        "max_tokens": inference_parameters.get("max_tokens_to_sample"), #2048,
        "system": inference_parameters.get("system_message") if inference_parameters.get("system_message") else  "You are a helpful assistant.",
        "messages": [
            {
                "role": "user", 
                "content": [
                    {
                        "type": "text",
                        "text": f"{prompt}"
                    },
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": text_file_mime,
                            "data": text_file_text,
                        },
                    }
                ]
            }
        ]
        #"stop_sequences": []
    }
    ####
    #await cl.Message(content=f"mime={json.dumps(request)}").send()

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



def image_to_base64(image,mime_type:str):
    buffer = io.BytesIO()
    image.save(buffer, format=mime_type)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")
