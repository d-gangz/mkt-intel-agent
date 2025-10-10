"""
LangGraph agent for hybrid search and SQL query analysis with structured output.

Input data sources: LanceDB (documents table), SQLite (owid-co2-data.db)
Output destinations: Structured responses with citations
Dependencies: langgraph, langchain-anthropic, lancedb, sqlite3, pydantic
Key exports: app (compiled LangGraph agent), process_queries()
Side effects: Queries LanceDB and SQLite databases, makes Anthropic API calls
"""

import sqlite3
from pathlib import Path
from typing import List

import lancedb  # type: ignore
from dotenv import load_dotenv
from lancedb.embeddings import get_registry  # type: ignore

# from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from pydantic import BaseModel, Field

load_dotenv()

# =============================================================================
# DATABASE CONNECTIONS
# =============================================================================

# Connect to LanceDB
db = lancedb.connect(
    uri="db://alix-partners-48x6ob",
    region="us-east-1",
)

# Configure OpenAI embeddings for LanceDB
embeddings = (
    get_registry()
    .get("openai")
    .create(
        name="text-embedding-3-small",
        dim=512,
    )
)

# SQLite database path
SQLITE_DB_PATH = (
    Path(__file__).parent.parent / "data-process" / "databases" / "owid-co2-data.db"
)


# =============================================================================
# PYDANTIC MODELS FOR STRUCTURED OUTPUT
# =============================================================================


class SearchResult(BaseModel):
    """Single search result from LanceDB hybrid search."""

    chunk_id: str
    text: str
    file_name: str
    start_page: int
    end_page: int
    relevance_score: float


class AgentResponse(BaseModel):
    """Structured response from the agent with citations."""

    response: str = Field(description="The complete answer to the user's query")
    citations: List[str] = Field(
        description="List of chunk_ids used as sources for the response",
        default_factory=list,
    )
    data_summary: str = Field(
        description="Summary of any quantitative data or SQL results used", default=""
    )


# =============================================================================
# TOOL DEFINITIONS
# =============================================================================


@tool
def hybrid_search(query: str, limit: int = 5) -> str:
    """
    Search document database using hybrid search (vector + full-text).

    Use this tool to find information from documents about climate, emissions,
    environmental topics, reports, and qualitative insights.

    Args:
        query: The search query to find relevant document chunks
        limit: Maximum number of results to return (default: 5)

    Returns:
        Formatted string with search results including chunk_ids for citation
    """
    try:
        # Open the documents table
        table = db.open_table("documents")

        # Perform hybrid search
        results = (
            table.search(
                query,
                query_type="hybrid",
                vector_column_name="vector",
                fts_columns="text",
            )
            .limit(limit)
            .to_pandas()
        )

        if results.empty:
            return "No relevant documents found for this query."

        # Format results for the agent
        formatted_results = []
        for idx, row in results.iterrows():
            formatted_results.append(
                f"[CHUNK_ID: {row['chunk_id']}]\n"
                f"Source: {row['file_name']} (pages {row['start_page']}-{row['end_page']})\n"
                f"Relevance: {row['_relevance_score']:.4f}\n"
                f"Content:\n{row['text'][:500]}...\n"
            )

        return "\n---\n".join(formatted_results)

    except Exception as e:
        return f"Error performing hybrid search: {str(e)}"


@tool
def sql_query(sql: str) -> str:
    """
    Execute SQL queries against the CO2 emissions database.

    Use this tool to run SQL queries for quantitative analysis, statistics, trends,
    comparisons, and any data-driven questions about CO2 emissions.

    The database contains global CO2 and greenhouse gas emissions data from 1750-2023
    in a table called 'data'. See the system prompt for complete schema details.

    IMPORTANT: You must generate a valid SQL query based on the user's question and
    the database schema provided in the system prompt. Only SELECT queries are allowed.

    Args:
        sql: The SQL SELECT query to execute against the database

    Returns:
        SQL query results as formatted string with column names and data
    """
    try:
        # Security: Only allow SELECT queries
        sql_upper = sql.strip().upper()
        if not sql_upper.startswith("SELECT"):
            return (
                "Error: Only SELECT queries are allowed. Please provide a SELECT query."
            )

        # Connect to SQLite database
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()

        # Execute the SQL query
        cursor.execute(sql)

        results = cursor.fetchall()
        column_names = [description[0] for description in cursor.description]

        conn.close()

        if not results:
            return "Query executed successfully but returned no results."

        # Format results
        formatted_output = f"SQL Query Executed:\n{sql}\n\n"
        formatted_output += f"Results ({len(results)} rows):\n\n"
        formatted_output += " | ".join(column_names) + "\n"
        formatted_output += "-" * 80 + "\n"

        for row in results:
            formatted_output += (
                " | ".join(str(val) if val is not None else "NULL" for val in row)
                + "\n"
            )

        return formatted_output

    except sqlite3.Error as e:
        return f"SQL Error: {str(e)}\n\nQuery attempted:\n{sql}"
    except Exception as e:
        return f"Error executing SQL query: {str(e)}"


# =============================================================================
# SYSTEM PROMPT WITH DATABASE SCHEMA
# =============================================================================

SYSTEM_PROMPT = """You are a specialized research assistant with access to two powerful tools:

1. **hybrid_search**: Search through document database for qualitative insights, reports, and context
2. **sql_query**: Query the CO2 emissions database for quantitative data and statistics

Note: Before you call a tool, explain why you are calling it.

## Your Capabilities

### Document Search (hybrid_search)
- Search climate and emissions-related documents
- Returns document chunks with unique chunk_ids for citation
- Use for: reports, analyses, explanations, context, qualitative information

### Database Analysis (sql_query)
- Query comprehensive CO2 emissions database (1750-2023)
- 255 countries/regions with detailed emissions metrics
- Use for: statistics, trends, comparisons, quantitative analysis

## CO2 Emissions Database Schema

# Table: data

Global CO2 and greenhouse gas emissions data with economic and demographic context from 1750-2023.

## Columns

| Column | Type | Description | Unit |
|--------|------|-------------|------|
| country | TEXT | Country or region name (includes individual countries and aggregates like 'World', 'Asia', 'OECD') | - |
| year | INTEGER | Year of measurement (1750-2023) | - |
| iso_code | TEXT | ISO 3166-1 alpha-3 country code | - |
| population | REAL | Total population | - |
| gdp | REAL | Gross domestic product in constant 2011 international dollars | USD |
| co2 | REAL | Annual total CO2 emissions | million tonnes |
| co2_per_capita | REAL | Per capita CO2 emissions | tonnes per person |
| co2_growth_abs | REAL | Absolute annual change in CO2 emissions | million tonnes |
| co2_growth_prct | REAL | Percentage annual change in CO2 emissions | percent |
| coal_co2 | REAL | Annual CO2 emissions from coal | million tonnes |
| coal_co2_per_capita | REAL | Per capita CO2 emissions from coal | tonnes per person |
| oil_co2 | REAL | Annual CO2 emissions from oil | million tonnes |
| oil_co2_per_capita | REAL | Per capita CO2 emissions from oil | tonnes per person |
| gas_co2 | REAL | Annual CO2 emissions from gas | million tonnes |
| gas_co2_per_capita | REAL | Per capita CO2 emissions from gas | tonnes per person |
| cement_co2 | REAL | Annual CO2 emissions from cement production | million tonnes |
| cement_co2_per_capita | REAL | Per capita CO2 emissions from cement | tonnes per person |
| flaring_co2 | REAL | Annual CO2 emissions from gas flaring | million tonnes |
| flaring_co2_per_capita | REAL | Per capita CO2 emissions from flaring | tonnes per person |
| co2_including_luc | REAL | Annual CO2 emissions including land-use change | million tonnes |
| co2_including_luc_per_capita | REAL | Per capita CO2 emissions including land-use change | tonnes per person |
| land_use_change_co2 | REAL | Annual CO2 emissions from land-use change | million tonnes |
| cumulative_co2 | REAL | Cumulative CO2 emissions since 1750 | million tonnes |
| cumulative_coal_co2 | REAL | Cumulative CO2 emissions from coal since 1750 | million tonnes |
| cumulative_oil_co2 | REAL | Cumulative CO2 emissions from oil since 1750 | million tonnes |
| cumulative_gas_co2 | REAL | Cumulative CO2 emissions from gas since 1750 | million tonnes |
| share_global_co2 | REAL | Share of global annual CO2 emissions | percent |
| share_global_cumulative_co2 | REAL | Share of global cumulative CO2 emissions | percent |
| total_ghg | REAL | Total greenhouse gas emissions including CO2, methane, and nitrous oxide | million tonnes CO2eq |
| ghg_per_capita | REAL | Per capita greenhouse gas emissions | tonnes CO2eq per person |
| methane | REAL | Annual methane emissions | million tonnes CO2eq |
| methane_per_capita | REAL | Per capita methane emissions | tonnes CO2eq per person |
| nitrous_oxide | REAL | Annual nitrous oxide emissions | million tonnes CO2eq |
| nitrous_oxide_per_capita | REAL | Per capita nitrous oxide emissions | tonnes CO2eq per person |
| consumption_co2 | REAL | Annual consumption-based CO2 emissions (adjusted for trade) | million tonnes |
| consumption_co2_per_capita | REAL | Per capita consumption-based CO2 emissions | tonnes per person |
| trade_co2 | REAL | Net CO2 emissions embedded in trade | million tonnes |
| trade_co2_share | REAL | Share of emissions embedded in trade relative to domestic emissions | percent |
| temperature_change_from_co2 | REAL | Temperature change attributed to CO2 emissions from this country | degrees Celsius |
| temperature_change_from_ch4 | REAL | Temperature change attributed to methane emissions from this country | degrees Celsius |
| temperature_change_from_n2o | REAL | Temperature change attributed to nitrous oxide emissions from this country | degrees Celsius |
| temperature_change_from_ghg | REAL | Total temperature change attributed to all greenhouse gas emissions from this country | degrees Celsius |
| co2_per_gdp | REAL | CO2 emissions per unit GDP (emissions intensity) | kg per international dollar |
| co2_per_unit_energy | REAL | CO2 emissions per unit energy | kg per kilowatt-hour |
| energy_per_capita | REAL | Primary energy consumption per capita | kilowatt-hours per person |
| energy_per_gdp | REAL | Energy consumption per unit GDP | kilowatt-hours per international dollar |
| primary_energy_consumption | REAL | Annual primary energy consumption | terawatt-hours |

## Data Characteristics

- Dataset contains 255 countries/regions including aggregates like 'World', 'Asia', 'OECD', 'EU', income groups
- Time range: 1750-2023 (273 years of historical data)
- Many early historical values (pre-1900) are NULL or zero, data becomes more complete in 20th century
- Includes both individual countries and regional/economic aggregates
- ISO country codes provided for standardization

## Filtering Guidelines

- To exclude aggregate regions when analyzing countries: WHERE country NOT LIKE '%World%' AND country NOT LIKE '%OECD%' AND country NOT LIKE '%income%'
- For recent comprehensive data: WHERE year >= 2000
- For historical analysis: WHERE year >= 1900 (better data availability)
- Common NULL handling: Add AND column_name IS NOT NULL for per capita and derived metrics
- To get only countries with ISO codes: WHERE iso_code IS NOT NULL

## Example Queries

**1. Top 10 CO2 Emitters in 2022**
```sql
SELECT country, co2, co2_per_capita
FROM data
WHERE year = 2022
  AND country NOT LIKE '%World%'
  AND country NOT LIKE '%OECD%'
ORDER BY co2 DESC
LIMIT 10;
```

**2. China's Emission Trend Since 2000**
```sql
SELECT year, co2, coal_co2, oil_co2, gas_co2
FROM data
WHERE country = 'China' AND year >= 2000
ORDER BY year;
```

**3. Per Capita Emissions Comparison**
```sql
SELECT country, co2_per_capita
FROM data
WHERE year = 2022
  AND country IN ('United States', 'China', 'India', 'Germany', 'Brazil')
  AND co2_per_capita IS NOT NULL
ORDER BY co2_per_capita DESC;
```

**4. Global Emissions by Fuel Type (2022)**
```sql
SELECT
  SUM(coal_co2) as total_coal,
  SUM(oil_co2) as total_oil,
  SUM(gas_co2) as total_gas
FROM data
WHERE year = 2022 AND country = 'World';
```

**5. Countries with Fastest Emission Growth (2010-2022)**
```sql
SELECT country,
  MAX(CASE WHEN year = 2022 THEN co2 END) - MAX(CASE WHEN year = 2010 THEN co2 END) as growth
FROM data
WHERE year IN (2010, 2022)
  AND country NOT LIKE '%World%'
  AND iso_code IS NOT NULL
GROUP BY country
HAVING growth IS NOT NULL
ORDER BY growth DESC
LIMIT 10;
```

## Important Guidelines

1. **Always cite your sources**: When using document search results, include the chunk_ids in your citations
2. **Be precise with data**: When presenting SQL results, include relevant context and units
3. **Use appropriate tools**:
   - Use hybrid_search for context, explanations, and qualitative information
   - Use sql_query for statistics, trends, and quantitative analysis
4. **Combine insights**: When relevant, use both tools to provide comprehensive answers
5. **Format your response**: Structure your answer clearly with the response text and citations list

When you provide your final answer, make sure to:
- Give a clear, comprehensive response
- List all chunk_ids used from document searches in the citations
- Summarize any quantitative data used from SQL queries
"""


# =============================================================================
# LANGGRAPH AGENT SETUP
# =============================================================================

# using the gpt-5-nano model with the responses api
llm = ChatOpenAI(
    model="gpt-5-nano",
    use_responses_api=True,
)

# Bind tools to LLM
tools = [hybrid_search, sql_query]
llm_with_tools = llm.bind_tools(tools)


def chatbot(state: MessagesState):
    """
    Main chatbot node that processes messages and calls tools.

    Automatically prepends system prompt to ensure context is maintained.
    """
    messages = state["messages"]

    # Add system prompt if not present
    if not (messages and messages[0].type == "system"):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

    # Invoke LLM with tools
    response = llm_with_tools.invoke(messages)

    return {"messages": [response]}


# Build the state graph
graph_builder = StateGraph(MessagesState)

# Add nodes
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("tools", ToolNode(tools))

# Add edges
graph_builder.add_edge(START, "chatbot")
graph_builder.add_conditional_edges("chatbot", tools_condition)
graph_builder.add_edge("tools", "chatbot")

# Compile graph (no checkpointer - following deployment-first principles)
graph = graph_builder.compile()

# Export as 'app' for LangGraph deployment
app = graph


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def process_queries(queries: List[str], verbose: bool = True) -> List[dict]:
    """
    Process multiple queries through the LangGraph agent.

    Args:
        queries: List of query strings to process
        verbose: If True, print progress information

    Returns:
        List of dictionaries containing query and response information
    """
    results = []

    for idx, query in enumerate(queries, 1):
        if verbose:
            print(f"\n{'='*80}")
            print(f"Processing Query {idx}/{len(queries)}: {query}")
            print(f"{'='*80}\n")

        # Stream the graph execution
        final_response = None
        for event in graph.stream({"messages": [HumanMessage(content=query)]}):  # type: ignore
            for value in event.values():
                last_message = value["messages"][-1]

                if verbose:
                    # Print tool calls and responses
                    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                        print(
                            f"Tool calls: {[tc['name'] for tc in last_message.tool_calls]}"
                        )
                    elif hasattr(last_message, "content") and last_message.content:
                        if last_message.type != "tool":
                            print(f"Response: {last_message.content[:200]}...")

                # Capture final response
                if last_message.type == "ai" and not hasattr(
                    last_message, "tool_calls"
                ):
                    final_response = last_message.content

        # Store result
        results.append(
            {
                "query": query,
                "response": final_response,
                "success": final_response is not None,
            }
        )

        if verbose:
            print(f"\nQuery {idx} completed\n")

    return results


def process_single_query(query: str, verbose: bool = True) -> str:
    """
    Process a single query through the agent and return the response.

    Args:
        query: The query string to process
        verbose: If True, print tool calls and intermediate steps

    Returns:
        The final response string from the agent
    """
    results = process_queries([query], verbose=verbose)
    return results[0]["response"] if results else "No response generated"


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    # Example queries covering different use cases
    example_queries = [
        # Qualitative: Document-based insights
        "What are the key challenges and barriers to reducing emissions mentioned in the documents?",
        # Quantitative: Statistical analysis
        "What is the relationship between GDP and CO2 emissions for European countries between 2010 and 2020?",
        # Quantitative: Trend analysis
        "Which countries had negative emission growth rates in the past 5 years and by how much did their emissions decrease?",
        # Combined: Context + Data
        "How do per capita emissions compare between the US, China, and India in recent years, and what factors explain these differences?",
        # Combined: Insights + Quantification
        "What role does coal play in global emissions according to the documents, and what percentage of total CO2 came from coal in 2022?",
    ]

    print("=" * 80)
    print("LangGraph Agent - Hybrid Search & SQL Query System")
    print("=" * 80)

    # Process example queries
    results = process_queries(example_queries, verbose=True)

    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    for i, result in enumerate(results, 1):
        status = "Success" if result["success"] else "Failed"
        print(f"{status} Query {i}: {result['query'][:80]}...")

    print("\nAgent ready for deployment as 'app'")
