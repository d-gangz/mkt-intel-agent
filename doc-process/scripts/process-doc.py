"""
Batch processes PDF/DOCX documents using Reducto SDK with variable chunking and saves results in raw and chunk formats.

Input data sources: doc-process/docs/unprocessed/
Output destinations: doc-process/results/raw-form/, doc-process/results/chunk-form/, doc-process/docs/processed/
Dependencies: Reducto API key in environment variable REDUCTO_API_KEY, reducto Python SDK
Key exports: process_documents(), process_single_document(), create_chunk_form(), move_processed_document()
Side effects: Creates directory structure, uploads files to Reducto API, saves JSON outputs, moves processed files
"""

import json
import random
import shutil
import string
from pathlib import Path

from dotenv import load_dotenv
from reducto import Reducto

# Load environment variables from .env file
load_dotenv()


def setup_directories(base_dir: Path) -> dict[str, Path]:
    """Create and return all required directory paths."""
    dirs = {
        "unprocessed": base_dir / "docs" / "unprocessed",
        "processed": base_dir / "docs" / "processed",
        "raw_form": base_dir / "results" / "raw-form",
        "chunk_form": base_dir / "results" / "chunk-form",
    }

    # Create all directories if they don't exist
    for dir_path in dirs.values():
        dir_path.mkdir(parents=True, exist_ok=True)

    return dirs


def generate_document_id() -> str:
    """Generate a random 3-character uppercase document ID (e.g., 'AOU', 'XYZ')."""
    return "".join(random.choices(string.ascii_uppercase, k=3))


def create_chunk_form(raw_result: dict, file_name: str) -> list[dict]:
    """
    Convert raw Reducto result to simplified chunk form.

    Args:
        raw_result: The raw Reducto API response
        file_name: Original filename (e.g., 'hello-there.pdf')

    Returns:
        List of chunks in simplified format with unique chunk IDs
    """
    # Generate unique document ID for this document
    doc_id = generate_document_id()

    chunks = []

    for idx, chunk_data in enumerate(raw_result["result"]["chunks"], start=1):
        # Extract page numbers from blocks
        pages = []
        for block in chunk_data.get("blocks", []):
            if "bbox" in block and "original_page" in block["bbox"]:
                pages.append(block["bbox"]["original_page"])

        # Determine start and end pages
        start_page = min(pages) if pages else None
        end_page = max(pages) if pages else None

        chunk = {
            "chunk_id": f"{doc_id}{idx:03d}",  # e.g., 'AOU001', 'AOU002'
            "text": chunk_data["content"],  # Full markdown text
            "file_name": file_name,
            "start_page": start_page,
            "end_page": end_page,
        }
        chunks.append(chunk)

    return chunks


def process_single_document(
    file_path: Path, client: Reducto, dirs: dict[str, Path]
) -> bool:
    """
    Process a single document through the Reducto pipeline.

    Args:
        file_path: Path to the document to process
        client: Initialized Reducto client
        dirs: Dictionary of directory paths

    Returns:
        True if processing succeeded, False otherwise
    """
    try:
        print(f"\n📄 Processing: {file_path.name}")

        # Upload the document
        print("   ⬆️  Uploading to Reducto...")
        upload_response = client.upload(file=file_path)

        # Parse the document
        print("   🔄 Parsing document...")
        result = client.parse.run(
            document_url=upload_response,  # type: ignore[arg-type]
            options={
                "chunking": {"chunk_mode": "variable", "chunk_size": 3200},
                "table_summary": {"enabled": True},
                "figure_summary": {"enabled": True},
            },
            advanced_options={
                "continue_hierarchy": False,
            },
        )

        # Convert to dictionary
        raw_result = result.model_dump()

        # Save raw form
        raw_output_file = dirs["raw_form"] / f"{file_path.stem}.json"
        print(f"   💾 Saving raw result to: {raw_output_file.name}")
        with open(raw_output_file, "w", encoding="utf-8") as f:
            json.dump(raw_result, f, indent=2, ensure_ascii=False)

        # Create and save chunk form
        chunk_data = create_chunk_form(raw_result, file_path.name)
        chunk_output_file = dirs["chunk_form"] / f"c-{file_path.stem}.json"
        print(f"   💾 Saving chunk form to: {chunk_output_file.name}")
        with open(chunk_output_file, "w", encoding="utf-8") as f:
            json.dump(chunk_data, f, indent=2, ensure_ascii=False)

        # Move to processed folder
        processed_path = dirs["processed"] / file_path.name
        print("   📦 Moving to processed folder...")
        shutil.move(str(file_path), str(processed_path))

        # Print summary
        num_chunks = len(raw_result["result"]["chunks"])
        num_pages = raw_result["usage"]["num_pages"]
        print(f"   ✅ Complete! {num_chunks} chunks created from {num_pages} page(s)")

        return True

    except Exception as e:
        print(f"   ❌ Error processing {file_path.name}: {e}")
        return False


def process_documents():
    """Process all unprocessed documents in the docs/unprocessed folder."""

    # Initialize Reducto client
    client = Reducto()

    # Define base directory (parent of scripts folder = doc-process/)
    base_dir = Path(__file__).parent.parent

    # Setup directory structure
    print("📁 Setting up directories...")
    dirs = setup_directories(base_dir)

    # Find all documents in unprocessed folder
    supported_extensions = {".pdf", ".docx"}
    unprocessed_files = [
        f
        for f in dirs["unprocessed"].iterdir()
        if f.is_file() and f.suffix.lower() in supported_extensions
    ]

    if not unprocessed_files:
        print("\n⚠️  No unprocessed documents found in docs/unprocessed/")
        print("   Supported formats: PDF, DOCX")
        return

    print(f"\n🔍 Found {len(unprocessed_files)} document(s) to process")
    print("=" * 60)

    # Process each document
    success_count = 0
    for file_path in unprocessed_files:
        if process_single_document(file_path, client, dirs):
            success_count += 1

    # Print final summary
    print("\n" + "=" * 60)
    print("🎉 Batch processing complete!")
    print(f"   ✅ Successfully processed: {success_count}/{len(unprocessed_files)}")
    if success_count < len(unprocessed_files):
        print(f"   ❌ Failed: {len(unprocessed_files) - success_count}")


if __name__ == "__main__":
    try:
        process_documents()
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        raise
