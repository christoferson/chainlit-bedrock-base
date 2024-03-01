# chainlit-bedrock-base
Chainlit Bedrock Base Code

##### Install Dependencies

pip install --upgrade boto3

pip install --upgrade langchain-community

pip install --upgrade chainlit

pip install --upgrade python-dotenv

##### Generate requirements.txt

pipreqs --encoding utf-8 "./" --force

##### Generate JWT Secret for Authentication

chainlit create-secret

Copy the following secret into your .env file. Once it is set, changing it will logout all users with active sessions.
CHAINLIT_AUTH_SECRET=xxx

##### Launch Locally

chainlit run app.py -h

##### List of Repository

Basic example that directly invokes the Bedrock Foundational Model

[chainlit-bedrock-base](https://github.com/christoferson/chainlit-bedrock-base)  LLM

[chainlit-bedrock-kb](https://github.com/christoferson/chainlit-bedrock-kb)      LLM+KB

[chainlit-bedrock-kb-lc](https://github.com/christoferson/chainlit-bedrock-kb-lc)

[chainlit-bedrock](https://github.com/christoferson/chainlit-bedrock)

[chainlit-bedrock-lc](https://github.com/christoferson/chainlit-bedrock-lc)

[chainlit-bedrock-agent]((https://github.com/christoferson/chainlit-bedrock-agent))


