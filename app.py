import os
import boto3
import chainlit as cl
from typing import Optional
import profiles.app_profile_chat
import profiles.app_profile_data
import profiles.app_profile_file
import profiles.app_profile_search
import profiles.app_profile_search_meta
import profiles.app_profile_chat_img

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
            markdown_description="Claude 3",
            icon="https://picsum.photos/250",
        ),
        cl.ChatProfile(
            name="DATA",
            markdown_description="Retrieve and Generate",
            icon="https://picsum.photos/250",
        ),
        cl.ChatProfile(
            name="FILE",
            markdown_description="Retrieve and Generate with File",
            icon="https://picsum.photos/250",
        ),
        cl.ChatProfile(
            name="SEARCH",
            markdown_description="Retrieve then Generate",
            icon="https://picsum.photos/250",
        ),
        cl.ChatProfile(
            name="SEARCH_META",
            markdown_description="Retrieve then Generate (Meta)",
            icon="https://picsum.photos/250",
        ),
        cl.ChatProfile(
            name="CHAT_IMG",
            markdown_description="Claude 3 + Image",
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
    elif chat_profile == "FILE":
       await profiles.app_profile_file.on_chat_start()
    elif chat_profile == "SEARCH":
       await profiles.app_profile_search.on_chat_start()
    elif chat_profile == "SEARCH_META":
       await profiles.app_profile_search_meta.on_chat_start()
    elif chat_profile == "CHAT_IMG":
        await profiles.app_profile_chat_img.on_chat_start()
    else:
       raise ValueError(f"Unsupported Profile. {chat_profile}")

@cl.on_settings_update
async def setup_agent(settings):

    chat_profile = cl.user_session.get("chat_profile")

    if chat_profile == "CHAT":
        await profiles.app_profile_chat.on_settings_update(settings)
    elif chat_profile == "DATA":
       await profiles.app_profile_data.on_settings_update(settings)
    elif chat_profile == "FILE":
       await profiles.app_profile_file.on_settings_update(settings)
    elif chat_profile == "SEARCH":
       await profiles.app_profile_search.on_settings_update(settings)
    elif chat_profile == "SEARCH_META":
       await profiles.app_profile_search_meta.on_settings_update(settings)
    elif chat_profile == "CHAT_IMG":
        await profiles.app_profile_chat_img.on_settings_update(settings)
    else:
       raise ValueError(f"Unsupported Profile. {chat_profile}")
    

@cl.on_message
async def main(message: cl.Message):

    chat_profile = cl.user_session.get("chat_profile")

    if chat_profile == "CHAT":
        await profiles.app_profile_chat.on_message(message)
    elif chat_profile == "DATA":
       await profiles.app_profile_data.on_message(message)
    elif chat_profile == "FILE":
       await profiles.app_profile_file.on_message(message)
    elif chat_profile == "SEARCH":
       await profiles.app_profile_search.on_message(message)
    elif chat_profile == "SEARCH_META":
       await profiles.app_profile_search_meta.on_message(message)
    elif chat_profile == "CHAT_IMG":
        await profiles.app_profile_chat_img.on_message(message)
    else:
       raise ValueError(f"Unsupported Profile. {chat_profile}")

