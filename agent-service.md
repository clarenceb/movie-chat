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
* Show me a chart of all Movies count by year as a bar chart.
* Show me a chart of all Movies count by year as a bar chart - annotate on the chart each year a "Mission: Impossible" movie was released (show which specific movie: original or sequel).

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
