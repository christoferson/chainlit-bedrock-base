import os
import boto3
from typing import List

AWS_REGION = os.environ["AWS_REGION"]

bedrock_agent = boto3.client('bedrock-agent', region_name=AWS_REGION)

async def list_knowledge_bases() -> List[str]:

    response = bedrock_agent.list_knowledge_bases(maxResults=20) #response = bedrock_agent.list_knowledge_bases(maxResults = 5)

    kb_id_list = []
    for i, knowledgeBaseSummary in enumerate(response['knowledgeBaseSummaries']):
        kb_id = knowledgeBaseSummary['knowledgeBaseId']
        name = knowledgeBaseSummary['name']
        description = knowledgeBaseSummary['description']
        status = knowledgeBaseSummary['status']
        updatedAt = knowledgeBaseSummary['updatedAt']
        #print(f"{i} RetrievalResult: {kb_id} {name} {description} {status} {updatedAt}")
        kb_id_list.append(f"{kb_id} {name}")
    
    if not kb_id_list:
        kb_id_list = ["EMPTY EMPTY"]
    
    return kb_id_list