# Azure AI Agent Service Demo

This is a interactive demo showing how to migrate the `movie-chat` app into an agent using the Azure AI Foundry service.

It leverages the same data source from the `movie-chat` demo in this repository.

## Services used

* Azure AI Foundry + Agent Service + Azure OpenAI Service (integrated via AI Foundry Project resource)
* Azure AI Search
* Azure Container Apps (for the custom Mermaid to Image tool; optionally, to deploy the Movie Chat app)

## Stay tuned - Work in progress...

TODO:

* IaC for the steps to create and configure AI Foundry with supporting services
* Steps test and deploy the Mermaid to Image custom tool to Azure Container Apps
* Steps to import the Mermaid to Image tool into Azure AI Agent Service
* Steps to test in the Agents Playground
* Steps to write your own host app using Azure AI SDK and interact with the the Azure AI Agent
* Steps to setup MCP Server to call your Agent in Azure AI Agent Service

## Create a new Agent in the Azure AI Foundry

Access the Azure Portal

* Launch the [Azure AI Foundry](https://ai.azure.com/) portal.
* Create a new Azure AI Foundry Project resource (not the older Hub-based project): `movie-chat-agent`
* Set the resource group to be `rg-movie-chat-agent`
* Create a deployment of `gpt-4o` or your preferred model
* Access the "Agents" pane
* Create a new Agent called `movie-agent`
* Agent description (optional): Movie AI assistant that helpfully answers your questions about movies and movie choices.
* Configure these parameters:
     * Temperature: 0.5
     * Top_P: 1.0

## Configure the System Prompt

Use the contents of this [System Prompt - Agent Service](./system_prompt_agent_service.md) for the `Instructions` field.

Note, this is for the monolthic agent setup.  See below for the Connected Agents setup.

## Create a Blob storage account for the movie data

* Create a new Storage Account, e.g. `moviedata1234`
* Select the new storage account
* Select Click Data storage / Containers
* Click "Add Container" called `movies`
* Select the `movies` container and click "Upload"
* Upload the `movie_list.csv` file

## Create an Azure OpenAI service for the integrated vectorisation for AI Search

* Create an Azure OpenAI service, e.g. `movie-chat-models`
* Open the resource with the AI Foundry portal view
* Add a Deployment for "text-embedding-3-large" with the defaults

## Create the Movie AI Search instance

* Create a new AI Search instance `movie-chat-search` in the AI Foundry Project reousrce group `rg-movie-chat-agent` (name must be unique, so add a suffix to the name if required)
* Choose `Standard` tier
* Keep the defaults for the remaining settings
* Proceed to **Create** the instance

## Create the movie index

* Select your new AI Search instance
* Click "Import and vectorize data"
* Select "Azure Blob Storage"
* Select "RAG" for your scenario
* Select your storage account and Blob container `movies`
* Select "Delimited text" for Parsing mode with Delimiter character as `,` and First line contains header is Checked (true)
* Click Next
* Select "plot" for column to vectorize
* Kind: Azure OpenAI
* Select your Azure OpenAI service with the embedding model deployment you created earlier
* Use API key for Authentication type
* Click Next
* Enable Semantic ranker - Checked (true)
* Click Preview and edit fields
* Change the following Target index field names:
     * title -> movie_title
     * origin -> country_of_origin
* Accept changes and click next with "Once" as the Schedule
* Set index name to be "movie-index"
* Click "Create"
* Wait for the index to be created (check the "Indexers", indexer should have Status "Completed" and the "Indexes" document count should be greater than 0)


## Test the New Agent

Click `Try in playground` to test the agent in it's current configuration and ask these questions:

* Hi, what can you do?

```
I can help you with anything related to movies! Here's what I can do:

1. Search for Movies:
     * Find movies by title, actor, genre, or year.
     * Search for movies with specific themes (e.g., comedy about aliens).
     * Identify movies that feature specific actors together.
2. Movie Suggestions:
     * Recommend movies based on actors, genres, or plots.
     * Suggest top-rated movies or hidden gems.
3. Movie Facts:
     * Provide information like cast, plot summaries, release dates, etc.
     * List movies an actor has starred in or the directors of specific films.
4. Aggregations and Charts:
     * Analyze datasets of movies (e.g., number of movies per year, top genres).
     * Create visualizations like bar charts, pie charts, or timelines.
6. Mermaid Diagrams:
     * Generate timeline diagrams for actors, movies, or events.

If you have a specific question or need suggestions, let me know!
```

Type:

* Suggest 3 movies about aliens and that are a comedy.

Sample response:

```
Sorry, I don't know.
```

## Add Knowledge

- Azure AI Search with `movie_list.csv` indexed.  The file is delimited by ',' and vectorised on the plot.
- Search type: Hybrid + semantic

Type:

* I've added a movie index for knowledge .  Try again.

Sample response:

```
Here are three movies about aliens that incorporate comedy:

Aliens in the Attic (2009) - A group of kids discovers aliens in their vacation home and must protect their family while engaging in comedic battles using homemade weapons 1 .
Meet Dave (2008) - Eddie Murphy stars as a spaceship in human form, controlled by tiny alien beings. The aliens learn about human emotions and culture in this humorous adventure 2 .
Spaced Invaders (1990) - A group of bumbling Martians lands on Earth and creates chaos in a small town, leading to comedic situations as they interact with humans 3 .
```

Try this:

* Find me 3 sci-fi movies for this week's movie marathon, provide a short description for each choice.
* Show that as a table with the movie name, cast, year of release and desription as columns.

## Add Tools

- Code Interpreter, add file: `movie_list.csv` (this file is created locally after you run the file `./create-redis-index.py`)
- Add custom tool using OpenAPI Spec([mermaid-tool-func](https://github.com/clarenceb/mermaid-tool-func)):

* **Name**: mermaidjs_to_image_tool
* **Description**: This tool uses an API that renders MermaidJS diagrams into PNG and SVG formats and provides URLs to both the rendered PNG and SVG image files. POST a Mermaid diagram in markdown format to /render and receive a JSON response with the image urls.
* Define schema: <paste contents of openapi.json> or from [https://<your-app>.azurecontainerapps.io/openapi.json](https://<your-app>.azurecontainerapps.io/openapi.json)
* Update the server url in the `openapi.json` file:

```json
"servers": [
    {
      "url": "https://<your-app>.azurecontainerapps.io"
    }
```

Clear and type:

* Which movies has Tom Cruise been in?  Just show me the most recent 10 in descending order.  Show the movie title, cast, plot, and year of release.
* Update the plot with up to 5 words that capture the key themes

Clear and type:

* Show me a chart of all Movies count by year as a bar chart.
* Show me a chart of all Movies count by year as a bar chart - annotate on the chart each year a "Mission: Impossible" movie was released (show which specific movie: original or sequel).  Also, for the year that the mission impossible movie was released, make that bar red.

Clear and type:

* Show me a Mermaid timeline diagram for Tom Cruise showing the year and movies he acted in for each year
* Show me a mermaid pie chart for movies by top 10 genres and movie counts for those genres
* Find the 5 most recent Tom Cruise movies.  Render the result as a Mermaid mindmap diagram.  The root node is the Tom Cruise, linking to the years, and under each year the movie titles.

## Sample chat questions

With `movies-index` AI Search index only (if any questions fail to return a response, ask "why?" or "did you try searching?"):

* Which movies have actors Tom Cruise and Jamie Foxx starred together?
* Find me 3 sci-fi movies for this week's movie marathon, provide a short description for each choice.
* Find me up to 3 movies released in 1987.
* Which movies has Tom Cruise been in?  (not how many results vs later when using code interpreter)
* Who were the supporting cast in those movies?  Show the year and movie title along with the cast.
* Present that as a table.
* Suggest 3 movies about aliens and that are a comedy.
* Show me a table with movie title, actors, plot summary, year, order by year for those movies.

With Code Interpreter and `movie_list.csv` added:

* Which movies has Tom Cruise been in?
* How many movies has Tom Cruise been in?  Just show me the number and a list of the years ordered oldest to my recent.
* Find the top 3 years that had the most movies in them.
* Create me a chart of all Movies count by year as a bar chart.
* Create me a chart of all Movies count by year as a bar chart - annotate on the chart each year a "Mission: Impossible" movie was released (show which specific movie: original or sequel).  Also, for the year that the mission impossible movie was released, make that bar red.

With custom tool (`mermaidjs_to_image_tool`) added as an OpenAPI tool:

* Show me a Mermaid timeline diagram for Tom Cruise showing the year and movies he acted in for each year
* Show me a mermaid pie chart with the years and count by year for all movies you know about
* Find the 5 most recent Tom Cruise movies.  Render the result as a Mermaid mindmap diagram.  The root node is the Tom Cruise, linking to the years, and under each year the movie titles. 

## Sample questions summary

Search:
* Suggest 3 movies about aliens and that are a comedy.
* Find me up to 3 movies released in 1987.
* Find me 3 sci-fi movies for this week's movie marathon, provide a short description for each choice.

Other:
* Find me 3 movies for this week's movie marathon, provide a short description for each choice.
* Search for movies released in 1995.
* Which movies has Tom Cruise been in?
* Which movies have actors Tom Cruise and Jamie Foxx starred together?
* Who were the supporting cast in those movies?  Show the year and movie title along with the cast.
* Show me a table with movie title, actors, plot summary, year, order by year for those movies.
* How many movies has Tom Cruise been in?  Just show me the number and a list of the years ordered oldest to my recent.
* Find the top 3 years that had the most movies in them.
* Show me a chart of Movies by year as a bar chart.
* Show me a Mermaid timeline diagram for Tom Cruise showing the year and movies he acted in for each year
* Show me a pie chart with the years and count by year for all movies you know about.
* Find the 5 most recent Tom Cruise movies.  Render the result as a Mermaid mindmap diagram.  The root node is the Tom Cruise, linking to the years, and under each year the movie titles.

## Show Mermaid to Image custom tool

[mermaid-tool-func](https://github.com/clarenceb/mermaid-tool-func)

Run locally to show how it works, explore the code.

Show the deployed version in Azure Container Apps.

## Connected Agents (splitting up monolithic agent into composable agents and a orchestration agent)

Rearchitect the solution into a main movie chat agent that acts as a coordinator, utilising a number of Connected Agents in Azure AI Foundry Agent Service.

It can also use its own tools, like Code Interpreter.

### Main Agent

**Movie Chat Agent**

- **Description**: Answers movie related questions and fulfills tasks requested by the user using specialised connected agents.
- **Instructions**:

```
You are an AI assistant who can answer questions about movies, make movie suggestions, summarise key movie facts (e.g. release dates, cast, etc.), and perform aggregate and charting operations on movie data.

Follow these rules:
- Make use of the Connected Agents to perform the specific required actions and use the returned information to formulate a final answer to the user's input.
- You can formulate a multi-step plan and then utilise more that one Connected Agent if a series of steps are required to arrived at the final answer.
- Do your best to provide a complete answer but a partial answer is better than no answer.
- Do not use movie facts in your pre-trained knowledge, rely only on the Connected Agents to give you that information and use your reasoning skills to provide an appropriate answer to the user.
- If you really do not know, just provide the reason to the user with a polite message.
- If user asks for a chart, diagram or visualization (except for a Mermaid diagram), then ask connected agents for the required data only (DO NOT ask them for a chart/diagram/visualization) and then use your Code Interpreter to render the chart yourself using the results from the connected agent.
```

- **Knowledge**: None
- **Tools**: Code Interpreter (optional) - if you want to create plots of request or perform further analysis on the results from connected agents

- **Connected Agent**: Movie Search Agent
     - **Unique name**: MovieSearchAgent
     - **Detail the steps to activate the agent**:

     ```
     You can use this connected agent to perform movie searches either with key words or semantic searches (e.g. find similar movies based on plot).
     This agent should be used when a subset of movies need to be returned or analysed.
     Examples for searching, the User might ask:
     - Find me...
     - Search for...
     - Which movies has <actor/cast> been in?
     - Who were the supporting cast in <movie>?
     - Which movie did both <actor1> and <actor2> star in?
     - Suggest 3 movies about aliens and that are a comedy
     - Summarise the plot for <movie>
     - Suggest a movie with a similar plot to <movie>
     ```
- **Connected Agent**: Movie Analysis Agent
     - **Unique name**: MovieAnalysisAgent
     - **Detail the steps to activate the agent**:

     ```
     You can use this connected agent to perform detailed movie analysis, aggregations, summaries, etc.
     If a chart result is expected, then download the image from the connected agent.
     Prefer to use this agent when you need to analyse, aggregate, or filter through all movies.
     Examples for aggregations:
     - How many movies has Tom Cruise been in?
     - Find the top 3 years that had movies in them.
     Examples for charting:
     - Show me a chart of all Movies by year as a bar chart
     ```
- **Connected Agent**: Mermaid Diagram Agent
     - **Unique name**: MermaidDiagramAgent
     - **Detail the steps to activate the agent**:

     ```
     When you specifically need to render a Mermaid diagram as an image you can call this agent.  You need to supply valid Mermaid markdown (YAML) and you'll get back image links (urls) for a PNG and SVG image type.

     Some chart type examples:

     pie title NETFLIX
     "Time spent looking for movie" : 90
     "Time spent watching it" : 10

     graph TD; A-->B; A-->C; B-->D; C-->D;
     ```

### Connected Agents Setup

**Movie Search Agent**
- **Description**: Search a knowledge base for movie information base on the user input.
- **Instructions**:
```
You are a Movie Search AI Agent that uses the available knowledge base to find relevant movie information based on the input query.

Follow these rules:
* Always try searching any attached movie knowledge base, if available, before responding with your answer.
* When searching against Azure AI Search, rewrite queries to be valid Apache Lucene queries against the index schema fields and use vector search for any vectorized fields.
* Use case-insensitive searches
```
- **Knowledge**: movie-index (Azure AI Search index)
- **Tools**: None

**Movie Analysis Agent**

- **Description**: Analyses and extracts movie data from files using Code Interpreter.
- **Instructions**:

```
You are a Movie Analysis AI Agent that uses the Code Interpreter and attached file(s) to extract relevant movie facts, create summaries or aggregations across all matching movies.  You can also and plot results onto a diagram (if required), and perform any other analysis to meet the input query.

Follow these rules:
* To answer aggregation or charting queries, use the code interpreter with attached file(s).
* Use the provided files with the code interpreter to answer queries that would require analysis of a full data set.
* Examples for aggregations:
     - How many movies has Tom Cruise been in? (where Tom Cruise here is the actor)
     - Find the top 3 years that had movies in them.
* Examples for charting:
     - Show me a chart of Movies by year as a bar chart (this can use matplot library in the code interpreter)
```

- **Knowledge**: None
- **Tools**: CodeInterpreter with the file: `movie_list.csv`

**Mermaid Diagram Agent**

- **Description**:
```Renders images from Mermaid markdown input. e.g. graph TD; A-->B; A-->C; B-->D; C-->D;```
- **Instructions**:
```
You are an AI agent that can render images from Mermaid diagrams (Markdown YAML).

When supplied Mermaid Markdown input, you'll use the available tools to render it.

Follow these rules:
* Prefer to render to a PNG image and display it from the returned URLs in the tool response.
* Ensure the image urls are not modified in anyway, don't add any leading or trailing chars, like backslashes "\", for example.
* If the image urls schemes in the url is "http" then change it to be "https".
* If the last char on any urls is a backslash ("\") then remove that char from the url.
* DO NOT try to render the returned image URLs as Markdown.

Some chart type examples:

     pie title NETFLIX
          "Time spent looking for movie" : 90
          "Time spent watching it" : 10

     graph TD; A-->B; A-->C; B-->D; C-->D;

You will respond with this HTML message:

Here is your <a href="<insert-SVG-image-url-here>" target="_blank">**Mermaid Diagram** (click to view)</a> or see preview below:
<p>
<img src="<insert-PNG-image-url-here>" />
</p>
```

- **Knowledge**: None
- **Tools**: OpenAPI 3.0 specified tool (`mermaidjs_to_image_tool`)

## Main Agent Queries

Searches:
* Suggest 3 movies about aliens and that are a comedy.
* Present those as a table (title, plot, year)
* Find me 3 sci-fi movies for this week's movie marathon, provide a short description for each choice.
* What movie genres do you know about?  Limit to the top 10.

Charts:
* Get me all the movie counts by year (limit to the last 30 years).  Create a bar chart of the results.
* Get me all the movie counts by year (limit to the last 30 years) and also all the years for Mission Impossible movies.  Create a bar chart of the results and annotate the year where a mission impossible movie was released (note if it is the original or a sequel).  For the year that the Mission Impossible movie was released, colour that bar red in the chart.

Mermaid diagrams:
* Find the 5 most recent Tom Cruise movies.  Render the result as a Mermaid mindmap diagram.  The root node is the Tom Cruise, linking to the years, and under each year the movie titles.
* Show me a Mermaid timeline diagram for Tom Cruise showing the year and movies he acted in for each year
* Show me a mermaid pie chart for movies by top 10 genres and movie counts for those genres

## Using Azure AI SDK

- TODO

## Using Sematic Kernel Agents Framework with Azure AI Agents

- TODO

## Movie Chat UI (Streamlit)

- TODO: Using Semantic Kernel
