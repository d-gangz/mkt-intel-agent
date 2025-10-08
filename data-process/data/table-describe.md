<!--
Document Type: Process Documentation
Purpose: Prompt template for generating comprehensive data table descriptions for the data_db.json registry
Context: Used when adding new CSV datasets to the market intelligence agent's database
Key Topics: Data analysis, schema extraction, searchable descriptions, SQL query generation
Target Use: Process guide for LLM to analyze CSV files and create structured metadata
-->

# Data Table Description Generator

## Task Overview

Analyze the provided data file (CSV or XLSX) and generate a comprehensive JSON object that will be added to the `data_db.json` registry. This JSON object enables the LLM agent to:
1. **Discover** the database when processing user queries (via searchable text description)
2. **Understand** the table structure and columns (via detailed schema)
3. **Generate** accurate SQL queries (via schema with types, descriptions, and examples)

**Note**: For XLSX files with multiple sheets, each sheet becomes a separate table within the same database. For CSV files, there is a single table named "data".

## Required Output Format

Generate a single JSON object with the following structure:

```json
{
  "database_id": "DB00X",
  "database_name": "filename-without-extension",
  "source_file": "exact-filename.csv or exact-filename.xlsx",
  "text": "Comprehensive searchable description of the entire database...",
  "tables": [
    {
      "table_name": "data (for CSV) or sheet_name (for XLSX)",
      "sheet_name": "SheetName (XLSX only - optional field)",
      "text": "Description of this specific table...",
      "schema": "Markdown-formatted schema (see below)"
    }
  ]
}
```

**For CSV files**: Create one table entry with `table_name: "data"`
**For XLSX files**: Create one table entry per sheet with `table_name` matching the sheet name, and include optional `sheet_name` field

## Field Requirements

### 1. `database_id` (String)
- Format: `DB001`, `DB002`, `DB003`, etc.
- Increment from the last database_id in the existing `data_db.json` file
- **Action**: Check the current highest database_id and increment by 1

### 2. `database_name` (String)
- Filename without extension (this becomes the SQLite database filename)
- Example: `owid-co2-data` (from `owid-co2-data.csv`)
- Example: `financial-data` (from `financial-data.xlsx`)

### 3. `source_file` (String)
- Exact filename including extension
- Example: `owid-co2-data.csv` or `financial-data.xlsx`

### 4. `text` (String) - **CRITICAL FOR DATABASE-LEVEL SEARCHABILITY**

This field is the **primary discovery mechanism** at the database level. It must be extremely comprehensive and keyword-rich, describing what the entire database contains.

**For CSV files**: Describe the single table's contents
**For XLSX files**: Describe all sheets/tables collectively, mentioning what data domains they cover

**Structure your text with these sections:**

#### Opening Summary
- Dataset name and source
- Coverage (countries, regions, time period)
- Total scope (e.g., "273 years of historical data")

#### Detailed Content Breakdown
Use **CAPITALIZED SECTION HEADERS** followed by detailed descriptions:

- **PRIMARY DATA CATEGORY**: Describe the main data with specifics (units, breakdowns, variations)
- **SECONDARY DATA CATEGORY**: Additional metrics and how they relate to primary data
- **AGGREGATIONS**: Cumulative, totals, averages, etc.
- **DERIVED METRICS**: Calculated fields (per capita, growth rates, ratios)
- **CONTEXTUAL DATA**: Supporting information (demographics, economics, geography)
- **COMPARATIVE METRICS**: Share percentages, rankings, relative measures

For each category:
- List specific column types available
- Mention units (tonnes, dollars, percentages, etc.)
- Explain what the data measures
- Note important variations (absolute vs per capita, annual vs cumulative)

#### Coverage Details
- Geographic coverage (countries, regions, aggregates)
- Time range and granularity
- Data completeness notes
- Special identifiers (ISO codes, etc.)

#### "PERFECT FOR QUERIES ABOUT:" Section
This is **extremely important**. List 30-50+ specific example questions using natural language:

**Format**: Write actual questions a user would ask:
- "Which countries have the highest X?"
- "How has Y changed in [country] since [year]?"
- "What is the per capita Z for [country]?"
- "Compare A vs B across countries"
- "Show trend of X over time for [region]"
- "What percentage of global Y comes from Z?"

**Include variations**:
- Comparison queries (A vs B)
- Trend queries (over time)
- Ranking queries (top/bottom N)
- Filtering queries (by region, year, threshold)
- Aggregation queries (totals, averages, sums)
- Relationship queries (correlation, dependency)

**Goal**: Maximum keyword density and query pattern coverage so the LLM can easily match user questions to this database.

### 5. `tables` (Array of Table Objects)

Each table object in the array contains:

#### 5.1 `table_name` (String)
- **For CSV**: Always `"data"`
- **For XLSX**: Use the sheet name (e.g., `"Revenue"`, `"Expenses"`, `"Forecasts"`)
- This becomes the actual SQL table name in the database

#### 5.2 `sheet_name` (String - Optional, XLSX only)
- Original sheet name from the XLSX file
- Helps trace back to the source
- Omit this field for CSV files

#### 5.3 `text` (String)
- Table-level description: what this specific table contains
- For CSV: Similar to database-level but focused on the single table
- For XLSX: Focused description of what this particular sheet/table contains

#### 5.4 `schema` (String - Markdown Format)

The schema should be formatted as **well-structured Markdown text** for token efficiency and readability.

**Template Structure:**

````markdown
# Table: {table_name}

{One-sentence description of what this table contains and its purpose}

## Columns

| Column | Type | Description | Unit |
|--------|------|-------------|------|
| column_name_1 | TEXT | Clear description of what this column contains | - |
| column_name_2 | INTEGER | Description here | - |
| column_name_3 | REAL | Description here | tonnes |
| column_name_4 | REAL | Description here | percent |
| ... | ... | ... | ... |

## Data Characteristics

- Dataset contains X entities (countries, companies, etc.) including aggregates
- Time range: YYYY-YYYY (N years/months)
- Geographic coverage: specific regions, countries
- Data quality: completeness notes, NULL patterns, historical gaps
- Special identifiers: ISO codes, unique IDs, categorical groups

## Filtering Guidelines

- To exclude aggregates: `WHERE column NOT LIKE '%pattern%'`
- For recent data: `WHERE year >= YYYY`
- Common filters: specific patterns users should know
- NULL handling: which columns commonly have NULLs
- Important groupings or categories to filter by

## Example Queries

**1. Basic Filtering and Top N**
```sql
SELECT col1, col2 FROM table_name
WHERE year = 2022
ORDER BY col2 DESC
LIMIT 10;
```

**2. Time Series Aggregation**
```sql
SELECT year, SUM(metric) as total
FROM table_name
WHERE entity = 'X'
GROUP BY year
ORDER BY year;
```

**3. Cross-Entity Comparison**
```sql
SELECT entity, metric_per_capita
FROM table_name
WHERE year = 2022 AND metric_per_capita IS NOT NULL
ORDER BY metric_per_capita DESC;
```

**4. Filtered Aggregation**
```sql
SELECT category, AVG(value) as avg_value
FROM table_name
WHERE year >= 2000 AND entity NOT LIKE '%Aggregate%'
GROUP BY category;
```

**5. Multi-Column Analysis**
```sql
SELECT entity, col1, col2, col3
FROM table_name
WHERE entity = 'SpecificEntity' AND year = 2022;
```
````

**Detailed Field Guidelines:**

#### Table Name & Description
- **Table name**: SQL-friendly (lowercase, underscores, descriptive)
  - Examples: `co2_emissions`, `gdp_by_country`, `global_trade_data`
- **Description**: One sentence capturing purpose and scope

#### Columns Table
For each important column (20-50+ columns recommended):

| Field | Guidelines |
|-------|-----------|
| **Column** | Exact name as in CSV (use SQL-friendly snake_case) |
| **Type** | `TEXT` (strings), `INTEGER` (whole numbers), `REAL` (decimals) |
| **Description** | Specific, clear explanation of what this measures |
| **Unit** | Measurement unit or `-` if not applicable |

**Type Mapping:**
- pandas `object` → `TEXT`
- pandas `int64` → `INTEGER`
- pandas `float64` → `REAL`

**Description Quality:**
- ❌ Bad: "Population data"
- ✅ Good: "Total population count for the country/region in that year"

**Prioritize Columns:**
1. Identifiers (keys, names, codes, years)
2. Primary metrics (main measurements)
3. Per capita/normalized versions
4. Growth/change metrics
5. Cumulative/aggregate values
6. Contextual data (demographics, economics)

#### Data Characteristics Section
Bullet points covering:
- Dataset scope (number of entities, time span)
- Geographic/categorical coverage
- Data quality and completeness
- Important patterns or groupings

#### Filtering Guidelines Section
Practical SQL filtering advice:
- How to exclude aggregates or special rows
- Common year/time filters
- NULL handling recommendations
- Useful WHERE clause patterns

#### Example Queries Section
5-10 queries demonstrating:
1. **Basic filtering** (WHERE, ORDER BY, LIMIT)
2. **Time series** (GROUP BY time)
3. **Comparisons** (multiple entities, rankings)
4. **Aggregations** (SUM, AVG, COUNT)
5. **Complex filters** (multiple conditions, NOT LIKE)

Each query should:
- Have a descriptive title
- Use actual table/column names
- Include realistic values
- Show valid SQL syntax
- Demonstrate a different pattern

## Analysis Process

### Step 1: Load and Inspect the Data File

**For CSV:**
```python
import pandas as pd

df = pd.read_csv('filename.csv')

# Get basic info
print(f"Shape: {df.shape}")
print(f"Columns: {df.columns.tolist()}")
print(f"\nData types:\n{df.dtypes}")
print(f"\nSample data:\n{df.head()}")
print(f"\nSummary stats:\n{df.describe()}")

# Check for key characteristics
print(f"\nUnique values in key columns:")
for col in ['country', 'year', 'category']:  # Adjust as needed
    if col in df.columns:
        print(f"{col}: {df[col].nunique()} unique values")
```

**For XLSX:**
```python
import pandas as pd

# First, see what sheets exist
xlsx_file = pd.ExcelFile('filename.xlsx')
print(f"Sheets: {xlsx_file.sheet_names}")

# Then load each sheet
for sheet_name in xlsx_file.sheet_names:
    df = pd.read_excel(xlsx_file, sheet_name=sheet_name)
    print(f"\n=== Sheet: {sheet_name} ===")
    print(f"Shape: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")
    print(f"Sample:\n{df.head()}")
```

### Step 2: Identify Data Structure
- What is this dataset about? (topic, domain)
- What are the main entities? (countries, companies, products, etc.)
- What time period does it cover?
- What are the primary measurements?
- What are derived/calculated fields?
- Are there categorical groupings?
- Are there aggregates or subtotals?

### Step 3: Analyze Column Patterns
Group columns by type:
- **Identifiers**: Keys, codes, names
- **Temporal**: Years, dates, periods
- **Measurements**: Absolute values, counts
- **Rates**: Per capita, percentages, ratios
- **Changes**: Growth rates, differences
- **Aggregates**: Cumulative, totals
- **Shares**: Percentages of total
- **Context**: Demographics, economics

### Step 4: Generate Comprehensive Text

**Database-level `text`**: Describe the overall purpose and scope of the database
- For CSV: What domain/topic does this data cover?
- For XLSX: What domains/topics do all sheets collectively cover?

**Table-level `text`**: Describe what each specific table contains
- Focus on the unique aspects of this table
- How does it relate to other tables (for XLSX)?
- What specific queries would target this table?

### Step 5: Create Schema
Map pandas dtypes to SQL types:
- `object` → `TEXT`
- `int64` → `INTEGER`
- `float64` → `REAL`

Write clear, specific descriptions for each column.

### Step 6: Write Example Queries
Think about the 5-10 most common questions users would ask about this data, and write SQL to answer them.

## Quality Checklist

Before submitting the JSON object:

- [ ] `database_id` increments from existing databases in data_db.json
- [ ] `database_name` is filename without extension
- [ ] `source_file` is exact filename with extension (.csv or .xlsx)
- [ ] Database-level `text` is 500+ words with rich keywords and 30+ example questions
- [ ] Database-level `text` includes CAPITALIZED SECTION HEADERS for organization
- [ ] `tables` array contains:
  - [ ] One entry for CSV (table_name: "data")
  - [ ] One entry per sheet for XLSX (table_name: sheet name)
- [ ] Each table object has: `table_name`, `text`, `schema`
- [ ] XLSX table objects also have: `sheet_name` (optional but recommended)
- [ ] Table-level `text` describes what that specific table contains
- [ ] `schema` is formatted as Markdown string (not JSON object)
- [ ] `schema` starts with `# Table: {table_name}`
- [ ] Columns table has 20-50+ important columns
- [ ] Each column row has: name, type, description, unit
- [ ] Units are included or marked with `-`
- [ ] Data Characteristics section describes the dataset
- [ ] Filtering Guidelines section provides practical SQL advice
- [ ] Example Queries section has 5-10 working SQL queries
- [ ] Each query has a descriptive title
- [ ] Queries use exact table and column names from schema
- [ ] JSON is valid and properly formatted (schema is a string value)

## Output Instructions

1. **Analyze the provided data file** (CSV or XLSX) using the process above
2. **Generate the complete JSON object** following all requirements
3. **Output ONLY the JSON object** (no additional commentary)
4. **Ensure valid JSON formatting** (proper quotes, commas, brackets)
5. The JSON object should be ready to append to the `data_db.json` array

## Example Reference

See the existing entry for `owid-co2-data.csv` in `data_db.json` as a reference for:
- Database structure with `database_id`, `database_name`, `source_file`
- Comprehensive database-level `text` field structure
- `tables` array with table objects
- Table-level `text` and `schema` structure
- Detailed column schema
- Helpful notes
- Realistic example queries

Your output should match or exceed this level of detail and searchability.

## Multi-Table XLSX Example Structure

For an XLSX file named `financial-data.xlsx` with sheets "Revenue", "Expenses", "Forecasts":

```json
{
  "database_id": "DB002",
  "database_name": "financial-data",
  "source_file": "financial-data.xlsx",
  "text": "Company financial data including revenue, expenses, and forecasts for 2020-2025...",
  "tables": [
    {
      "table_name": "Revenue",
      "sheet_name": "Revenue",
      "text": "Monthly revenue data by product line...",
      "schema": "# Table: Revenue\n\n..."
    },
    {
      "table_name": "Expenses",
      "sheet_name": "Expenses",
      "text": "Operating expenses by department...",
      "schema": "# Table: Expenses\n\n..."
    },
    {
      "table_name": "Forecasts",
      "sheet_name": "Forecasts",
      "text": "Revenue and expense projections...",
      "schema": "# Table: Forecasts\n\n..."
    }
  ]
}
```
