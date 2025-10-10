"""
Uploads processed document chunks to LanceDB with vector embeddings and full-text search.

Input data sources: doc-process/results/chunk-form/
Output destinations: LanceDB cloud (alix-partners-48x6ob)
Dependencies: lancedb, openai (via embeddings), python-dotenv
Key exports: DocumentChunk (schema), upload_chunks_to_lancedb()
Side effects: Creates/overwrites 'documents' table in LanceDB, makes OpenAI API calls for embeddings
"""

import json
from pathlib import Path

import lancedb  # type: ignore
from dotenv import load_dotenv
from lancedb.embeddings import get_registry  # type: ignore
from lancedb.pydantic import LanceModel, Vector  # type: ignore

load_dotenv()

# Directory paths
CHUNK_DIR = Path(__file__).parent.parent / "results" / "chunk-form"

# Connect to LanceDB
db = lancedb.connect(
    uri="db://alix-partners-48x6ob",
    region="us-east-1",
)

# Configure OpenAI embeddings
embeddings = (
    get_registry()
    .get("openai")
    .create(
        name="text-embedding-3-small",
        dim=512,  # Can be any value from 128 to 1536 for text-embedding-3-small
    )
)


# Define schema matching chunk JSON structure
class DocumentChunk(LanceModel):
    chunk_id: str
    # This is the source field for OpenAI Embedding API
    text: str = embeddings.SourceField()
    file_name: str
    start_page: int
    end_page: int
    # This vector field stores the OpenAI embedding output
    vector: Vector(embeddings.ndims()) = embeddings.VectorField()  # type: ignore


def load_chunks_from_json_files():
    """Load all chunks from JSON files in chunk-form directory."""
    all_chunks = []

    if not CHUNK_DIR.exists():
        print(f"⚠ Chunk directory not found: {CHUNK_DIR}")
        return all_chunks

    json_files = list(CHUNK_DIR.glob("*.json"))

    if not json_files:
        print(f"⚠ No JSON files found in {CHUNK_DIR}")
        return all_chunks

    print(f"Found {len(json_files)} JSON file(s) to process")

    for json_file in json_files:
        print(f"  Reading: {json_file.name}")
        with open(json_file, "r", encoding="utf-8") as f:
            chunks = json.load(f)
            all_chunks.extend(chunks)

    print(f"✓ Loaded {len(all_chunks)} total chunks")
    return all_chunks


def upload_chunks_to_lancedb():
    """Main function to upload chunks to LanceDB."""
    print("=" * 60)
    print("Document Chunks to LanceDB Uploader")
    print("=" * 60)

    # Load chunks from JSON files
    chunks = load_chunks_from_json_files()

    if not chunks:
        print("\n⚠ No chunks to upload")
        return

    # Create table with overwrite mode
    print("\nCreating 'documents' table in LanceDB...")
    table = db.create_table("documents", schema=DocumentChunk, mode="overwrite")

    # Add chunks to table
    print(f"Uploading {len(chunks)} chunks...")
    table.add(chunks)
    print("✓ Chunks uploaded successfully")

    # Verify data ingestion
    print("\nVerifying data (first 5 chunks):")
    sample = table.search().limit(5).to_pandas()
    print(sample[["chunk_id", "file_name", "start_page", "end_page"]])

    # Create full-text search index on 'text' field
    print("\nCreating full-text search index on 'text' field...")
    table.create_fts_index("text", replace=True)
    index_name = "text_idx"
    table.wait_for_index([index_name])
    print("✓ FTS index created successfully")

    print("\n" + "=" * 60)
    print(f"Summary: {len(chunks)} chunks uploaded to 'documents' table")
    print("=" * 60)


"""
HYBRID SEARCH OUTPUT FORMAT DOCUMENTATION
==========================================

When performing hybrid search on the 'documents' table, the results are returned as a pandas DataFrame
with the following structure:

QUERY EXAMPLE:
--------------
results = (
    table.search(
        "what are the co2 emissions impact",
        query_type="hybrid",
        vector_column_name="vector",
        fts_columns="text",
    )
    .limit(10)
    .to_pandas()
)

OUTPUT COLUMNS:
---------------
1. chunk_id          (str)     - Unique chunk identifier (e.g., "HAQ001", "DAW004")
2. text              (str)     - Full markdown content of the chunk
3. file_name         (str)     - Source PDF filename (e.g., "CO_and_Greenhouse_Gas_Emissions_-_Our_World_in_Data.pdf")
4. start_page        (int)     - Starting page number in source document
5. end_page          (int)     - Ending page number in source document
6. vector            (ndarray) - 512-dimensional embedding vector (float32 array)
7. _relevance_score  (float32) - Hybrid search relevance score (higher = more relevant)

DATAFRAME STRUCTURE:
--------------------
- Type: pandas.DataFrame
- Sorted by: _relevance_score (descending - most relevant first)
- Dtypes:
  * chunk_id, text, file_name: object (string)
  * start_page, end_page: int64
  * vector: object (numpy array)
  * _relevance_score: float32

SAMPLE OUTPUT:
--------------
  chunk_id                                               text  ... _relevance_score
0   HAQ002  ## Explore Data on CO2 and Greenhouse Gas E...  ...         0.032266
1   DAW004  ## Annual CO2 emissions from fossil fuels, ...  ...         0.031514
2   HAQ001  # CO2 and Greenhouse Gas Emissions\n\nBy: H...  ...         0.031319
...

USAGE NOTES FOR QUERY FUNCTION:
--------------------------------
- Results are pre-sorted by relevance (no need to sort again)
- Access top result: results.iloc[0]
- Get chunk text: results.iloc[0]['text']
- Get source info: results.iloc[0][['file_name', 'start_page', 'end_page']]
- Filter by score: results[results['_relevance_score'] > threshold]
- The vector field contains the embedding but typically isn't needed in query results
- Use .to_list() instead of .to_pandas() if you need a list of dictionaries
"""


if __name__ == "__main__":
    upload_chunks_to_lancedb()
