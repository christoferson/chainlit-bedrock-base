import os
import boto3
import chainlit as cl
from chainlit.input_widget import Select, Slider
import traceback
import logging
import app_bedrock

AWS_REGION = os.environ["AWS_REGION"]
AUTH_ADMIN_USR = os.environ["AUTH_ADMIN_USR"]
AUTH_ADMIN_PWD = os.environ["AUTH_ADMIN_PWD"]

bedrock = boto3.client("bedrock", region_name=AWS_REGION)
bedrock_runtime = boto3.client('bedrock-runtime', region_name=AWS_REGION)

async def on_chat_start():
    
    model_ids = ["anthropic.claude-3-sonnet-20240229-v1:0"]
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

    bedrock_model_id = cl.user_session.get("bedrock_model_id")
    inference_parameters = cl.user_session.get("inference_parameters")
    application_options = cl.user_session.get("application_options")
    bedrock_model_strategy : app_bedrock.BedrockModelStrategy = cl.user_session.get("bedrock_model_strategy")

    #create_prompt(self, application_options: dict, context_info: str, query: str) -> str:
    prompt_template = bedrock_model_strategy.create_prompt(application_options, "", message.content)
    #prompt = prompt_template.replace("{input}", message.content)
    #prompt = prompt.replace("{history}", "")
    prompt = prompt_template
    print(prompt)
    #print(inference_parameters)
    request = bedrock_model_strategy.create_request(inference_parameters, prompt)
    #print(request)
    print(f"{type(request)} {request}")

    msg = cl.Message(content="")

    await msg.send()

    try:

        #response = bedrock_runtime.invoke_model_with_response_stream(modelId = bedrock_model_id, body = json.dumps(request))
        response = bedrock_model_strategy.send_request(request, bedrock_runtime, bedrock_model_id)

        #stream = response["body"]
        #await bedrock_model_strategy.process_response_stream(stream, msg)
        await bedrock_model_strategy.process_response(response, msg)

    except Exception as e:
        logging.error(traceback.format_exc())
        await msg.stream_token(f"{e}")
    finally:
        await msg.send()

    print("End")

