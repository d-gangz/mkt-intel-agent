"""
Converts unprocessed data files (CSV, XLSX) into SQLite databases for SQL querying.

Input data sources: data-process/data/unprocessed/
Output destinations: data-process/databases/
Dependencies: pandas, openpyxl (for XLSX support)
Key exports: process_file(), convert_csv_to_db(), convert_xlsx_to_db()
Side effects: Creates SQLite database files, moves processed files to data/processed/
"""

import shutil
import sqlite3
from pathlib import Path

import pandas as pd


# Directory paths
UNPROCESSED_DIR = Path(__file__).parent / "data" / "unprocessed"
PROCESSED_DIR = Path(__file__).parent / "data" / "processed"
DATABASE_DIR = Path(__file__).parent / "databases"


def ensure_directories():
    """Create necessary directories if they don't exist."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)


def convert_csv_to_db(csv_path: Path, db_path: Path) -> None:
    """
    Convert a CSV file to SQLite database with a single table named 'data'.

    Args:
        csv_path: Path to the CSV file
        db_path: Path where the SQLite database will be created
    """
    print(f"  Reading CSV: {csv_path.name}")
    df = pd.read_csv(csv_path)

    print(f"  Shape: {df.shape[0]} rows, {df.shape[1]} columns")

    # Create SQLite database
    conn = sqlite3.connect(db_path)

    try:
        # Write DataFrame to SQLite with table name "data"
        df.to_sql("data", conn, if_exists="replace", index=False)
        print(f"  ✓ Created table 'data' with {df.shape[0]} rows")
    finally:
        conn.close()


def convert_xlsx_to_db(xlsx_path: Path, db_path: Path) -> None:
    """
    Convert an XLSX file to SQLite database with one table per sheet.

    Args:
        xlsx_path: Path to the XLSX file
        db_path: Path where the SQLite database will be created
    """
    print(f"  Reading XLSX: {xlsx_path.name}")

    # Load Excel file and get all sheet names
    excel_file = pd.ExcelFile(xlsx_path)
    sheet_names = excel_file.sheet_names

    print(f"  Found {len(sheet_names)} sheets: {', '.join(sheet_names)}")

    # Create SQLite database
    conn = sqlite3.connect(db_path)

    try:
        for sheet_name in sheet_names:
            # Read each sheet
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            print(
                f"    - Sheet '{sheet_name}': {df.shape[0]} rows, {df.shape[1]} columns"
            )

            # Use sheet name as table name
            # Note: SQLite table names are case-sensitive
            df.to_sql(sheet_name, conn, if_exists="replace", index=False)
            print(f"      ✓ Created table '{sheet_name}' with {df.shape[0]} rows")
    finally:
        conn.close()


def process_file(file_path: Path) -> None:
    """
    Process a single data file (CSV or XLSX) and convert to SQLite database.

    Args:
        file_path: Path to the file to process
    """
    print(f"\nProcessing: {file_path.name}")

    # Get file extension
    file_ext = file_path.suffix.lower()

    # Determine database name (filename without extension)
    db_name = file_path.stem
    db_path = DATABASE_DIR / f"{db_name}.db"

    try:
        if file_ext == ".csv":
            convert_csv_to_db(file_path, db_path)
        elif file_ext in [".xlsx", ".xls"]:
            convert_xlsx_to_db(file_path, db_path)
        else:
            print(f"  ⚠ Unsupported file type: {file_ext}")
            return

        # Move processed file to processed directory
        dest_path = PROCESSED_DIR / file_path.name
        shutil.move(str(file_path), str(dest_path))
        print(f"  ✓ Moved to: {dest_path.relative_to(Path(__file__).parent)}")
        print(f"  ✓ Database created: {db_path.relative_to(Path(__file__).parent)}")

    except Exception as e:
        print(f"  ✗ Error processing {file_path.name}: {e}")
        raise


def main():
    """Main function to process all files in the unprocessed directory."""
    print("=" * 60)
    print("Data to Database Converter")
    print("=" * 60)

    # Ensure directories exist
    ensure_directories()

    # Check if unprocessed directory exists
    if not UNPROCESSED_DIR.exists():
        print(f"\n⚠ Unprocessed directory not found: {UNPROCESSED_DIR}")
        return

    # Get all CSV and XLSX files
    files = (
        list(UNPROCESSED_DIR.glob("*.csv"))
        + list(UNPROCESSED_DIR.glob("*.xlsx"))
        + list(UNPROCESSED_DIR.glob("*.xls"))
    )

    if not files:
        print(
            f"\n✓ No files to process in {UNPROCESSED_DIR.relative_to(Path(__file__).parent)}"
        )
        return

    print(f"\nFound {len(files)} file(s) to process:")
    for f in files:
        print(f"  - {f.name}")

    # Process each file
    successful = 0
    failed = 0

    for file_path in files:
        try:
            process_file(file_path)
            successful += 1
        except Exception as e:
            failed += 1
            print(f"  Failed: {e}")

    # Summary
    print("\n" + "=" * 60)
    print(f"Summary: {successful} successful, {failed} failed")
    print("=" * 60)


if __name__ == "__main__":
    main()
