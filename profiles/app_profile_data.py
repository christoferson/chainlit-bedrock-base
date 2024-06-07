import os
import boto3
import chainlit as cl
from chainlit.input_widget import Select, Slider
import traceback
import logging
import app_bedrock
import app_bedrock_lib

AWS_REGION = os.environ["AWS_REGION"]
AUTH_ADMIN_USR = os.environ["AUTH_ADMIN_USR"]
AUTH_ADMIN_PWD = os.environ["AUTH_ADMIN_PWD"]

bedrock = boto3.client("bedrock", region_name=AWS_REGION)
bedrock_runtime = boto3.client('bedrock-runtime', region_name=AWS_REGION)
bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name=AWS_REGION)

async def on_chat_start():

    kb_id_list = await app_bedrock_lib.list_knowledge_bases()
    model_ids = ["anthropic.claude-3-sonnet-20240229-v1:0"]
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
                initial = 8,
                min = 1,
                max = 32,
                step = 1,
            ),
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
    knowledge_base_id = settings["KnowledgeBase"]
    knowledge_base_id = knowledge_base_id.split(" ", 1)[0]
    
    llm_model_arn = "arn:aws:bedrock:{}::foundation-model/{}".format(AWS_REGION, settings["Model"])

    application_options = dict (
        option_terse = False,
        option_strict = False
    )

    inference_parameters = dict (
        kb_retrieve_document_count = int(settings["RetrieveDocumentCount"]),
        temperature = settings["Temperature"],
        top_p = float(settings["TopP"]),
        top_k = int(settings["TopK"]),
        max_tokens_to_sample = int(settings["MaxTokenCount"]),
        system_message = "You are a helpful assistant.",
        stop_sequences =  []
    )

    model_strategy = app_bedrock.BedrockModelStrategyFactory.create(bedrock_model_id)

    cl.user_session.set("bedrock_model_id", bedrock_model_id)
    cl.user_session.set("llm_model_arn", llm_model_arn)
    cl.user_session.set("knowledge_base_id", knowledge_base_id)
    cl.user_session.set("application_options", application_options)
    cl.user_session.set("inference_parameters", inference_parameters)
    cl.user_session.set("bedrock_model_strategy", model_strategy)
    

#@cl.on_message
async def on_message(message: cl.Message):

    session_id = cl.user_session.get("session_id")
    bedrock_model_id = cl.user_session.get("bedrock_model_id")
    inference_parameters = cl.user_session.get("inference_parameters")
    application_options = cl.user_session.get("application_options")
    knowledge_base_id = cl.user_session.get("knowledge_base_id") 
    llm_model_arn = cl.user_session.get("llm_model_arn") 
    bedrock_model_strategy : app_bedrock.BedrockModelStrategy = cl.user_session.get("bedrock_model_strategy")

    #create_prompt(self, application_options: dict, context_info: str, query: str) -> str:
    prompt_template = bedrock_model_strategy.create_prompt(application_options, "", message.content)
    #prompt = prompt_template.replace("{input}", message.content)
    #prompt = prompt.replace("{history}", "")
    prompt = prompt_template
    #print(prompt)
    #print(inference_parameters)
    request = bedrock_model_strategy.create_request(inference_parameters, prompt)
    #print(request)
    #print(f"{type(request)} {request}")


    msg = cl.Message(content="")

    await msg.send()

    try:

        params = {
            "input" : {
                'text': prompt,
            },
            "retrieveAndGenerateConfiguration" : {
                'type': 'KNOWLEDGE_BASE',
                'knowledgeBaseConfiguration': {
                    'knowledgeBaseId': knowledge_base_id,
                    'modelArn': llm_model_arn,
                    'retrievalConfiguration': {
                        'vectorSearchConfiguration': {
                            'numberOfResults': inference_parameters.get('kb_retrieve_document_count'), #kb_retrieve_document_count,  #Minimum value of 1. Maximum value of 100
                            #'overrideSearchType': 'HYBRID'|'SEMANTIC'
                        }
                    },
                    'generationConfiguration': {
                        'inferenceConfig': {
                            'textInferenceConfig': {
                                'maxTokens': inference_parameters.get("max_tokens_to_sample"),
                                'temperature': inference_parameters.get('temperature'),
                                'topP': inference_parameters.get('top_p'),
                            }
                        }
                    },
                    'additionalModelRequestFields': {
                        "top_k": inference_parameters.get('top_k')
                    }
                    # Unknown parameter in retrieveAndGenerateConfiguration.knowledgeBaseConfiguration: "generationConfiguration", must be one of: knowledgeBaseId, modelArn, retrievalConfiguration
                    #'generationConfiguration': {
                    #    'promptTemplate': {
                    #        'textPromptTemplate': prompt_template
                    #    }
                    #}
                }
            },
        }

        if session_id != "" and session_id is not None:
            params["sessionId"] = session_id #session_id=84219eab-2060-4a8f-a481-3356d66b8586

        print(params)

        response = bedrock_agent_runtime.retrieve_and_generate(
            **params
        )

        text = response['output']['text']
        await msg.stream_token(text)

        async with cl.Step(name="KnowledgeBase", type="llm", root=False) as step:
            step.input = msg.content

            elements = []

            if "citations" in response:
                #print(response["citations"])
                for citation in response["citations"]:
                    if "retrievedReferences" in citation:
                        references = citation["retrievedReferences"]
                        #print(references)
                        reference_idx = 0
                        for reference in references:
                            reference_idx = reference_idx + 1
                            print(reference)
                            reference_name = f"r{reference_idx}"
                            reference_text = ""
                            reference_location_type = ""
                            reference_location_uri = ""
                            if "content" in reference:
                                content = reference["content"]
                                reference_text = content["text"]
                                #elements.append(cl.Text(name=f"r{reference_idx}", content=reference_text, display="inline"))
                            if "location" in reference:
                                location = reference["location"]
                                location_type = location["type"]
                                reference_location_type = location_type
                                if "S3" == location_type:
                                    location_uri = location["s3Location"]["uri"]
                                    reference_location_uri = location_uri
                                    reference_name = f"\n{reference_location_type}-{reference_location_uri}"
                            #await step.stream_token(f"\n{reference_location_type} {reference_location_uri}")
                            #elements.append(cl.Text(name=f"src_{reference_idx}", content=f"{location_uri}\n{reference_text}"))
                            elements.append(cl.Text(name=f"{reference_name}", content=reference_text, display="inline"))

            step.elements = elements
            prompt_display = prompt.replace("\n", "").rstrip()
            await step.stream_token(f"{prompt_display}")
            await step.send()

        session_id = response['sessionId']
        await msg.stream_token(f"\nsession_id={session_id}")
        cl.user_session.set("session_id", session_id)

    except Exception as e:
        logging.error(traceback.format_exc())
        await msg.stream_token(f"{e}")
    finally:
        await msg.send()

