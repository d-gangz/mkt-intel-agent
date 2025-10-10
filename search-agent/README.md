<!--
Document Type: Technical Documentation
Purpose: Explains the LangGraph search agent architecture and usage
Context: Created for the search-agent implementation with hybrid search and SQL capabilities
Key Topics: LangGraph agent, tool usage, deployment, testing
Target Use: Reference guide for developers using or deploying the agent
-->

# Search Agent

LangGraph-based agent that combines hybrid document search and SQL query capabilities for comprehensive CO2 emissions research.

## Overview

This agent provides intelligent access to two data sources:
1. **LanceDB** - Vector + full-text hybrid search across document chunks
2. **SQLite** - Quantitative CO2 emissions data (1750-2023)

## Architecture

```
User Query → LangGraph Agent → Tool Selection → Results
                  ↓
          System Prompt (with DB schema)
                  ↓
         [hybrid_search] [sql_query]
                  ↓              ↓
              LanceDB        SQLite
```

### Components

- **agent.py** - Main LangGraph agent implementation
  - `app` - Compiled graph (export for deployment)
  - `hybrid_search` - Tool for document search
  - `sql_query` - Tool for SQL execution
  - `process_queries()` - Batch query processor
  - `process_single_query()` - Single query processor
  - Includes example queries when run as main script

- **langgraph.json** - LangGraph deployment configuration

## Tools

### 1. hybrid_search(query: str, limit: int = 5)

Searches document database using vector + full-text hybrid search.

**Use for:**
- Qualitative insights
- Document context
- Explanations
- Reports and analyses

**Returns:**
```
[CHUNK_ID: ABC123]
Source: filename.pdf (pages 1-5)
Relevance: 0.8542
Content: Document text excerpt...
```

### 2. sql_query(sql: str)

Executes SQL SELECT queries against CO2 emissions database.

**Use for:**
- Statistics and trends
- Country comparisons
- Time series analysis
- Quantitative data

**Database Schema:**
- Table: `data`
- 255 countries/regions
- 1750-2023 time range
- 45+ emission metrics

See system prompt in agent.py for complete schema documentation.

## Usage

### Running the Agent

```python
from agent import process_single_query, process_queries

# Single query
response = process_single_query(
    "What were the top CO2 emitters in 2022?",
    verbose=True
)
print(response)

# Multiple queries
queries = [
    "What are the main emission sources?",
    "Compare China and USA emissions trends",
    "Which countries reduced emissions most?"
]
results = process_queries(queries, verbose=True)
```

### Testing

```bash
# Run agent with example queries
cd search-agent
uv run python agent.py
```

### Deployment with LangGraph

```bash
# Deploy to LangGraph Cloud
langgraph deploy

# Or run locally
langgraph dev
```

## System Prompt

The agent uses a comprehensive system prompt that includes:
- Tool descriptions and usage guidelines
- Complete CO2 database schema with all columns
- Data characteristics and filtering guidelines
- Example SQL queries
- Citation requirements

## Response Format

The agent is designed to provide structured responses:
- Clear, comprehensive answer
- Citations (chunk_ids from document searches)
- Summary of quantitative data used

## Environment Variables

Required in `.env`:
```
ANTHROPIC_API_KEY=your_anthropic_key
OPENAI_API_KEY=your_openai_key  # For embeddings
```

## Dependencies

Core:
- `langgraph` - Agent framework
- `langchain-anthropic` - LLM (Claude 3.5 Sonnet)
- `lancedb` - Vector database
- `openai` - Embeddings (text-embedding-3-small)
- `sqlite3` - SQL database

## Example Queries

The agent.py script includes 5 example queries demonstrating different use cases:

**Qualitative (Document Search):**
```
"What are the key challenges and barriers to reducing emissions mentioned in the documents?"
```

**Quantitative (Statistical Analysis):**
```
"What is the relationship between GDP and CO2 emissions for European countries between 2010 and 2020?"

"Which countries had negative emission growth rates in the past 5 years and by how much did their emissions decrease?"
```

**Combined (Context + Data):**
```
"How do per capita emissions compare between the US, China, and India in recent years, and what factors explain these differences?"

"What role does coal play in global emissions according to the documents, and what percentage of total CO2 came from coal in 2022?"
```

## Development Notes

### Following LangGraph Best Practices

Per `langgraph-dev-guide.md`:
- Uses `MessagesState` for state management
- No checkpointer (stateless deployment-first approach)
- Exports graph as `app` for LangGraph Cloud
- Uses Anthropic's Claude 3.5 Sonnet (recommended model)
- Temperature set to 0 for consistent outputs

### Security

- SQL queries are restricted to SELECT only
- Input validation on SQL tool
- Read-only database access

## Troubleshooting

**LanceDB Connection Issues:**
- Ensure documents have been uploaded via `doc-process/scripts/doc-to-lance.py`
- Check LanceDB credentials and region

**SQLite Issues:**
- Verify database exists at: `data-process/databases/owid-co2-data.db`
- Ensure database has data with: `sqlite3 path/to/db.db "SELECT COUNT(*) FROM data;"`

**API Key Issues:**
- Check `.env` file has both ANTHROPIC_API_KEY and OPENAI_API_KEY
- Verify keys are valid and have proper permissions

## Future Enhancements

- [ ] Add structured output with Pydantic models
- [ ] Implement result caching
- [ ] Add query validation and suggestions
- [ ] Support for more complex multi-step reasoning
- [ ] Integration with additional data sources
