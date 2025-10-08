<!--
Document Type: Learning Notes
Purpose: Understanding Reducto SDK output structure and usage patterns for PDF document processing
Context: Created while implementing document processing pipeline for contextual retrieval
Key Topics: Reducto API structure, chunking strategies, content vs embed fields, contextual retrieval patterns
Target Use: Reference guide for working with Reducto parsed results and implementing RAG systems
-->

# Reducto SDK Learnings

## Overview

Reducto is a document parsing service that converts PDFs into structured, searchable content with intelligent chunking and figure/table descriptions.

## API Usage

### Basic Processing Flow

```python
from reducto import Reducto

client = Reducto()

# 1. Upload document
upload_url = client.upload(file="path/to/document.pdf")

# 2. Parse with chunking options
result = client.parse.run(
    document_url=upload_url,
    options={
        "chunking": {
            "chunk_mode": "variable",  # or "fixed"
            "chunk_size": 3200         # character limit per chunk
        },
        "table_summary": {"enabled": True},
        "figure_summary": {"enabled": True},
    }
)

# 3. Save result
with open("output.json", "w") as f:
    json.dump(result.model_dump(), f, indent=2)
```

### Configuration Options

- **chunk_mode**: `"variable"` (semantic boundaries) or `"fixed"` (strict character limits)
- **chunk_size**: Maximum characters per chunk (e.g., 3200)
- **table_summary**: Generates text descriptions of tables
- **figure_summary**: Generates text descriptions of images/figures

## Output Data Structure

### Root Level Structure

```json
{
  "duration": 13.65,
  "job_id": "fd424e25-facd-4178-b60a-157e77965fc7",
  "result": {
    "chunks": [...],
    "type": "full",
    "custom": null,
    "ocr": null
  },
  "usage": {
    "num_pages": 1,
    "credits": 1.0
  },
  "pdf_url": "https://...",
  "studio_link": "https://studio.reducto.ai/job/..."
}
```

### Chunks Array Structure

Each document is split into chunks based on your `chunk_size` setting:

```json
{
  "result": {
    "chunks": [
      {
        "blocks": [...],      // Granular content breakdown
        "content": "...",     // Full markdown text
        "embed": "...",       // Embedding-optimized text
        "enriched": null,
        "enrichment_success": false
      }
    ]
  }
}
```

### Blocks Array (Granular Content)

Each chunk contains `blocks[]` with detailed metadata:

```json
{
  "bbox": {
    "page": 1,
    "top": 0.105,
    "left": 0.083,
    "width": 0.236,
    "height": 0.064,
    "original_page": 1
  },
  "content": "HOME FOR FUTURE",
  "type": "Title",  // "Title", "Text", "Section Header", "List Item", "Figure"
  "confidence": "high",  // "high" or "low"
  "granular_confidence": {
    "extract_confidence": null,
    "parse_confidence": 0.860
  },
  "image_url": null
}
```

### Content Types in Blocks

- **Title**: Document titles, major headings
- **Section Header**: Section/subsection headings
- **Text**: Body text paragraphs
- **List Item**: Bulleted or numbered list items
- **Figure**: Images with AI-generated descriptions

## Key Fields: `content` vs `embed`

### `content` Field
- **Contains**: Full markdown-formatted text
- **Formatting**: Includes `#` for headers, `-` for lists
- **Use case**: Human-readable display, markdown rendering

### `embed` Field
- **Contains**: Text optimized for vector embeddings
- **Formatting**: May strip some markdown syntax
- **Use case**: Generating embeddings for vector databases

**Note**: In many cases, `content` and `embed` are identical. Reducto may strip formatting in `embed` when it improves embedding quality.

## Accessing Chunk Content

### Single Chunk Access

```python
import json

with open('parsed_result.json') as f:
    data = json.load(f)

# Get first chunk's content
first_chunk = data['result']['chunks'][0]['content']
```

### Multiple Chunks Access

```python
# Extract all chunks as a list
all_chunks = [chunk['content'] for chunk in data['result']['chunks']]

# Or use embed field for embeddings
all_chunks = [chunk['embed'] for chunk in data['result']['chunks']]

# Process each chunk
for idx, chunk_text in enumerate(all_chunks):
    print(f"Chunk {idx + 1}: {len(chunk_text)} chars")
    # Generate embedding, store in vector DB, etc.
```

### Full Document Reconstruction

```python
# Concatenate all chunks to get full document
full_document = "\n\n".join([
    chunk['content'] for chunk in data['result']['chunks']
])
```

## Advanced Usage: Contextual Retrieval

Contextual retrieval improves search accuracy by adding document context to each chunk before embedding.

### Implementation Pattern

```python
import json

def process_with_contextual_retrieval(parsed_result_path):
    """
    Implement contextual retrieval by:
    1. Creating full document context
    2. Generating contextual prefix for each chunk using LLM
    3. Prepending context to each chunk
    4. Embedding the enhanced chunks
    """

    with open(parsed_result_path) as f:
        data = json.load(f)

    chunks = data['result']['chunks']

    # Step 1: Create full document context
    full_document = "\n\n".join([chunk['content'] for chunk in chunks])

    # Step 2-4: Process each chunk with context
    enhanced_chunks = []

    for idx, chunk in enumerate(chunks):
        chunk_content = chunk['content']

        # Generate contextual prefix via LLM
        prefix = generate_contextual_prefix(
            chunk=chunk_content,
            full_document=full_document,
            chunk_index=idx
        )

        # Combine prefix with original chunk
        enhanced_chunk = f"{prefix}\n\n{chunk_content}"
        enhanced_chunks.append(enhanced_chunk)

        # Embed and store
        embedding = generate_embedding(enhanced_chunk)
        store_in_vector_db(embedding, enhanced_chunk)

    return enhanced_chunks


def generate_contextual_prefix(chunk, full_document, chunk_index):
    """
    Call LLM to generate contextual prefix for a chunk.
    """
    prompt = f"""
Here is the full document:
<document>
{full_document}
</document>

Here is the chunk we want to situate within the whole document:
<chunk>
{chunk}
</chunk>

Please give a short succinct context to situate this chunk within the overall document for the purposes of improving search retrieval of the chunk. Answer only with the succinct context and nothing else.
"""

    # Call your LLM (OpenAI, Anthropic, etc.)
    response = llm_client.generate(prompt)
    return response.strip()
```

### Why Contextual Retrieval?

**Without context**: Each chunk is embedded in isolation
- Query: "What is the master bedroom like?"
- Chunk: "Walk-in closet and en-suite bath"
- Result: Poor match (no mention of "bedroom")

**With context**: Each chunk has document context prepended
- Enhanced chunk: "This describes features of the master suite in a 4-bedroom home for sale. Walk-in closet and en-suite bath"
- Result: Better match (mentions "master suite", "bedroom", "home")

## Working with Blocks (Advanced)

Use `blocks[]` when you need:
- **Page numbers**: `block['bbox']['page']`
- **Position data**: `block['bbox']` for coordinates
- **Content type filtering**: Only extract figures, tables, or headers
- **Confidence filtering**: Skip low-confidence extractions

```python
# Example: Extract only high-confidence figures
figures = [
    block for chunk in data['result']['chunks']
    for block in chunk['blocks']
    if block['type'] == 'Figure' and block['confidence'] == 'high'
]

# Example: Get content by page
page_2_content = [
    block['content'] for chunk in data['result']['chunks']
    for block in chunk['blocks']
    if block['bbox']['page'] == 2
]
```

## Tips & Best Practices

1. **Chunk Size**: Use 3200 chars for most RAG applications (balances context and specificity)
2. **Variable vs Fixed**: Prefer `"variable"` mode for semantic coherence
3. **Enable Summaries**: Always enable `table_summary` and `figure_summary` for rich content
4. **Use `embed` field**: For vector databases, prefer `embed` over `content`
5. **Contextual Retrieval**: Implement for 30-50% retrieval accuracy improvement
6. **Store Metadata**: Save `job_id` and `studio_link` for debugging

## Example Output Characteristics

For a 1-page PDF (~1,587 characters):
- **Chunks**: 1 chunk (under 3200 char limit)
- **Blocks**: 21 blocks (mix of titles, text, figures, headers)
- **Figures**: 4 figure descriptions generated by AI
- **Processing time**: ~13 seconds

For larger documents:
- Multiple chunks in `chunks[]` array
- Each chunk ≤ `chunk_size` characters
- Semantic boundaries preserved in `"variable"` mode

## Related Files

- [process-doc.py](./process-doc.py) - Main processing script
- [results/parsed_result.json](./results/parsed_result.json) - Example output
- [unstructured-real-estate.pdf](./unstructured-real-estate.pdf) - Sample input PDF
