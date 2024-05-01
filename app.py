import os
import boto3
import chainlit as cl
from typing import Optional
import profiles.app_profile_chat
import profiles.app_profile_data

AWS_REGION = os.environ["AWS_REGION"]
AUTH_ADMIN_USR = os.environ["AUTH_ADMIN_USR"]
AUTH_ADMIN_PWD = os.environ["AUTH_ADMIN_PWD"]

bedrock = boto3.client("bedrock", region_name=AWS_REGION)
bedrock_runtime = boto3.client('bedrock-runtime', region_name=AWS_REGION)

@cl.password_auth_callback
def auth_callback(username: str, password: str) -> Optional[cl.User]:
  # Fetch the user matching username from your database
  # and compare the hashed password with the value stored in the database
  if (username, password) == (AUTH_ADMIN_USR, AUTH_ADMIN_PWD):
    return cl.User(identifier=AUTH_ADMIN_USR, metadata={"role": "admin", "provider": "credentials"})
  else:
    return None


@cl.set_chat_profiles
async def chat_profile():
    #if current_user.metadata["role"] != "ADMIN":
    #    return None
    return [
        cl.ChatProfile(
            name="CHAT",
            markdown_description="The underlying LLM model is **GPT-3.5**.",
            icon="https://picsum.photos/200",
        ),
        cl.ChatProfile(
            name="DATA",
            markdown_description="The underlying LLM model is **GPT-4**.",
            icon="https://picsum.photos/250",
        ),
    ]

@cl.on_chat_start
async def main():

    user = cl.user_session.get("user")
    chat_profile = cl.user_session.get("chat_profile")
    #await cl.Message(content=f"starting chat with {user.identifier} using the {chat_profile} chat profile").send()

    if chat_profile == "CHAT":
        await profiles.app_profile_chat.on_chat_start()
    elif chat_profile == "DATA":
       await profiles.app_profile_data.on_chat_start()
    else:
       raise ValueError(f"Unsupported Profile. {chat_profile}")

@cl.on_settings_update
async def setup_agent(settings):

    chat_profile = cl.user_session.get("chat_profile")

    if chat_profile == "CHAT":
        await profiles.app_profile_chat.on_settings_update(settings)
    elif chat_profile == "DATA":
       await profiles.app_profile_data.on_settings_update(settings)
    else:
       raise ValueError(f"Unsupported Profile. {chat_profile}")
    

@cl.on_message
async def main(message: cl.Message):

    chat_profile = cl.user_session.get("chat_profile")

    if chat_profile == "CHAT":
        await profiles.app_profile_chat.on_message(message)
    elif chat_profile == "DATA":
       await profiles.app_profile_data.on_message(message)
    else:
       raise ValueError(f"Unsupported Profile. {chat_profile}")

