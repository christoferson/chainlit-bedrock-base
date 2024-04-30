# chainlit-bedrock-base
Chainlit Bedrock Base Code

##### Concepts

Tasks
- entity extraction
- question answering
- text summarization
- code generation
- creative writing

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

[chainlit-bedrock-base](https://github.com/christoferson/chainlit-bedrock-base)

Boto3

[chainlit-bedrock-llm](https://github.com/christoferson/chainlit-bedrock-llm) LLM

[chainlit-bedrock-llm-kb](https://github.com/christoferson/chainlit-bedrock-llm-kb) LLM+KB

[chainlit-bedrock-agent](https://github.com/christoferson/chainlit-bedrock-agent)

Boto3 - SDXL

[chainlit-bedrock-sdxl](https://github.com/christoferson/chainlit-bedrock-sdxl)

Langchain

[chainlit-bedrock-kb](https://github.com/christoferson/chainlit-bedrock-kb) LLM+KB LLM+KB+LC(ConversationalRetrievalChain)

[chainlit-bedrock-kb-lc](https://github.com/christoferson/chainlit-bedrock-kb-lc) LLL+KB+LC(RetrievalQA)

[chainlit-bedrock](https://github.com/christoferson/chainlit-bedrock) Copilot

[chainlit-bedrock-lc](https://github.com/christoferson/chainlit-bedrock-lc)








##### Links

[anthropic-cookbook](https://github.com/anthropics/anthropic-cookbook)

https://docs.anthropic.com/claude/docs/prompt-engineering

##### Links (Amazon Knowledge Base for Bedrock)

- https://aws.amazon.com/jp/blogs/aws/knowledge-bases-for-amazon-bedrock-now-supports-amazon-aurora-postgresql-and-cohere-embedding-models/

- https://aws.amazon.com/jp/blogs/aws/vector-engine-for-amazon-opensearch-serverless-is-now-generally-available/

- https://docs.anthropic.com/claude/docs/models-overview#model-comparison

##### Completions vs Messages API

1. **Completions API**:
   - The completions API is designed for generating text completions or responses to prompts.
   - It's typically used for tasks like text generation, language translation, text summarization, and other similar natural language processing (NLP) tasks.
   - You provide a prompt or input text, and the API generates a completion or continuation of that text based on the model it was trained on.
   - The completion API is well-suited for scenarios where you need the model to generate a single response or a set of responses based on a given input.

2. **Messages API**:
   - The messages API is tailored for conversational applications, where there's an ongoing interaction between the user and the model.
   - It's used to send messages back and forth between the user and the model, maintaining context over multiple exchanges.
   - The messages API supports more complex interactions compared to the completions API. It allows for context handling, maintaining state across multiple messages, and managing conversational flow.
   - This API is suitable for building chatbots, virtual assistants, dialogue systems, and other conversational AI applications where maintaining a conversational context is essential.

In summary, while both APIs involve generating text-based responses, the completions API is more suited for generating standalone responses based on prompts, while the messages API is designed for managing ongoing conversational interactions between users and the model.