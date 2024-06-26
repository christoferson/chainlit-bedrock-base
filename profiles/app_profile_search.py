import os
import boto3
import chainlit as cl
from chainlit.input_widget import Select, Slider, Switch
import traceback
import logging
import app_bedrock
import app_bedrock_lib

from botocore.exceptions import ClientError

AWS_REGION = os.environ["AWS_REGION"]

bedrock = boto3.client("bedrock", region_name=AWS_REGION)
bedrock_runtime = boto3.client('bedrock-runtime', region_name=AWS_REGION)
bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name=AWS_REGION)

async def on_chat_start():

    kb_id_list = await app_bedrock_lib.list_knowledge_bases()
    
    model_ids = [
        "anthropic.claude-v2", #"anthropic.claude-v2:0:18k",
        "anthropic.claude-instant-v1",
        "anthropic.claude-3-sonnet-20240229-v1:0",
        "anthropic.claude-3-haiku-20240307-v1:0",
        "amazon.titan-text-express-v1",
        "mistral.mistral-7b-instruct-v0:2",
        "mistral.mixtral-8x7b-instruct-v0:1",
        "cohere.command-light-text-v14",
        "cohere.command-text-v14",
        #"meta.llama2-13b-chat-v1",
        #"meta.llama2-70b-chat-v1",
        "ai21.j2-mid"
    ]
    
    settings = await cl.ChatSettings(
        [
            Select(
                id="KnowledgeBase",
                label="KnowledgeBase ID",
                values=kb_id_list,
                initial_index=0
            ),
            Slider(
                id = "RetrieveDocumentCount",
                label = "KnowledgeBase DocumentCount",
                initial = 3,
                min = 1,
                max = 8,
                step = 1,
            ),
            Select(
                id = "Mode",
                label = "KnowledgeBase Generation Mode",
                values = ["RetrieveAndGenerate", "Retrieve", "Generate"],
                initial_index = 1,
            ),
            Select(
                id = "Model",
                label = "Foundation Model",
                values = model_ids,
                initial_index = model_ids.index("anthropic.claude-3-sonnet-20240229-v1:0"),
            ),
            Slider(
                id = "Temperature",
                label = "Temperature - Analytical vs Creative",
                initial = 0.0,
                min = 0,
                max = 1,
                step = 0.1,
            ),
            Slider(
                id = "TopP",
                label = "Top P - High Diversity vs Low Diversity",
                initial = 1,
                min = 0,
                max = 1,
                step = 0.1,
            ),
            Slider(
                id = "TopK",
                label = "Top K - High Probability vs Low Probability",
                initial = 250,
                min = 0,
                max = 1500,
                step = 5,
            ),
            Slider(
                id="MaxTokenCount",
                label="Max Token Size",
                initial = 2560,
                min = 256,
                max = 4096,
                step = 256,
            ),
            Switch(id="Strict", label="Retrieve - Limit Answers to KnowledgeBase", initial=False),
            Switch(id="Terse", label="Terse - Terse & Consise Answers", initial=False),
            Switch(id="SourceTableMarkdown", label="Source Tables Markdown Display", initial=True),
        ]
    ).send()

    await on_settings_update(settings)

#@cl.on_settings_update
async def on_settings_update(settings):

    knowledge_base_id = settings["KnowledgeBase"]
    knowledge_base_id = knowledge_base_id.split(" ", 1)[0]
    
    llm_model_arn = "arn:aws:bedrock:{}::foundation-model/{}".format(AWS_REGION, settings["Model"])
    #mode = settings["Mode"]
    #strict = settings["Strict"]
    kb_retrieve_document_count = int(settings["RetrieveDocumentCount"])

    bedrock_model_id = settings["Model"]

    inference_parameters = dict (
        temperature = settings["Temperature"],
        top_p = float(settings["TopP"]),
        top_k = int(settings["TopK"]),
        max_tokens_to_sample = int(settings["MaxTokenCount"]),
        stop_sequences =  [],
        #system_message = "You are a helpful assistant. Unless instructed, omit any preamble and provide straight to the point concise answers."
        system_message = "You are a helpful assistant and tries to answer questions as best as you can."
    )

    application_options = dict (
        option_terse = settings["Terse"],
        option_strict = settings["Strict"],
        option_source_table_markdown_display = settings["SourceTableMarkdown"],
    )

    cl.user_session.set("inference_parameters", inference_parameters)
    cl.user_session.set("bedrock_model_id", bedrock_model_id)
    cl.user_session.set("llm_model_arn", llm_model_arn)
    cl.user_session.set("knowledge_base_id", knowledge_base_id)
    cl.user_session.set("kb_retrieve_document_count", kb_retrieve_document_count)
    cl.user_session.set("application_options", application_options)
    
@cl.step(name="retrieve", type="tool")
async def tool(query:str):

    application_options = cl.user_session.get("application_options")
    knowledge_base_id = cl.user_session.get("knowledge_base_id") 
    kb_retrieve_document_count = cl.user_session.get("kb_retrieve_document_count")

    current_step = cl.context.current_step
    
    await current_step.stream_token(f"\nSearch Max {kb_retrieve_document_count} documents.\n")

    context_info = ""

    try:

        prompt = f"""\n\nHuman: {query[0:900]}
        Assistant:
        """

        response = bedrock_agent_runtime.retrieve(
            knowledgeBaseId = knowledge_base_id,
            retrievalQuery={
                'text': prompt,
            },
            retrievalConfiguration={
                'vectorSearchConfiguration': {
                    'numberOfResults': kb_retrieve_document_count
                }
            }
        )

        reference_elements = []
        for i, retrievalResult in enumerate(response['retrievalResults']):
            uri = retrievalResult['location']['s3Location']['uri']
            text = retrievalResult['content']['text']
            excerpt = text[0:75]
            score = retrievalResult['score']
            print(f"{i} RetrievalResult: {score} {uri} {excerpt}")
            #await msg.stream_token(f"\n{i} RetrievalResult: {score} {uri} {excerpt}\n")
            context_info += f"{text}\n" #context_info += f"<p>${text}</p>\n" #context_info += f"${text}\n"
            #await step.stream_token(f"\n[{i+1}] score={score} uri={uri} len={len(text)} text={excerpt}\n")
            await current_step.stream_token(f"\n[{i+1}] score={score} uri={uri} len={len(text)}\n")
            reference_elements.append(cl.Text(name=f"[{i+1}] {uri}", content=text, display="inline")) # “side” (default), “inline”, or “page”
        
        await current_step.stream_token(f"\n")
        current_step.elements = reference_elements

    except Exception as e:
        logging.error(traceback.format_exc())
        await current_step.stream_token(f"{e}")
    finally:
        await current_step.send()

    return context_info

@cl.step(name="generate", type="tool")
async def generate(context_info:str, query:str, msg:cl.Message):

    application_options = cl.user_session.get("application_options")
    application_options = cl.user_session.get("application_options")
    #session_id = cl.user_session.get("session_id") 
    knowledge_base_id = cl.user_session.get("knowledge_base_id") 
    #llm_model_arn = cl.user_session.get("llm_model_arn") 
    bedrock_model_id = cl.user_session.get("bedrock_model_id")
    inference_parameters = cl.user_session.get("inference_parameters")
    option_strict = application_options.get("option_strict")
    option_terse = application_options.get("option_terse")
    kb_retrieve_document_count = cl.user_session.get("kb_retrieve_document_count")

    current_step = cl.context.current_step
    
    elements = []

    try:

        bedrock_model_strategy = app_bedrock.BedrockModelStrategyFactory.create(bedrock_model_id)

        # Create Prompt create_prompt(self, application_options: dict, context_info: str, query: str) -> str:

        prompt = bedrock_model_strategy.create_prompt(application_options, context_info, query)

        # End - Create Prompt 

        system_message = inference_parameters.get("system_message")
        elements.append(cl.Text(name=f"system", content=system_message.replace("\n\n", "").rstrip(), display="inline")) 

        elements.append(cl.Text(name=f"prompt", content=prompt.replace("\n\n", "").rstrip(), display="inline"))

        max_tokens = inference_parameters.get("max_tokens_to_sample")
        temperature = inference_parameters.get('temperature')
        await current_step.stream_token(f"model.id={bedrock_model_id} prompt.len={len(prompt)} temperature={temperature} max_tokens={max_tokens}")

        request = bedrock_model_strategy.create_request(inference_parameters, prompt)

        print(f"{type(request)} {request}")

        response = bedrock_model_strategy.send_request(request, bedrock_runtime, bedrock_model_id)

        await bedrock_model_strategy.process_response(response, msg)

        current_step.elements = elements

    except ClientError as err:
        message = err.response["Error"]["Message"]
        logging.error("A client error occurred: %s", message)
        await current_step.stream_token(f"{message}")
    except Exception as e:
        logging.error(traceback.format_exc())
        await current_step.stream_token(f"{e}")
    finally:
        await current_step.send()

    await current_step.stream_token(f". strict={option_strict} terse={option_terse}\n")
    await current_step.send()

    return "Response from the tool!"

#@cl.on_message
async def on_message(message: cl.Message):

    application_options = cl.user_session.get("application_options")
    #session_id = cl.user_session.get("session_id") 
    knowledge_base_id = cl.user_session.get("knowledge_base_id") 
    #llm_model_arn = cl.user_session.get("llm_model_arn") 
    bedrock_model_id = cl.user_session.get("bedrock_model_id")
    inference_parameters = cl.user_session.get("inference_parameters")
    option_strict = application_options.get("option_strict")
    option_terse = application_options.get("option_terse")
    kb_retrieve_document_count = cl.user_session.get("kb_retrieve_document_count")

    query = message.content

    msg = cl.Message(content="")

    await msg.send()

    try:

        context_info = ""

        context_info = await tool(query)
        
        await generate(context_info, query, msg)

        await msg.send()

    except Exception as e:
        logging.error(traceback.format_exc())
        await msg.stream_token(f"{e}")
    finally:
        await msg.send()

