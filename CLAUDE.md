# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Market Intelligence Agent - A hybrid search system combining document processing and database querying. Uses Reducto SDK for document chunking and will integrate LangGraph agents for intelligent search orchestration.

**Current Phase**: Document processing and data pipeline setup (Phase 1)
**Next Phase**: LangGraph agent implementation for hybrid search

## Development Commands

### Package Management
```bash
# Install all dependencies
uv sync

# Add runtime dependency
uv add package-name

# Add development dependency
uv add --dev package-name

# Run Python scripts (automatically uses project venv)
uv run python script.py
```

### Code Quality
```bash
# Format code
uv run black .

# Lint code
uv run ruff check .

# Type check
uv run mypy .
```

### Document Processing
```bash
# Process documents from unprocessed folder
cd doc-process/scripts
uv run python process-doc.py
```

### Data Processing
```bash
# Convert CSV/XLSX files to SQLite databases
uv run python data-process/data-to-db.py

# Query SQLite databases
sqlite3 -header -column data-process/databases/{db_name}.db "SELECT * FROM data LIMIT 5;"
```

## Architecture

### Two-Pipeline System

**1. Document Processing Pipeline (`doc-process/`)**
- Input: PDFs/DOCX in `docs/unprocessed/`
- Processing: Reducto SDK with variable chunking (3200 chars)
- Outputs:
  - Raw form: `results/raw-form/` - Complete Reducto API responses
  - Chunk form: `results/chunk-form/` - Simplified format for RAG (prefix: `c-`)
- Processed files moved to: `docs/processed/`

**2. Data Processing Pipeline (`data-process/`)**
- Input: CSV/XLSX files in `data/unprocessed/`
- Processing: Conversion to SQLite databases
- Output: SQLite `.db` files in `databases/`
- Database structure:
  - CSV files → Single table named `data`
  - XLSX files → Multiple tables (one per sheet, named after sheet)
- Processed files moved to: `data/processed/`

### Data Registry System

**Database Registry**: `data-process/data/data_db.json`

Structure for LLM-powered database search:
```json
{
  "database_id": "DB001",
  "database_name": "filename-without-extension",
  "source_file": "original-file.csv",
  "text": "Searchable description of entire database...",
  "tables": [
    {
      "table_name": "data (CSV) or SheetName (XLSX)",
      "text": "Description of this specific table...",
      "schema": "Markdown schema with columns, types, examples..."
    }
  ]
}
```

**Purpose**: Enables LLM to:
1. Search registry to find relevant databases
2. Understand table structure and relationships
3. Generate accurate SQL queries
4. Know which database file to query

### Document Chunk Format

Each processed document chunk (in `doc-process/results/chunk-form/`):
```json
{
  "chunk_id": "AOU001",
  "text": "Full markdown content...",
  "file_name": "report.pdf",
  "start_page": 1,
  "end_page": 4
}
```

**Chunk ID Format**:
- 3 random uppercase letters + 3-digit number
- Example: `AOU001`, `AOU002`, `XYZ001`
- Generated fresh for each document

## Key Implementation Details

### Document Processing
- Uses Reducto SDK with variable chunking mode
- Parallel processing (default: 5 documents max)
- AI-generated summaries for tables and figures
- `continue_hierarchy: False` for clean chunk boundaries

### Database Processing
- CSV files become single-table databases (table name: `data`)
- XLSX files become multi-table databases (one table per sheet)
- Database name matches source filename (no extension)
- SQL queries for CSV: `SELECT * FROM data WHERE ...`
- SQL queries for XLSX: `SELECT * FROM SheetName WHERE ...`

### File Headers (Standardized Documentation)

All `.py` files must include this header format:
```python
"""
One-line purpose description.

Input data sources: where/data/comes/from/
Output destinations: where/output/goes/
Dependencies: Required packages, APIs, env vars
Key exports: main_function(), helper_function()
Side effects: File creation, API calls, etc.
"""
```

### Registry Update Process

When adding new data files:
1. Drop files in `data-process/data/unprocessed/`
2. Run `uv run python data-process/data-to-db.py`
3. Use prompt template in `data-process/data/table-describe.md` to generate registry entry
4. Manually append entry to `data_db.json`

## Future LangGraph Integration

### Planned Agent Architecture

Follow principles in `langgraph-dev-guide.md`:
- Use `create_react_agent` for basic agents
- Prefer Anthropic models: `claude-3-5-sonnet-20241022`
- Export compiled graph as `app`
- No checkpointer unless explicitly needed
- Use `MessagesState` when sufficient

### Planned Tools

1. **Document Search Tool**: Semantic search across chunk registry
2. **Database Search Tool**: SQL query generation and execution
3. **Answer Synthesis**: Combine results from multiple sources

### Deployment Structure
```
./agent.py          # Main LangGraph agent (exports: app)
./langgraph.json    # LangGraph configuration
```

## Environment Variables

Required in `.env`:
```
REDUCTO_API_KEY=your_reducto_api_key
```

## Important Patterns

### Always use uv commands
- `uv run python script.py` (NOT `python script.py`)
- `uv add package` (NOT `pip install package`)

### Database Queries
- Use `sqlite3` CLI for querying: `sqlite3 -header -column path/to/db.db "SQL_QUERY"`
- CSV databases: Always use `FROM data`
- XLSX databases: Use sheet name as table name

### Parallel Processing
- Document processing: Max 5 concurrent uploads to Reducto API
- Database conversion: Sequential (fast enough for typical files)

## Project Structure

```
mkt-intel-agent/
├── doc-process/
│   ├── scripts/process-doc.py       # Main document processor
│   ├── docs/
│   │   ├── unprocessed/             # Drop PDFs/DOCX here
│   │   └── processed/               # Successfully processed docs
│   ├── results/
│   │   ├── raw-form/                # Full Reducto responses
│   │   └── chunk-form/              # Simplified RAG format
│   └── reducto-learnings.md         # Reducto SDK documentation
├── data-process/
│   ├── data-to-db.py                # CSV/XLSX to SQLite converter
│   ├── data/
│   │   ├── unprocessed/             # Drop data files here
│   │   ├── processed/               # Successfully processed data
│   │   ├── data_db.json             # Database registry for LLM
│   │   └── table-describe.md        # Prompt for generating registry entries
│   └── databases/                   # SQLite database files
├── langgraph-dev-guide.md           # LangGraph coding principles
├── pyproject.toml                   # Dependencies and tooling config
└── README.md                        # Project overview
```

## Testing Approach

No formal test framework yet. Testing strategy:
- Document processing: Drop test files in `unprocessed/`, verify outputs
- Database conversion: Check `.db` files with `sqlite3` CLI
- LangGraph agents (future): Test small components before complex graphs
