import os
import time
from typing import List
from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Prompt
from rich.text import Text

from langchain_openai import AzureOpenAIEmbeddings
from langchain_community.vectorstores import Redis as RedisVectorStore
from langchain_openai import AzureChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, trim_messages
from langchain_core.messages.utils import count_tokens_approximately
from langchain_core.runnables import Runnable
from langchain.chains import create_history_aware_retriever
from langchain_core.prompts import MessagesPlaceholder
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

import debugging as debugging

load_dotenv()

API_KEY = os.getenv('API_KEY')
RESOURCE_ENDPOINT = os.getenv('RESOURCE_ENDPOINT')
DEPLOYMENT_NAME = os.getenv('DEPLOYMENT_NAME')
MODEL_NAME = os.getenv('MODEL_NAME')
REDIS_ENDPOINT = os.getenv('REDIS_ENDPOINT')
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')
DEBUG = os.getenv('DEBUG')

console = Console()

def get_system_prompt():
    return (
        "You are a movie buff assistant who can answer questions about movies, make suggestions, summarise key facts, and provide other useful movie information."
        "Use the following movie(s) context that and any previous chat history to answer the user's questions."
        """If you are unsure, just say "I'm unsure". Only discuss movies from the context provided. Provide a succinct follow up prompt.  Don't discuss other topics not related to the movies."""
        "\n\n"
        "{context}"
    )

def display_answer(answer):
    console.print(f'\nAnswer:\n', style="yellow")
    console.print(answer, style="white")

def welcome_message():
        console.print(f"""
#     #                                          #####
##   ##   ####   #    #     #    ######         #     #  #    #    ##     #####
# # # #  #    #  #    #     #    #              #        #    #   #  #      #
#  #  #  #    #  #    #     #    #####          #        ######  #    #     #
#     #  #    #  #    #     #    #              #        #    #  ######     #
#     #  #    #   #  #      #    #              #     #  #    #  #    #     #
#     #   ####     ##       #    ######          #####   #    #  #    #     #\n""", style="bold green")

def user_input_prompt() -> str:
    prompt = Text("\nWhat's your question about movie(s)? ")
    prompt.stylize("yellow")
    return prompt

contextualize_q_system_prompt = (
    "Given a chat history and the latest user question "
    "which might reference context in the chat history, "
    "formulate a standalone question which can be understood "
    "without the chat history. Do NOT answer the question, "
    "just reformulate it if needed and otherwise return it as is."
)

contextualize_q_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)

# we will use Azure OpenAI as our embeddings provider
embedding = AzureOpenAIEmbeddings(
    azure_endpoint=RESOURCE_ENDPOINT,
    azure_deployment=DEPLOYMENT_NAME,
    openai_api_key=API_KEY,
    openai_api_version='2024-03-01-preview',
    chunk_size=16)

# name of the Redis search index to create
index_name = "movieindex"

# create a connection string for the Redis Vector Store. Uses Redis-py format: https://redis-py.readthedocs.io/en/stable/connections.html#redis.Redis.from_url
# This example assumes TLS is enabled. If not, use "redis://" instead of "rediss://
redis_url = "rediss://:" + REDIS_PASSWORD + "@"+ REDIS_ENDPOINT

vectorstore = RedisVectorStore.from_existing_index(
    embedding=embedding,
    redis_url=redis_url,
    index_name=index_name,
    schema="redis_schema.yaml"
)

# Initialize the LLM
llm = AzureChatOpenAI(
    azure_endpoint=RESOURCE_ENDPOINT,
    azure_deployment='gpt-4o-mini',
    api_key=API_KEY,
    openai_api_version="2024-09-01-preview"
)

retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 10})

history_aware_retriever = create_history_aware_retriever(
    llm, retriever, contextualize_q_prompt
)

qa_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", get_system_prompt()),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)
question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)

rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

if DEBUG:
    debug_handler = debugging.DebugCallbackHandler()

welcome_message()

chat_history = []

while True:
    question = Prompt.ask(user_input_prompt())
    if question == 'q':
        print('Bye!')
        break
    elif question == '':
        welcome_message()
        chat_history = []
        console.print(f'Starting a new conversation...\n', style="yellow")
    else:
        try:
            if DEBUG:
                start_time = time.time()
                response = rag_chain.invoke({"input": question, "chat_history": chat_history}, config={'callbacks': [debug_handler]})
                end_time = time.time()
                elapsed_time = end_time - start_time
            else:
                response = rag_chain.invoke({"input": question, "chat_history": chat_history})

            answer = response["answer"]
            chat_history.extend(
                [
                HumanMessage(content=question),
                AIMessage(content=answer)
                ]
            )

            display_answer(answer)

            if DEBUG:
                print(f"\n(Processing time: {elapsed_time:.2f} seconds)")
                debugging.debug_chat_history(
                    messages=[
                        SystemMessage(content=get_system_prompt()),
                        *chat_history
                    ],
                    truncate_length=200
                )
        except Exception as e:
            print(f"Error during chain execution: {e}")