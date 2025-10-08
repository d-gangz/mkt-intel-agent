# Market Intelligence Agent

A LangGraph-based search agent that combines document retrieval and database querying to answer questions based on processed documents and structured data.

## Overview

This project implements an intelligent search system that:
- Processes PDF and DOCX documents into searchable chunks
- Uses LangGraph agents to orchestrate hybrid search across document chunks and database records
- Synthesizes answers from multiple data sources based on user queries
- Provides a script-based interface for running queries and inspecting results

## Project Structure

```
mkt-intel-agent/
├── doc-process/              # Document processing pipeline
│   ├── scripts/
│   │   └── process-doc.py   # Main document processing script
│   ├── docs/
│   │   ├── unprocessed/     # Drop documents here for processing
│   │   └── processed/       # Successfully processed documents
│   ├── results/
│   │   ├── raw-form/        # Full Reducto API responses
│   │   └── chunk-form/      # Simplified chunk format for RAG
│   ├── reducto-learnings.md # Reducto SDK documentation
│   └── langgraph-dev-guide.md
├── pyproject.toml           # Python dependencies
└── README.md               # This file
```

## Features

### Document Processing
- **Batch Processing**: Automatically processes all documents in `docs/unprocessed/`
- **Intelligent Chunking**: Uses Reducto SDK with variable chunking (3200 chars)
- **Figure & Table Extraction**: AI-generated descriptions for images and tables
- **Dual Output Formats**:
  - **Raw form**: Complete Reducto API response with full metadata
  - **Chunk form**: Simplified format optimized for retrieval systems

### Chunk Format
Each processed chunk contains:
```json
{
  "chunk_id": "AOU001",           // Unique ID (3 random chars + running number)
  "text": "Full markdown text...", // Content from the document
  "file_name": "report.pdf",       // Original filename
  "start_page": 1,                 // First page in this chunk
  "end_page": 4                    // Last page in this chunk
}
```

### LangGraph Agent (Planned)
- **Document Search Tool**: Semantic search across processed document chunks
- **Database Search Tool**: Query structured data in databases
- **Answer Synthesis**: LangGraph agent orchestrates tool calls and combines results
- **Script-based Interface**: Run queries via Python scripts and inspect results

## Setup

### Prerequisites
- Python 3.12+
- [uv](https://github.com/astral-sh/uv) for dependency management
- Reducto API key

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd mkt-intel-agent
   ```

2. **Install dependencies**
   ```bash
   uv sync
   ```

3. **Set up environment variables**
   Create a `.env` file in the project root:
   ```bash
   REDUCTO_API_KEY=your_reducto_api_key_here
   ```

## Usage

### Processing Documents

1. **Add documents** to the `doc-process/docs/unprocessed/` folder
   - Supported formats: PDF, DOCX

2. **Run the processing script**
   ```bash
   cd doc-process/scripts
   uv run python process-doc.py
   ```

3. **Output**:
   - Raw results saved to `doc-process/results/raw-form/`
   - Chunk results saved to `doc-process/results/chunk-form/` (with `c-` prefix)
   - Original documents moved to `doc-process/docs/processed/`

### Example Processing Output

```
📁 Setting up directories...

🔍 Found 2 document(s) to process
============================================================

📄 Processing: market-analysis.pdf
   ⬆️  Uploading to Reducto...
   🔄 Parsing document...
   💾 Saving raw result to: market-analysis.json
   💾 Saving chunk form to: c-market-analysis.json
   📦 Moving to processed folder...
   ✅ Complete! 12 chunks created from 25 page(s)

📄 Processing: competitor-research.docx
   ⬆️  Uploading to Reducto...
   🔄 Parsing document...
   💾 Saving raw result to: competitor-research.json
   💾 Saving chunk form to: c-competitor-research.json
   📦 Moving to processed folder...
   ✅ Complete! 8 chunks created from 15 page(s)

============================================================
🎉 Batch processing complete!
   ✅ Successfully processed: 2/2
```

## Document Processing Pipeline

```
┌─────────────────┐
│  Drop PDFs/DOCX │
│  in unprocessed │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Upload to       │
│ Reducto API     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Parse with      │
│ - Variable      │
│   chunking      │
│ - Figure/Table  │
│   summaries     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Save Results    │
│ - Raw form      │
│ - Chunk form    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Move to         │
│ processed/      │
└─────────────────┘
```

## Configuration

### Chunking Settings
Modify in `doc-process/scripts/process-doc.py`:
```python
options={
    "chunking": {
        "chunk_mode": "variable",  # or "fixed"
        "chunk_size": 3200         # characters per chunk
    },
    "table_summary": {"enabled": True},
    "figure_summary": {"enabled": True},
}
```

### Chunk ID Format
- **Document Prefix**: 3 random uppercase letters (e.g., `AOU`, `XYZ`)
- **Chunk Number**: Zero-padded 3-digit number (`001`, `002`, `003`)
- **Example IDs**: `AOU001`, `AOU002`, `XYZ001`

## Development Phases

### Phase 1: Document Processing ✅ (Current)
- [x] Batch document processing pipeline
- [x] Reducto SDK integration for chunking
- [x] Dual output format (raw + chunk form)
- [x] Automatic file management

### Phase 2: LangGraph Agent (Next)
- [ ] Vector database integration for document chunks
- [ ] Database connector for structured data
- [ ] LangGraph agent with search tools
- [ ] Query script interface
- [ ] Answer synthesis logic

### Phase 3: Future Enhancements
- [ ] Support for additional document formats
- [ ] Advanced retrieval strategies
- [ ] Query result caching
- [ ] Performance monitoring

## Dependencies

Main dependencies (see `pyproject.toml` for full list):
- **reducto**: Document parsing and chunking SDK
- **python-dotenv**: Environment variable management
- **langgraph**: Agent orchestration framework (to be integrated)

## Documentation

- [Reducto SDK Learnings](doc-process/reducto-learnings.md) - Complete guide to Reducto output structure and usage
- [LangGraph Development Guide](doc-process/langgraph-dev-guide.md) - Agent implementation patterns

## How It Will Work

Once the LangGraph agent is implemented, you'll be able to:

1. **Run queries via script**:
   ```bash
   uv run python query.py "What are the key market trends in Q3?"
   ```

2. **Agent orchestrates search**:
   - Determines which tools to use (document search, database query, or both)
   - Executes searches in parallel when possible
   - Combines results from multiple sources

3. **Inspect results**:
   - View synthesized answers
   - See source chunks and data used
   - Review agent's reasoning process

No UI needed—just scripts and terminal output for maximum flexibility and debugging visibility.
