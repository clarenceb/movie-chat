# Azure AI Agent Service Demo

This is a interactive demo showing how to build an agent in the Azure AI Foundry and Azure AI Agent Service.

It leverages the same data source from the `movie-chat` demo in this repository.

## Services used

* Azure AI Foundry
* Azure AI Agent Service
* Azure AI Search
* Azure OpenAI Service
* Azure Container Apps (for the custom Mermaid to Image tool)

## Stay tuned - Work in progress...

TODO:

* Steps to create and configure AI Foundry with supporting services
* Steps test and deploy the Mermaid to Image custom tool to Azure Container Apps
* Steps to import the Mermaid to Image tool into Azure AI Agent Service
* Steps to test in the Agents Playground
* Steps to write your own host app using Azure AI SDK and interact with the the Azure AI Agent
* Steps to setup MCP Server to call your Agent in Azure AI Agent Service

## Create a new Agent in the Azure AI Foundry

Access the Azure Portal

* Create a Azure AI Hub
* Create a new Azure AI Project
* Launch the [Azure AI Foundry](https://ai.azure.com/) portal.
* Access the "Agents" pane
* Create a new Agent
* Configure these parameters:
     * Temperature: 0.5
     * Top_P: 1.0


## Configure the System Prompt

Use this [System Prompt - Agent Service](./system_prompt_agent_service.md)

## Test the New Agent

Ask these questions:

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

* Which movies has Tom Cruise been in?

```
Sorry, I don't know. It seems I couldn't access the relevant data source to find the movies Tom Cruise has been in. If you have a dataset or file, you can upload it, and I can help analyze it!
```

## Add Knowledge

- Azure AI Search with `movie_list.csv` indexed.  The file is delimited by ',' and vectorised on the plot.
- Search type: Hybrid + semantic

## Add Tools

- Code Interpreter, add file: `movie_list.csv`
- Add custom tool using OpenAPI Spec: [mermaid-tool-func](https://github.com/clarenceb/mermaid-tool-func)

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
* Show me a chart of Movies count by year as a bar chart.
* Show me a chart of Movies count by year as a bar chart - annotate on the chart each year a "Mission: Impossible" movie was released (show which specific movie: original or sequel).

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
