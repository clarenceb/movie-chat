import os
import time
from typing import List
from dotenv import load_dotenv

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

import streamlit as st

@st.cache_resource
def load_env():
    load_dotenv()

def get_system_prompt():
    return (
        "You are a movie buff assistant who can answer questions about movies, make suggestions, summarise key facts, and provide other useful movie information."
        "Use the following movie(s) context that and any previous chat history to answer the user's questions."
        """If you are unsure, just say "I'm unsure". Only discuss movies from the context provided. Provide a succinct follow up prompt.  Don't discuss other topics not related to the movies."""
        "\n\n"
        "{context}"
    )

def display_answer(answer):
    with st.chat_message("assistant"):
        st.write(answer)

def display_question(message):
    with st.chat_message("user"):
        st.write(message)

def contextualize_q_system_prompt():
    return (
        "Given a chat history and the latest user question "
        "which might reference context in the chat history, "
        "formulate a standalone question which can be understood "
        "without the chat history. Do NOT answer the question, "
        "just reformulate it if needed and otherwise return it as is."
    )

@st.cache_resource
def setup_rag_chain(api_key, resource_endpoint, deployment_name, redis_endpoint, redis_password):
    contextualize_q_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", contextualize_q_system_prompt()),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
    )

    # we will use Azure OpenAI as our embeddings provider
    embedding = AzureOpenAIEmbeddings(
        azure_endpoint=resource_endpoint,
        azure_deployment=deployment_name,
        openai_api_key=api_key,
        openai_api_version='2024-03-01-preview',
        chunk_size=16)

    # name of the Redis search index to create
    index_name = "movieindex"

    # create a connection string for the Redis Vector Store. Uses Redis-py format: https://redis-py.readthedocs.io/en/stable/connections.html#redis.Redis.from_url
    # This example assumes TLS is enabled. If not, use "redis://" instead of "rediss://
    redis_url = "rediss://:" + redis_password + "@"+ redis_endpoint

    vectorstore = RedisVectorStore.from_existing_index(
        embedding=embedding,
        redis_url=redis_url,
        index_name=index_name,
        schema="redis_schema.yaml"
    )

    # Initialize the LLM
    llm = AzureChatOpenAI(
        azure_endpoint=resource_endpoint,
        azure_deployment='gpt-4o-mini',
        api_key=api_key,
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

    return create_retrieval_chain(history_aware_retriever, question_answer_chain)

def reset_chat_history():
    st.session_state['chat_history'] = []

def get_chat_history():
    if 'chat_history' not in st.session_state:
        reset_chat_history()
    return st.session_state.get('chat_history')

def append_to_chat_history(message):
    if 'chat_history' not in st.session_state:
        reset_chat_history()

    st.session_state['chat_history'].append(message)

def display_chat_history():
    if 'chat_history' not in st.session_state:
        reset_chat_history()

    for message in st.session_state.chat_history:
        with st.chat_message(message.type):
            st.write(message.content)

def welcome_message():
    if len(get_chat_history()) == 0:
        append_to_chat_history(AIMessage(content=(
            "Welcome to the Movie Chatbot!"
            "Ask me anything about movies, and I'll do my best to help you out."
            " Type 'q' to start a new conversation.")))

if __name__ == "__main__":
    load_env()

    API_KEY = os.getenv('API_KEY')
    RESOURCE_ENDPOINT = os.getenv('RESOURCE_ENDPOINT')
    DEPLOYMENT_NAME = os.getenv('DEPLOYMENT_NAME')
    REDIS_ENDPOINT = os.getenv('REDIS_ENDPOINT')
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')
    DEBUG = os.getenv('DEBUG')

    rag_chain = setup_rag_chain(
        api_key=API_KEY,
        resource_endpoint=RESOURCE_ENDPOINT,
        deployment_name=DEPLOYMENT_NAME,
        redis_endpoint=REDIS_ENDPOINT,
        redis_password=REDIS_PASSWORD
    )

    st.title('Movie Chat')
    welcome_message()
    display_chat_history()

    question = st.chat_input("Ask your questions about movies or type 'q' to start a new conversation.")

    if question:
        if question == 'q':
            reset_chat_history()
            welcome_message()
            display_chat_history()
        else:
            append_to_chat_history(HumanMessage(content=question))
            display_question(question)
            try:
                with st.spinner("Thinking...", show_time=True):
                    if DEBUG:
                        start_time = time.time()
                        response = rag_chain.invoke({"input": question, "chat_history": get_chat_history()}, config={'callbacks': [debugging.DebugCallbackHandler()]})
                        end_time = time.time()
                        elapsed_time = end_time - start_time
                    else:
                        response = rag_chain.invoke({"input": question, "chat_history": get_chat_history()})

                append_to_chat_history(AIMessage(content=response["answer"]))
                display_answer(response["answer"])

                if DEBUG:
                    with st.chat_message("assistant"):
                        st.write(f"Processing time: {elapsed_time:.2f} seconds")
                    debugging.debug_chat_history(
                        messages=[
                            SystemMessage(content=get_system_prompt()), 
                            *get_chat_history()
                        ],
                        truncate_length=200
                    )
            except Exception as e:
                print(f"Error during chain execution: {e}")