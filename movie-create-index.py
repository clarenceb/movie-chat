# The dataset contains descriptions of 34,886 movies from around the world from 1901 to 2017.
# Source: https://www.kaggle.com/datasets/jrobischon/wikipedia-movie-plots

import re
import os
import pandas as pd
import tiktoken
from typing import List
from dotenv import load_dotenv
from num2words import num2words
from langchain_openai import AzureOpenAIEmbeddings
from langchain_community.vectorstores import Redis as RedisVectorStore
from langchain_community.document_loaders import DataFrameLoader

load_dotenv()

API_KEY = os.getenv('API_KEY')
RESOURCE_ENDPOINT = os.getenv('RESOURCE_ENDPOINT')
DEPLOYMENT_NAME = os.getenv('DEPLOYMENT_NAME')
MODEL_NAME = os.getenv('MODEL_NAME')
REDIS_ENDPOINT = os.getenv('REDIS_ENDPOINT')
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')

print(f"RESOURCE_ENDPOINT: {RESOURCE_ENDPOINT}")
print(f"REDIS_ENDPOINT: {REDIS_ENDPOINT}")
print(f"DEPLOYMENT_NAME: {DEPLOYMENT_NAME}")
print(f"MODEL_NAME: {MODEL_NAME}")

## Import dataset
## --------------
# This example uses the [Wikipedia Movie Plots](https://www.kaggle.com/datasets/jrobischon/wikipedia-movie-plots) dataset from Kaggle.
# Download this file and place it in the same directory as this file.
FILE_NAME = 'wiki_movie_plots_deduped.csv'
if not os.path.exists(FILE_NAME):
    raise FileNotFoundError(f"The dataset file '{FILE_NAME}' was not found in the current directory. Please download it from https://www.kaggle.com/datasets/jrobischon/wikipedia-movie-plots and place it in the current directory.")
print(f"Loading dataset {FILE_NAME}...")
df=pd.read_csv(os.path.join(os.getcwd(),FILE_NAME))

# Process the dataset to remove spaces in the column titles and filter the dataset to lower the size.
# This isn't required, but is helpful in reducing the time it takes to generate embeddings and loading the index into Redis.
# Feel free to play around with the filters, or add your own! 
df.insert(0, 'id', range(0, len(df)))
df['year'] = df['Release Year'].astype(int)
df['origin'] = df['Origin/Ethnicity'].astype(str)
del df['Release Year']
del df['Origin/Ethnicity']
df = df[df.year > 1970] # only movies made after 1970
df = df[df.origin.isin(['American','British','Canadian'])] # only movies from English-speaking cinema

# Remove whitespace from the `Plot` column to make it easier to generate embeddings.
pd.options.mode.chained_assignment = None

# s is input text
def normalize_text(s, sep_token = " \n "):
    s = re.sub(r'\s+',  ' ', s).strip()
    s = re.sub(r". ,","",s)
    # remove all instances of multiple spaces
    s = s.replace("..",".")
    s = s.replace(". .",".")
    s = s.replace("\n", "")
    s = s.strip()
    
    return s

df['Plot']= df['Plot'].apply(lambda x : normalize_text(x))

# Calculate the number of tokens required to generate the embeddings for this dataset. You may want to filter the dataset more stringently in order to limit the tokens required. 
tokenizer = tiktoken.get_encoding("cl100k_base")
df['n_tokens'] = df["Plot"].apply(lambda x: len(tokenizer.encode(x)))
df = df[df.n_tokens<8192]
print('Number of movies: ' + str(len(df))) # print number of movies remaining in dataset
print('Number of tokens required: ' + str(df['n_tokens'].sum())) # print number of tokens

## Load Dataframe into LangChain
## -----------------------------
# Using the `DataFrameLoader` class allows you to load a pandas dataframe into LangChain. That makes it easy to load your data and use it to generate embeddings using LangChain's other integrations.
print("Loading dataframe into LangChain...")
loader = DataFrameLoader(df, page_content_column="Plot" )
movie_list = loader.load()

## Generate CSV file with filered movies and snake_case titles
## -----------------------------------------------------------
print("Creating CSV file with filered movies and snake_case titles...")
import csv
# Write the movie list to a CSV file as a flat list of the dictionary values without the keys and these columns: id,title,director,cast,genre,wiki_page,plot,year,origin
# update the column names to be lowercase and remove the spaces
# On the plot, I don't want surrounding quotes
df.columns = df.columns.str.lower().str.replace(' ', '_')
# Don't quote the first column which is the column titles
df.to_csv('movie_list.csv', index=False, header=True, sep=',', quoting=csv.QUOTE_NONNUMERIC, escapechar='\\', quotechar='"')
print("CSV file created: movie_list.csv")

## Generate embeddings and Load them into Azure Managed Redis
## ----------------------------------------------------------
# Using LangChain, this example connects to Azure OpenAI Service to generate embeddings for the dataset. These embeddings are then loaded into [Azure Managed Redis](https://learn.microsoft.com/en-us/azure/azure-cache-for-redis/managed-redis/managed-redis-overview), a fully managed Redis service on Azure, which features the [RediSearch](https://redis.io/docs/latest/develop/interact/search-and-query/) module that includes vector search capability. Finally, a copy of the index schema is saved. That is useful for loading the index into Redis later if you don't want to regenerate the embeddings.
# we will use Azure OpenAI as our embeddings provider
embedding = AzureOpenAIEmbeddings(
    azure_endpoint=RESOURCE_ENDPOINT,
    azure_deployment=DEPLOYMENT_NAME,
    openai_api_key=API_KEY,
    openai_api_version='2024-03-01-preview',
    show_progress_bar=True,
    chunk_size=16)

# Name of the Redis search index to create
index_name = "movieindex"

# Create a connection string for the Redis Vector Store. Uses Redis-py format: https://redis-py.readthedocs.io/en/stable/connections.html#redis.Redis.from_url
# This example assumes TLS is enabled. If not, use "redis://" instead of "rediss://
redis_url = "rediss://:" + REDIS_PASSWORD + "@"+ REDIS_ENDPOINT

# Create and load redis with documents
print("Creating document index, this may take 10+ minutes to complete...")
vectorstore = RedisVectorStore.from_documents(
    documents=movie_list,
    embedding=embedding,
    index_name=index_name,
    redis_url=redis_url
)

# Save index schema so you can reload in the future without re-generating embeddings
print("Saving schema to redis_schema.yaml")
vectorstore.write_schema("redis_schema.yaml")

### Run search queries
# Using the vectorstore we just built in LangChain, we can conduct similarity searches using the `similarity_search_with_score` method. In this example, the top 10 results for a given query are returned.
print("Running similarity search...")
results = vectorstore.similarity_search_with_score(query="Spaceships, aliens, and heroes saving America", k=10)

for doc, score  in enumerate(results):
    movie_title = str(results[doc][0].metadata['Title'])
    similarity_score = str(round((1 - results[doc][1]),4))
    print(movie_title + ' (Score: ' + similarity_score + ')')

### Run hybrid queries
# You can also run hybrid queries. That is, queries that use both vector search and filters based on other parameters in the dataset. In this case, we filter our query results to only movies tagged with the `comedy` genre. One of the advantages of using LangChain with Redis is that metadata is preserved in the index, so you can use it to filter your results. 
from langchain_community.vectorstores.redis.filters import RedisText

query = "Spaceships, aliens, and heroes saving America"
genre = "comedy"

genre_filter = RedisText("Genre") == genre
print("Running hybrid query with filter...")
results = vectorstore.similarity_search_with_score(query, filter=genre_filter, k=10)
for i, j in enumerate(results):
    movie_title = str(results[i][0].metadata['Title'])
    similarity_score = str(round((1 - results[i][1]),4))
    print(movie_title + ' (Score: ' + similarity_score + ')')

print("Done!")
