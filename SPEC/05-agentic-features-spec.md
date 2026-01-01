# Arc Reactor - Agentic Features Specification

## Overview

The AI agent is the core innovation of the Arc Reactor. It enables wet lab scientists to configure complex bioinformatics pipelines through natural language conversation, bridging the gap between Benchling sample data and Nextflow pipeline inputs.

The agent is built on LangChain v1 with the DeepAgents framework, providing planning capabilities, tool orchestration, and stateful conversation management.

## Agent Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          PIPELINE AGENT                                     │
│                   (DeepAgent Orchestrator)                                  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                        SYSTEM PROMPT                                  │  │
│  │  • Role: Helpful assistant for wet lab scientists                     │  │
│  │  • Goal: Help users find samples and configure pipeline runs          │  │
│  │  • Style: Conversational, step-by-step guidance                       │  │
│  │  • Constraints: Always validate before submission                     │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌─────────────────────────────┐  ┌─────────────────────────────────────┐   │
│  │        TOOLS                │  │         SUBAGENTS                   │   │
│  │                             │  │                                     │   │
│  │  NGS Data Discovery:        │  │  benchling_expert:                  │   │
│  │  • search_ngs_runs          │  │  • Complex multi-step queries       │   │
│  │  • get_ngs_run_samples      │  │  • Relationship traversal           │   │
│  │  • get_ngs_run_qc           │  │  • Data reconciliation              │   │
│  │  • get_fastq_paths          │  │                                     │   │
│  │                             │  │  config_expert:                     │   │
│  │  Benchling Discovery:       │  │  • Pipeline parameter selection     │   │
│  │  • get_entities             │  │  • Protocol recommendations         │   │
│  │  • get_entity_relationships │  │  • Parameter optimization           │   │
│  │  • list_entries             │  │  • Resource estimation              │   │
│  │  • get_entry_content        │  │                                     │   │
│  │  • get_entry_entities       │  │                                     │   │
│  │                             │  │                                     │   │
│  │  Schema & Metadata:         │  │                                     │   │
│  │  • get_schemas              │  │                                     │   │
│  │  • get_schema_field_info    │  │                                     │   │
│  │  • get_dropdown_values      │  │                                     │   │
│  │  • list_projects            │  │                                     │   │
│  │                             │  │                                     │   │
│  │  Pipeline Info:             │  │                                     │   │
│  │  • list_pipelines           │  │                                     │   │
│  │  • get_pipeline_schema      │  │                                     │   │
│  │                             │  │                                     │   │
│  │  File Generation:           │  │                                     │   │
│  │  • generate_samplesheet     │  │                                     │   │
│  │  • generate_config          │  │                                     │   │
│  │                             │  │                                     │   │
│  │  Validation & Submission:   │  │                                     │   │
│  │  • validate_inputs          │  │                                     │   │
│  │  • submit_run (HITL)        │  │                                     │   │
│  │  • cancel_run (HITL)        │  │                                     │   │
│  │  • delete_file (HITL)       │  │                                     │   │
│  │  • clear_samplesheet (HITL) │  │                                     │   │
│  │                             │  │                                     │   │
│  │  Advanced:                  │  │                                     │   │
│  │  • execute_warehouse_query  │  │                                     │   │
│  └─────────────────────────────┘  └─────────────────────────────────────┘   │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                       MIDDLEWARE STACK                                │  │
│  │                                                                       │  │
│  │  • TodoListMiddleware - Task planning and tracking                    │  │
│  │  • LargeOutputMiddleware - Context offloading (for large results)     │  │
│  │  • SummarizationMiddleware - Auto-summarize at 85% context            │  │
│  │  • HumanInTheLoopMiddleware - Approval for destructive/costly tools   │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Reference Code Repositories

- `./external-repos/arc-benchling-mcp`
  - MCP server that includes many tools for read-only interfacing with Benchling
  - Use as a guide for developing the Benchling tools for the Pipeline Agent
- `./external-repos/benchling-py`
  - Python package for interfacing with the Benchling postgres database and Python SDK
  - Use as a dependency: `"benchling-py @ git+https://github.com/arcinstitute/benchling-py.git@main"`

## Agent Configuration

### Model Selection

Model configuration values are defined in `SPEC/11-conf-spec.md` and must be
referenced from there to avoid drift.

**Default Model**: `google_genai:gemini-3-flash-preview`

**Initialization Pattern**:
```python
from langchain.chat_models import init_chat_model

# Main agent model
model = init_chat_model(
    "google_genai:gemini-3-flash-preview",
    temperature=1.0,  # Required for Gemini with thinking
    thinking_level="low",  # Default thinking level
)

# For complex reasoning tasks (subagents)
model_thinking = init_chat_model(
    "google_genai:gemini-3-flash-preview",
    temperature=1.0,
    thinking_level="high",
)
```

### System Prompt

```markdown
You are a helpful assistant for wet lab scientists at Arc Institute. Your job is to help users set up Nextflow bioinformatics pipeline runs.

## Your Capabilities

1. **Find NGS runs**: Search for sequencing runs by SspArc ID, run name, date, submitter, or other criteria
2. **Get run samples**: Retrieve all samples and FASTQ paths for a given run
3. **Check QC metrics**: View quality control data for runs and samples
4. **Find samples**: Search Benchling for entities and samples by name, schema, project, or other criteria
5. **Explore relationships**: Trace sample lineage through entity relationships
6. **Access protocols**: Read notebook entries for experimental context
7. **Generate files**: Create samplesheet CSV files and Nextflow configuration files
8. **Configure pipelines**: Help users choose appropriate pipeline parameters
9. **Validate inputs**: Check that all required files exist and parameters are valid
10. **Submit runs**: Send validated runs to the compute cluster (requires approval)

## Workflow

When a user wants to process their sequencing data:

1. **Identify the data source**: Ask for SspArc ID, NGS run name, or help them search
2. **Retrieve samples**: Use search_ngs_runs and get_ngs_run_samples to find their data
3. **Generate samplesheet**: Create the samplesheet CSV with FASTQ paths and metadata
4. **Configure pipeline**: Help select appropriate pipeline and parameters
5. **Validate**: Check all files exist and parameters are correct
6. **Submit**: Request approval, then submit the run

## Important Notes

- Always confirm sample counts and verify FASTQ file existence before submission
- When users mention "SspArc" they're referring to a Pooled Sample name (sequencing submission)
- NGS Run names follow patterns like "NR-2024-0156" or "20241215_SspArc0050_W1"
- Be proactive in showing QC metrics to help users assess data quality
- If a user's query is ambiguous, ask clarifying questions before proceeding
```

## Benchling Service

All Benchling tools communicate with the data warehouse through a shared service. The service
is initialized at application startup and injected into tools via FastAPI dependencies.

```python
from benchling_py import WarehouseClient

class BenchlingService:
    """Service for Benchling data warehouse operations."""
    
    def __init__(self):
        self._client = WarehouseClient()
    
    @property
    def warehouse(self) -> WarehouseClient:
        return self._client
```

---

## NGS Data Discovery Tools

These tools are specifically designed to help users find and retrieve NGS sequencing data
for samplesheet generation. They provide the primary workflow for locating samples based
on user queries like "I want to process my SspArc0050 dataset".

**Table formatting:** Any tabular tool output returned to the LLM agent must be encoded
using the `toon` library (TOON format) for compact, token-efficient responses.

### search_ngs_runs

Search for NGS runs with comprehensive filtering options. This is the primary tool for
helping users find their sequencing data.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `ngs_run` | string | No | NGS Run name or pattern (e.g., "NR-2024-0156", "NR-2024-%") |
| `pooled_sample` | string | No | Pooled sample / SspArc name or pattern (e.g., "SspArc0050", "SspArc%") |
| `submitter` | string | No | Submitter name (first, last, or full name) |
| `submitter_email` | string | No | Submitter email address |
| `instrument` | string | No | Instrument name (e.g., "NovaSeqX", "NextSeq2000") |
| `project` | string | No | Project name |
| `lib_prep_method` | string | No | Library preparation method |
| `cost_center` | string | No | Cost center for billing |
| `start_date` | string | No | Start of date range (YYYY-MM-DD format) |
| `end_date` | string | No | End of date range (YYYY-MM-DD format) |
| `days_back` | integer | No | Alternative to date range: runs from last N days |
| `use_wildcards` | boolean | No | Treat name parameters as SQL wildcard patterns (default: false) |
| `limit` | integer | No | Maximum results to return (default: 50, max: 500) |
| `include_qc_summary` | boolean | No | Include basic QC metrics in results (default: false) |

**Returns (TOON table):**
```
Found 3 NGS runs matching your criteria:

ngs_run       | pooled_sample | submitter      | instrument | completion_date | sample_count | run_path
--------------|---------------|----------------|------------|-----------------|--------------|----------------------------------
NR-2024-0156  | SspArc0050    | Jane Smith     | NovaSeqX   | 2024-12-18      | 24           | gs://arc-ngs-data/NR-2024-0156/
NR-2024-0152  | SspArc0048    | Jane Smith     | NovaSeqX   | 2024-12-16      | 12           | gs://arc-ngs-data/NR-2024-0152/
NR-2024-0149  | SspArc0047    | John Doe       | NextSeq2000| 2024-12-14      | 8            | gs://arc-ngs-data/NR-2024-0149/

Use get_ngs_run_samples to retrieve detailed sample information for a specific run.
```

**Example Usage:**
```python
# Find runs by SspArc
search_ngs_runs(pooled_sample="SspArc0050")

# Find recent runs by submitter
search_ngs_runs(submitter="Jane Smith", days_back=30)

# Find all NovaSeqX runs from last week with QC
search_ngs_runs(instrument="NovaSeqX", days_back=7, include_qc_summary=True)

# Find runs by project with wildcards
search_ngs_runs(project="Smith_RNAseq%", use_wildcards=True)
```

**Implementation:**
```python
from langchain.tools import tool
from typing import Optional
from datetime import date, timedelta

@tool
def search_ngs_runs(
    ngs_run: Optional[str] = None,
    pooled_sample: Optional[str] = None,
    submitter: Optional[str] = None,
    submitter_email: Optional[str] = None,
    instrument: Optional[str] = None,
    project: Optional[str] = None,
    lib_prep_method: Optional[str] = None,
    cost_center: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    days_back: Optional[int] = None,
    use_wildcards: bool = False,
    limit: int = 50,
    include_qc_summary: bool = False,
) -> str:
    """Search for NGS runs with flexible filtering options.
    
    This is the primary tool for finding sequencing runs. Users typically
    reference their data by SspArc (pooled sample) name, NGS run name,
    or by their own name as submitter.
    
    Args:
        ngs_run: NGS Run name (e.g., "NR-2024-0156") or pattern with wildcards
        pooled_sample: Pooled sample / SspArc name (e.g., "SspArc0050")
        submitter: Submitter name (first, last, or full)
        submitter_email: Submitter email address
        instrument: Instrument name (NovaSeqX, NextSeq2000, etc.)
        project: Project name
        lib_prep_method: Library prep method
        cost_center: Cost center for billing
        start_date: Start of date range (YYYY-MM-DD)
        end_date: End of date range (YYYY-MM-DD)
        days_back: Alternative to date range - last N days
        use_wildcards: Treat names as SQL wildcard patterns (%, _)
        limit: Maximum results to return (default: 50, max: 500)
        include_qc_summary: Include basic QC metrics (slower query)
    
    Returns:
        Formatted table of matching NGS runs with key metadata
    """
    # Build dynamic WHERE clause
    conditions = ["nr.\"archived$\" = FALSE"]
    params = {}
    
    # Handle date filtering
    if days_back:
        start_date = (date.today() - timedelta(days=days_back)).isoformat()
        end_date = date.today().isoformat()
    
    if start_date:
        conditions.append("nro.completion_date >= :start_date")
        params["start_date"] = start_date
    
    if end_date:
        conditions.append("nro.completion_date <= :end_date")
        params["end_date"] = end_date
    
    # Handle name filters with optional wildcards
    if ngs_run:
        op = "LIKE" if use_wildcards else "="
        conditions.append(f'nr."name$" {op} :ngs_run')
        params["ngs_run"] = ngs_run
    
    if pooled_sample:
        op = "LIKE" if use_wildcards else "="
        conditions.append(f'ps."name$" {op} :pooled_sample')
        params["pooled_sample"] = pooled_sample
    
    if submitter:
        conditions.append("""
            (ps.submitter_first_name ILIKE :submitter_pattern
             OR ps.submitter_last_name ILIKE :submitter_pattern
             OR CONCAT(ps.submitter_first_name, ' ', ps.submitter_last_name) ILIKE :submitter_pattern)
        """)
        params["submitter_pattern"] = f"%{submitter}%"
    
    if submitter_email:
        conditions.append("ps.submitter_email = :submitter_email")
        params["submitter_email"] = submitter_email
    
    if instrument:
        op = "LIKE" if use_wildcards else "="
        conditions.append(f'ni."name$" {op} :instrument')
        params["instrument"] = instrument
    
    if project:
        op = "LIKE" if use_wildcards else "="
        conditions.append(f'pt."name$" {op} :project')
        params["project"] = project
    
    if lib_prep_method:
        conditions.append("lps.lib_prep_method = :lib_prep_method")
        params["lib_prep_method"] = lib_prep_method
    
    if cost_center:
        conditions.append("ps.cost_center = :cost_center")
        params["cost_center"] = cost_center
    
    # Build query
    where_clause = " AND ".join(conditions)
    
    qc_columns = ""
    if include_qc_summary:
        qc_columns = """,
            AVG(nros.q30_percent) AS avg_q30,
            SUM(nros.sequenced_number_of_molecules) AS total_reads
        """
    
    sql = f"""
    SELECT DISTINCT
        nr."name$" AS ngs_run,
        ps."name$" AS pooled_sample,
        CONCAT(ps.submitter_first_name, ' ', ps.submitter_last_name) AS submitter,
        ni."name$" AS instrument,
        nro.completion_date,
        COUNT(DISTINCT lps."name$") AS sample_count,
        nro.link_to_sequencing_data AS run_path,
        pt."name$" AS project
        {qc_columns}
    FROM ngs_run$raw nr
    INNER JOIN ngs_instrument$raw ni ON nr.instrument = ni.id
    INNER JOIN ngs_run_output_v2$raw nro ON nr.id = nro.ngs_run
    INNER JOIN ngs_run_pooling_v2$raw nrp ON nr.id = nrp.ngs_run
    INNER JOIN pooled_sample$raw ps ON nrp.ngs_library_pool = ps.id
    LEFT JOIN ngs_library_pooling_v2$raw nlp ON ps.id = nlp.destination
    LEFT JOIN library_prep_sample$raw lps ON nlp.source = lps.id
    LEFT JOIN project_tag$raw pt ON lps.project = pt.id
    {"LEFT JOIN ngs_run_output_sample$raw nros ON nr.id = nros.ngs_run" if include_qc_summary else ""}
    WHERE {where_clause}
        AND ni."archived$" = FALSE
        AND nro."archived$" = FALSE
        AND (ps."archived$" = FALSE OR ps."archived$" IS NULL)
        AND (lps."archived$" = FALSE OR lps."archived$" IS NULL)
    GROUP BY 
        nr."name$", ps."name$", ps.submitter_first_name, ps.submitter_last_name,
        ni."name$", nro.completion_date, nro.link_to_sequencing_data, pt."name$"
    ORDER BY nro.completion_date DESC
    LIMIT :limit
    """
    
    params["limit"] = min(limit, 500)
    
    result = benchling_service.warehouse.query(
        sql=sql,
        params=params,
        return_format="dataframe",
    )
    
    return format_ngs_run_results(result)
```

---

### get_ngs_run_samples

Get detailed sample information for a specific NGS run, including FASTQ paths and
metadata needed for samplesheet generation.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `ngs_run` | string | Yes* | NGS Run name (e.g., "NR-2024-0156") |
| `pooled_sample` | string | Yes* | Alternative: Pooled sample / SspArc name |
| `include_metadata` | boolean | No | Include sample metadata (organism, tissue, cell line, etc.) |
| `include_qc` | boolean | No | Include per-sample QC metrics |

*One of `ngs_run` or `pooled_sample` is required.

**Returns (TOON table):**
```
NGS Run: NR-2024-0156
Pooled Sample: SspArc0050
Submitter: Jane Smith (jane.smith@arcinstitute.org)
Instrument: NovaSeqX
Completion Date: 2024-12-18
Sample Count: 24

Samples (TOON):
sample_id  | fastq_r1                                           | fastq_r2                                           | organism | cell_line | read_count | q30_percent
-----------|----------------------------------------------------|----------------------------------------------------|----------|-----------|------------|------------
LPS-001    | gs://arc-ngs-data/NR-2024-0156/LPS-001_R1.fastq.gz | gs://arc-ngs-data/NR-2024-0156/LPS-001_R2.fastq.gz | Human    | HeLa      | 45000000   | 94.2
LPS-002    | gs://arc-ngs-data/NR-2024-0156/LPS-002_R1.fastq.gz | gs://arc-ngs-data/NR-2024-0156/LPS-002_R2.fastq.gz | Human    | HeLa      | 42000000   | 93.8
...

Ready to generate samplesheet? Use generate_samplesheet with these samples.
```

**Implementation:**
```python
@tool
def get_ngs_run_samples(
    ngs_run: Optional[str] = None,
    pooled_sample: Optional[str] = None,
    include_metadata: bool = True,
    include_qc: bool = True,
) -> str:
    """Get detailed sample information for a specific NGS run.
    
    This tool retrieves all library prep samples associated with an NGS run,
    including FASTQ file paths, sample metadata, and QC metrics. Use this
    to prepare data for samplesheet generation.
    
    Args:
        ngs_run: NGS Run name (e.g., "NR-2024-0156")
        pooled_sample: Alternative: Pooled sample / SspArc name (e.g., "SspArc0050")
        include_metadata: Include organism, tissue, cell line, etc. (default: True)
        include_qc: Include per-sample QC metrics (default: True)
    
    Returns:
        Formatted run summary and sample table with FASTQ paths
    """
    if not ngs_run and not pooled_sample:
        return "Error: Please provide either ngs_run or pooled_sample parameter."
    
    # Build filter condition
    if ngs_run:
        run_filter = 'nr."name$" = :run_id'
        params = {"run_id": ngs_run}
    else:
        run_filter = 'ps."name$" = :pooled_sample'
        params = {"pooled_sample": pooled_sample}
    
    # Build query with optional columns
    metadata_cols = ""
    metadata_join = ""
    if include_metadata:
        metadata_cols = """,
            md.organism,
            md.tissue,
            md.cell_line,
            md.perturbation,
            md.replicate
        """
        metadata_join = """
        LEFT JOIN ngs_library_metadata_v2$raw md 
            ON lps.id = md.ngs_library AND md."archived$" = FALSE
        """
    
    qc_cols = ""
    if include_qc:
        qc_cols = """,
            nros.sequenced_number_of_molecules AS read_count,
            nros.q30_percent,
            nros.average_read_length
        """
    
    sql = f"""
    WITH run_info AS (
        SELECT DISTINCT
            nr."name$" AS ngs_run,
            ps."name$" AS pooled_sample,
            ps.submitter_first_name,
            ps.submitter_last_name,
            ps.submitter_email,
            ps.cost_center,
            ni."name$" AS instrument,
            nro.completion_date,
            nro.link_to_sequencing_data AS run_path
        FROM ngs_run$raw nr
        INNER JOIN ngs_instrument$raw ni ON nr.instrument = ni.id
        INNER JOIN ngs_run_output_v2$raw nro ON nr.id = nro.ngs_run
        INNER JOIN ngs_run_pooling_v2$raw nrp ON nr.id = nrp.ngs_run
        INNER JOIN pooled_sample$raw ps ON nrp.ngs_library_pool = ps.id
        WHERE {run_filter}
            AND nr."archived$" = FALSE
            AND ni."archived$" = FALSE
            AND nro."archived$" = FALSE
            AND (ps."archived$" = FALSE OR ps."archived$" IS NULL)
        LIMIT 1
    ),
    samples AS (
        SELECT DISTINCT
            lps.sample_id,
            lps."name$" AS sample_name,
            lps.lib_prep_method,
            lps.lib_prep_kit_used,
            nros_r1.link_to_fastq_file AS fastq_r1,
            nros_r2.link_to_fastq_file AS fastq_r2
            {metadata_cols}
            {qc_cols}
        FROM ngs_run$raw nr
        INNER JOIN ngs_run_pooling_v2$raw nrp ON nr.id = nrp.ngs_run
        INNER JOIN pooled_sample$raw ps ON nrp.ngs_library_pool = ps.id
        INNER JOIN ngs_library_pooling_v2$raw nlp ON ps.id = nlp.destination
        INNER JOIN library_prep_sample$raw lps ON nlp.source = lps.id
        LEFT JOIN ngs_run_output_sample$raw nros_r1 
            ON nr.id = nros_r1.ngs_run 
            AND lps.id = nros_r1.ngs_library 
            AND nros_r1.read = 'R1'
            AND nros_r1."archived$" = FALSE
        LEFT JOIN ngs_run_output_sample$raw nros_r2 
            ON nr.id = nros_r2.ngs_run 
            AND lps.id = nros_r2.ngs_library 
            AND nros_r2.read = 'R2'
            AND nros_r2."archived$" = FALSE
        {"LEFT JOIN ngs_run_output_sample$raw nros ON nr.id = nros.ngs_run AND lps.id = nros.ngs_library AND nros.read = 'R1'" if include_qc else ""}
        {metadata_join}
        WHERE {run_filter}
            AND nr."archived$" = FALSE
            AND lps."archived$" = FALSE
            AND (ps."archived$" = FALSE OR ps."archived$" IS NULL)
        ORDER BY lps.sample_id
    )
    SELECT * FROM run_info, samples
    """
    
    result = benchling_service.warehouse.query(
        sql=sql,
        params=params,
        return_format="dataframe",
    )
    
    return format_run_samples_result(result)
```

---

### get_ngs_run_qc

Get detailed QC metrics for an NGS run, including per-lane and per-sample statistics.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `ngs_run` | string | Yes* | NGS Run name |
| `pooled_sample` | string | Yes* | Alternative: Pooled sample / SspArc name |
| `level` | string | No | Detail level: "summary", "lane", or "sample" (default: "summary") |

*One of `ngs_run` or `pooled_sample` is required.

**Returns (summary level; tables in TOON):**
```
NGS Run QC Summary: NR-2024-0156

Run Metrics:
  Instrument: NovaSeqX
  Completion Date: 2024-12-18
  Total Samples: 24
  Total Reads: 1.2B
  Average Q30: 94.5%
  Average Read Length: 150 bp

Lane Summary (TOON):
  Lane 1: 305M reads, 94.2% Q30, 0.8% error rate
  Lane 2: 298M reads, 94.8% Q30, 0.7% error rate
  Lane 3: 312M reads, 94.4% Q30, 0.9% error rate
  Lane 4: 285M reads, 94.6% Q30, 0.8% error rate

QC Status: PASS (all lanes >90% Q30)
```

**Implementation:**
```python
@tool
def get_ngs_run_qc(
    ngs_run: Optional[str] = None,
    pooled_sample: Optional[str] = None,
    level: str = "summary",
) -> str:
    """Get QC metrics for an NGS run.
    
    Retrieves quality control data at different levels of detail to help
    users assess data quality before processing.
    
    Args:
        ngs_run: NGS Run name (e.g., "NR-2024-0156")
        pooled_sample: Alternative: Pooled sample / SspArc name
        level: Detail level - "summary" (default), "lane", or "sample"
    
    Returns:
        Formatted QC report with metrics and pass/fail status
    """
    if not ngs_run and not pooled_sample:
        return "Error: Please provide either ngs_run or pooled_sample parameter."
    
    if level == "summary":
        return _get_run_qc_summary(ngs_run, pooled_sample)
    elif level == "lane":
        return _get_run_qc_by_lane(ngs_run, pooled_sample)
    elif level == "sample":
        return _get_run_qc_by_sample(ngs_run, pooled_sample)
    else:
        return f"Error: Invalid level '{level}'. Use 'summary', 'lane', or 'sample'."
```

---

### get_fastq_paths

Quick lookup of FASTQ file paths for specified samples. Use this when you already
know the sample IDs and just need the file paths.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `sample_ids` | string | Yes | Sample IDs, semicolon-delimited (e.g., "LPS-001;LPS-002;LPS-003") |
| `ngs_run` | string | No | Restrict to specific NGS run |
| `validate_exists` | boolean | No | Check if files exist in GCS (default: false) |

**Returns (TOON table):**
```
FASTQ paths for 3 samples:

sample_id | fastq_r1                                           | fastq_r2                                           | exists
----------|----------------------------------------------------|----------------------------------------------------|-------
LPS-001   | gs://arc-ngs-data/NR-2024-0156/LPS-001_R1.fastq.gz | gs://arc-ngs-data/NR-2024-0156/LPS-001_R2.fastq.gz | YES
LPS-002   | gs://arc-ngs-data/NR-2024-0156/LPS-002_R1.fastq.gz | gs://arc-ngs-data/NR-2024-0156/LPS-002_R2.fastq.gz | YES
LPS-003   | gs://arc-ngs-data/NR-2024-0156/LPS-003_R1.fastq.gz | gs://arc-ngs-data/NR-2024-0156/LPS-003_R2.fastq.gz | YES

All files verified in GCS.
```

**Implementation:**
```python
@tool
def get_fastq_paths(
    sample_ids: str,
    ngs_run: Optional[str] = None,
    validate_exists: bool = False,
) -> str:
    """Get FASTQ file paths for specified samples.
    
    Quick lookup when you know the sample IDs and need file paths
    for samplesheet generation or validation.
    
    Args:
        sample_ids: Sample IDs, semicolon-delimited (e.g., "LPS-001;LPS-002")
        ngs_run: Restrict to specific NGS run (optional)
        validate_exists: Check if files exist in GCS (slower)
    
    Returns:
        Table of sample IDs with FASTQ R1/R2 paths
    """
    samples = [s.strip() for s in sample_ids.split(";") if s.strip()]
    if not samples:
        return "Error: No valid sample IDs provided."
    
    # Build parameterized IN clause
    sample_params = {f"s{i}": s for i, s in enumerate(samples)}
    sample_placeholders = ", ".join(f":s{i}" for i in range(len(samples)))
    
    run_filter = ""
    if ngs_run:
        run_filter = 'AND nr."name$" = :ngs_run'
        sample_params["ngs_run"] = ngs_run
    
    sql = f"""
    SELECT DISTINCT
        lps.sample_id,
        nr."name$" AS ngs_run,
        nros_r1.link_to_fastq_file AS fastq_r1,
        nros_r2.link_to_fastq_file AS fastq_r2
    FROM library_prep_sample$raw lps
    INNER JOIN ngs_library_pooling_v2$raw nlp ON lps.id = nlp.source
    INNER JOIN pooled_sample$raw ps ON nlp.destination = ps.id
    INNER JOIN ngs_run_pooling_v2$raw nrp ON ps.id = nrp.ngs_library_pool
    INNER JOIN ngs_run$raw nr ON nrp.ngs_run = nr.id
    LEFT JOIN ngs_run_output_sample$raw nros_r1 
        ON nr.id = nros_r1.ngs_run 
        AND lps.id = nros_r1.ngs_library 
        AND nros_r1.read = 'R1'
    LEFT JOIN ngs_run_output_sample$raw nros_r2 
        ON nr.id = nros_r2.ngs_run 
        AND lps.id = nros_r2.ngs_library 
        AND nros_r2.read = 'R2'
    WHERE lps.sample_id IN ({sample_placeholders})
        AND lps."archived$" = FALSE
        AND nr."archived$" = FALSE
        {run_filter}
    ORDER BY lps.sample_id
    """
    
    result = benchling_service.warehouse.query(
        sql=sql,
        params=sample_params,
        return_format="dataframe",
    )
    
    if validate_exists:
        result = validate_gcs_files(result)
    
    return format_fastq_paths(result, validated=validate_exists)
```

---

## Benchling Discovery Tools

### get_entities

Search for entities in the Benchling data warehouse with flexible filtering.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `entity_names` | string | Yes | Entity names (semicolon-delimited) |
| `schema_names` | string | No | Filter by schema names (semicolon-delimited) |
| `project_names` | string | No | Filter by project names (semicolon-delimited) |
| `use_wildcards` | boolean | No | Treat names as SQL wildcard patterns (default: false) |
| `limit` | integer | No | Maximum results to return (default: 100) |

**Returns (TOON table):**
```
Found 3 entities matching "LPS-001%":

entity_id    | entity_name | schema_name           | project_name  | entity_url
-------------|-------------|-----------------------|---------------|---------------------------
bfi_abc123   | LPS-001     | NGS Library Prep Sample | Smith_RNAseq | https://arcinstitute...
bfi_def456   | LPS-001-P1  | NGS Pooled Sample      | Smith_RNAseq | https://arcinstitute...
bfi_ghi789   | LPS-001-R1  | NGS Run Output v2      | Smith_RNAseq | https://arcinstitute...
```

**Implementation:**
```python
from langchain.tools import tool

@tool
def get_entities(
    entity_names: str,
    schema_names: str | None = None,
    project_names: str | None = None,
    use_wildcards: bool = False,
    limit: int = 100,
) -> str:
    """Get entities from the Benchling data warehouse.
    
    Search for entities by name with optional filtering by schema and project.
    Use wildcards (%, _) when you need pattern matching.
    
    Args:
        entity_names: Entity names to search for (semicolon-delimited)
        schema_names: Filter by schema names (semicolon-delimited)
        project_names: Filter by project names (semicolon-delimited)
        use_wildcards: Treat names as SQL wildcard patterns
        limit: Maximum results (default: 100)
    
    Returns:
        Formatted table of matching entities with metadata
    """
    # Parse semicolon-delimited inputs
    names = [n.strip() for n in entity_names.split(";")]
    schemas = [s.strip() for s in schema_names.split(";")] if schema_names else None
    projects = [p.strip() for p in project_names.split(";")] if project_names else None
    
    # Build query via arc-benchling-mcp pattern
    result = benchling_mcp.get_entities(
        entity_names=";".join(names),
        schema_names=";".join(schemas) if schemas else None,
        project_names=";".join(projects) if projects else None,
        use_wildcards=use_wildcards,
        limit=limit,
    )
    
    return format_entity_results(result)
```

### get_entity_relationships

Traverse entity relationships to understand sample lineage.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `entity_name` | string | Yes | Starting entity name |
| `schema_name` | string | No | Schema name (improves performance) |
| `relationship_depth` | integer | No | How many levels to traverse (default: 4, max: 10) |
| `relationship_types` | string | No | Specific relationship fields to follow (semicolon-delimited) |
| `include_reverse_links` | boolean | No | Include entities that link TO this entity (default: true) |
| `output_format` | string | No | Output format: "tree", "yaml", or "json" (default: "tree") |

**Returns (tree format):**
```
Entity Relationships for LPS-001 (depth: 4)

NGS Library Prep Sample: LPS-001
├── Cell Line: HeLa
│   └── Cell Line Lot: HeLa-Lot-2024-001
├── NGS Pooled Sample: Pool-2024-156-A
│   └── NGS Run: NR-2024-0156
│       └── NGS Run Output v2: LPS-001-R1
│           ├── fastq_r1: gs://arc-ngs-data/.../LPS-001_R1.fastq.gz
│           └── fastq_r2: gs://arc-ngs-data/.../LPS-001_R2.fastq.gz
└── Protocol: 10X Library Prep Protocol v3
```

### list_entries

List Benchling notebook entries with optional filtering.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `entry_names` | string | No | Entry names (semicolon-delimited) |
| `project_names` | string | No | Project names (semicolon-delimited) |
| `folder_names` | string | No | Folder names (semicolon-delimited) |
| `creator_names` | string | No | Creator names (semicolon-delimited) |
| `min_date` | string | No | Minimum creation/modification date (YYYY-MM-DD) |
| `max_date` | string | No | Maximum creation/modification date (YYYY-MM-DD) |
| `allow_wildcards` | boolean | No | Recognize SQL wildcards in names (default: false) |
| `archived` | boolean | No | Include archived entries (default: false) |

### get_entry_content

Get the content of a Benchling notebook entry.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `entry_names` | string | Yes | Entry names (semicolon-delimited) |
| `head` | integer | No | Number of lines from the beginning |
| `tail` | integer | No | Number of lines from the end |

### get_entry_entities

Get entities associated with a Benchling notebook entry.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `entry_name` | string | Yes | Entry name |
| `limit` | integer | No | Maximum entities to return (default: 40) |

---

## Schema & Metadata Tools

### get_schemas

Get general information about one or more schemas.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `schema_names` | string | No | Schema names (semicolon-delimited) |
| `get_all_schemas` | boolean | No | Get all schema names (default: false) |

### get_schema_field_info

Get detailed field information for a schema.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `schema_name` | string | Yes | Name of the schema |

### get_dropdown_values

Get available values for a Benchling dropdown.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `dropdown_name` | string | Yes | Name of the dropdown |

### list_projects

List all projects in the Benchling data warehouse.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `wildcard_pattern` | string | No | SQL wildcard pattern to filter projects |

---

## Pipeline Info Tools

### list_pipelines

List available Nextflow pipelines with supported parameters.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `category` | string | No | Filter by category (e.g., "scRNA-seq", "bulk-RNA-seq") |

**Returns (TOON table):**
```
Available Pipelines:

Pipeline           | Version | Description                     | Category
-------------------|---------|--------------------------------|------------
nf-core/scrnaseq   | 2.7.1   | Single-cell RNA-seq analysis   | scRNA-seq
nf-core/rnaseq     | 3.14.0  | Bulk RNA-seq analysis          | bulk-RNA-seq
nf-core/viralrecon | 2.6.0   | Viral sequence analysis        | viral

Use get_pipeline_schema for detailed parameter information.
```

### get_pipeline_schema

Get detailed parameter schema for a pipeline.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `pipeline` | string | Yes | Pipeline name (e.g., "nf-core/scrnaseq") |
| `version` | string | No | Specific version (default: latest) |

**Returns:**
```
Pipeline: nf-core/scrnaseq (v2.7.1)

Required Parameters:
  --input           Samplesheet CSV with sample metadata
  --outdir          Output directory for results
  --genome          Reference genome (GRCh38 | GRCm39)
  --protocol        10X protocol version (10XV2 | 10XV3)

Optional Parameters:
  --aligner         Aligner to use (alevin | cellranger | star)
  --expected_cells  Expected cells per sample (default: 10000)
  ...
```

---

## File Generation Tools

### generate_samplesheet

Generate a samplesheet CSV from retrieved sample data.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `ngs_run` | string | Yes* | NGS Run name |
| `pooled_sample` | string | Yes* | Alternative: Pooled sample name |
| `sample_ids` | string | No | Specific samples to include (semicolon-delimited) |
| `pipeline` | string | Yes | Target pipeline (e.g., "nf-core/scrnaseq") |
| `expected_cells` | integer | No | Expected cells per sample (default: 10000) |

*One of `ngs_run` or `pooled_sample` is required.

**Returns:**
```
Generated samplesheet for nf-core/scrnaseq:

sample,fastq_1,fastq_2,expected_cells
LPS-001,gs://arc-ngs-data/NR-2024-0156/LPS-001_R1.fastq.gz,gs://arc-ngs-data/NR-2024-0156/LPS-001_R2.fastq.gz,10000
LPS-002,gs://arc-ngs-data/NR-2024-0156/LPS-002_R1.fastq.gz,gs://arc-ngs-data/NR-2024-0156/LPS-002_R2.fastq.gz,10000
...

24 samples ready. Review in the samplesheet panel and proceed with configuration.
```

### generate_config

Generate Nextflow configuration file.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `pipeline` | string | Yes | Pipeline name |
| `params` | dict | No | Pipeline parameters to include |
| `profile` | string | No | Execution profile (default: "gcp_batch") |

**Returns:**
```
Generated config for nf-core/scrnaseq:

// Nextflow configuration
params {
    genome = 'GRCh38'
    protocol = '10XV3'
    aligner = 'simpleaf'
    expected_cells = 10000
}

process {
    executor = 'google-batch'
    ...
}
```

---

## Validation & Submission Tools

### validate_inputs

Validate samplesheet and configuration before submission.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `samplesheet_csv` | string | Yes | CSV content |
| `config_content` | string | Yes | Config content |
| `pipeline` | string | Yes | Pipeline name |

**Returns (Success):**
```json
{
  "valid": true,
  "warnings": [
    "3 samples have expected_cells below 5000"
  ],
  "summary": {
    "sample_count": 24,
    "files_verified": 48,
    "estimated_runtime": "4-6 hours"
  }
}
```

**Returns (Failure):**
```json
{
  "valid": false,
  "errors": [
    {
      "type": "MISSING_FILE",
      "sample": "LPS-012",
      "field": "fastq_2",
      "message": "File not found: gs://arc-ngs-data/NR-2024-0156/LPS-012_R2.fastq.gz"
    },
    {
      "type": "INVALID_PARAM",
      "param": "genome",
      "message": "Invalid genome 'hg38'. Valid options: GRCh38, GRCm39"
    }
  ]
}
```

### submit_run

Submit a validated pipeline run to GCP Batch.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `samplesheet_csv` | string | Yes | Validated CSV content |
| `config_content` | string | Yes | Validated config content |
| `pipeline` | string | Yes | Pipeline name |
| `pipeline_version` | string | Yes | Pipeline version |

**Human-in-the-Loop:** This tool requires explicit user approval before execution.

**Returns:**
```json
{
  "run_id": "run-abc123",
  "status": "submitted",
  "gcs_path": "gs://arc-reactor-runs/runs/run-abc123",
  "estimated_runtime": "4-6 hours",
  "message": "Pipeline run submitted successfully. You can track progress in the Runs tab."
}
```

### cancel_run

Cancel a running pipeline job.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `run_id` | string | Yes | Run identifier |

**Human-in-the-Loop:** This tool requires explicit user approval before execution.

### delete_file

Delete a run file from GCS (dangerous operation).

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `run_id` | string | Yes | Run identifier |
| `file_path` | string | Yes | Path relative to the run root |

**Human-in-the-Loop:** This tool requires explicit user approval before execution.

### clear_samplesheet

Remove all rows from the current samplesheet.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `confirm` | boolean | Yes | Must be true to proceed |

**Human-in-the-Loop:** This tool requires explicit user approval before execution.

---

## Advanced Tools

### execute_warehouse_query

Execute a read-only SQL query against the Benchling data warehouse. This is an
escape hatch for complex queries that cannot be expressed through the standard tools.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `sql` | string | Yes | SQL query (SELECT only) |
| `params` | dict | No | Query parameters (for parameterized queries) |
| `limit` | integer | No | Maximum rows to return (default: 100, max: 1000) |


**Returns (TOON table):**
```
Query results (42 rows):

name        | barcode  | schema_name | location_name
------------|----------|-------------|----------------
TUBE-001    | BC123456 | Tube        | Freezer-A-Shelf-2
TUBE-002    | BC123457 | Tube        | Freezer-A-Shelf-2
...
```

**Implementation:**
```python
@tool
def execute_warehouse_query(
    sql: str,
    params: dict | None = None,
    limit: int = 100,
) -> str:
    """Execute a read-only SQL query against the Benchling data warehouse.
    
    Use this for complex queries that cannot be expressed through
    standard tools. Only SELECT queries are allowed.
    
    Args:
        sql: SQL query (SELECT only)
        params: Query parameters for parameterized queries
        limit: Maximum rows to return (default: 100, max: 1000)
    
    Returns:
        Formatted query results
    """
    # Validate SELECT only
    normalized = sql.strip().upper()
    if not normalized.startswith("SELECT"):
        raise ValueError("Only SELECT queries are allowed")
    
    # Enforce limit
    effective_limit = min(limit, 1000)
    if "LIMIT" not in normalized:
        sql = f"{sql.rstrip(';')} LIMIT {effective_limit}"
    
    result = benchling_service.warehouse.query(
        sql=sql,
        params=params or {},
        return_format="dataframe",
    )
    
    return format_query_results(result)
```

**Common Warehouse Tables:**
| Table | Description |
|-------|-------------|
| `entity$raw` | All registry entities |
| `entry$raw` | Notebook entries |
| `schema$raw` | Schema definitions |
| `schema_field$raw` | Schema field definitions |
| `project$raw` | Projects |
| `folder$raw` | Folders |
| `container$raw` | Sample containers |
| `box$raw` | Storage boxes |
| `location$raw` | Storage locations |
| `dropdown$raw` | Dropdown definitions |

**Schema-Specific Tables:**
Schema entities have dedicated tables named `{schema_system_name}$raw`:
- `ngs_library_prep_sample$raw`
- `ngs_pooled_sample$raw`
- `ngs_run$raw`
- `ngs_run_output_v2$raw`

---

## Subagents

### benchling_expert

Handles complex Benchling queries that require multi-step reasoning.

**Use Cases:**
- Finding samples across multiple runs
- Tracing sample lineage (parent → child relationships)
- Reconciling data discrepancies
- Complex filtering with multiple criteria

**Example Query:**
```
User: "Find all my HeLa samples from the last month that haven't been processed yet"

benchling_expert:
1. Query library prep samples with Cell_Line = HeLa from last month
2. For each sample, traverse relationships to find NGS Run Outputs
3. Cross-reference with existing pipeline runs in Arc Reactor
4. Return samples without completed pipeline runs
```

**Configuration:**
```python
benchling_expert = {
    "name": "benchling_expert",
    "description": "Expert at complex Benchling queries involving multiple data sources, relationship traversal, and data reconciliation",
    "prompt": """You are an expert at querying Arc Institute's Benchling database.
    
    You have deep knowledge of:
    - NGS workflow: samples → library prep → pooling → sequencing
    - Benchling schema relationships and entity link fields
    - Common data quality issues and how to handle them
    
    When given a complex query:
    1. Break it down into simpler sub-queries
    2. Use get_entity_relationships for lineage traversal
    3. Combine and reconcile results
    4. Present a clear summary
    
    Available schemas in the NGS workflow:
    - NGS Library Prep Sample: Individual samples prepared for sequencing
    - NGS Pooled Sample: Pooled samples ready for loading
    - NGS Run: Sequencing run metadata
    - NGS Run Output v2: Per-sample outputs with FASTQ paths
    """,
    "tools": [search_ngs_runs, get_ngs_run_samples, get_entities, get_entity_relationships, list_entries, get_entry_entities, execute_warehouse_query],
    "model": "google_genai:gemini-3-flash-preview",
}
```

### config_expert

Helps users choose optimal pipeline parameters.

**Use Cases:**
- Recommending aligner based on sample type
- Estimating resource requirements
- Explaining parameter trade-offs
- Troubleshooting configuration issues

**Example Query:**
```
User: "Should I use cellranger or simpleaf for my 10X v3 samples?"

config_expert:
Based on your 48 10X Genomics v3 samples:

**Recommendation: simpleaf**

Reasons:
1. Faster execution (2-3x faster than cellranger)
2. Lower memory requirements
3. Comparable accuracy for standard analyses
4. No license restrictions

Consider cellranger if:
- You need specific cellranger-only features (e.g., CRISPR analysis)
- Your downstream tools require cellranger outputs
- You're comparing to previous cellranger results
```

**Configuration:**
```python
config_expert = {
    "name": "config_expert",
    "description": "Expert at Nextflow pipeline configuration, parameter selection, and resource optimization",
    "prompt": """You are an expert at configuring bioinformatics pipelines.
    
    You have deep knowledge of:
    - nf-core pipeline parameters and their effects
    - Aligner strengths and weaknesses
    - Resource requirements for different data types
    - Common configuration pitfalls
    
    When helping with configuration:
    1. Understand the user's data and goals
    2. Recommend appropriate parameters with explanations
    3. Warn about potential issues
    4. Estimate runtime and costs
    """,
    "tools": [list_pipelines, get_pipeline_schema, get_dropdown_values],
    "model": "google_genai:gemini-3-flash-preview",
}
```

---

## Conversation Patterns

### Pattern 1: SspArc-Based Discovery

The most common workflow where users reference their sequencing submission.

```
User: I want to process my SspArc0050 dataset

Agent: [Calls search_ngs_runs(pooled_sample="SspArc0050")]

I found your SspArc0050 sequencing data:

**NGS Run:** NR-2024-0156
**Instrument:** NovaSeqX
**Completion Date:** December 18, 2024
**Sample Count:** 24 samples
**QC Status:** ✓ PASS (94.5% average Q30)

Would you like me to:
1. Show detailed sample information
2. Check the QC metrics
3. Generate a samplesheet for analysis

User: Show me the samples

Agent: [Calls get_ngs_run_samples(pooled_sample="SspArc0050")]

Here are all 24 samples from SspArc0050:

| Sample   | Cell Line | Organism | Read Count | Q30 % | Status |
|----------|-----------|----------|------------|-------|--------|
| LPS-001  | HeLa      | Human    | 45M        | 94.2% | ✓      |
| LPS-002  | HeLa      | Human    | 42M        | 93.8% | ✓      |
...

All FASTQ files are available. Ready to generate the samplesheet?
```

### Pattern 2: Recent Runs Search

```
User: What runs have I submitted recently?

Agent: [Calls search_ngs_runs(submitter="[user name]", days_back=30)]

Here are your NGS runs from the last 30 days:

| Run          | SspArc    | Date       | Samples | Instrument  | Status |
|--------------|-----------|------------|---------|-------------|--------|
| NR-2024-0156 | SspArc0050| Dec 18     | 24      | NovaSeqX    | ✓      |
| NR-2024-0152 | SspArc0048| Dec 16     | 12      | NovaSeqX    | ✓      |
| NR-2024-0149 | SspArc0047| Dec 14     | 8       | NextSeq2000 | ✓      |

Which run would you like to work with?
```

### Pattern 3: Guided Discovery

```
User: I want to run scRNA-seq analysis

Agent: I'd be happy to help you set up a single-cell RNA-seq analysis! 

To find your samples, I'll need a bit more information:
- Do you have a specific SspArc ID or NGS run name?
- Or should I search by your name, project, or date range?

User: Search for my HeLa samples from last week

Agent: [Calls search_ngs_runs(submitter="[user]", days_back=7, include_qc_summary=True)]
[Calls get_ngs_run_samples for matching runs]

I found 24 HeLa samples from 2 NGS runs last week:

1. **NR-2024-0156** (Dec 18) - 12 samples, avg Q30: 94.2%
2. **NR-2024-0152** (Dec 16) - 12 samples, avg Q30: 93.8%

All samples have FASTQ files available. Which run would you like to analyze?
```

### Pattern 4: QC Assessment

```
User: Show me the QC for SspArc0050

Agent: [Calls get_ngs_run_qc(pooled_sample="SspArc0050", level="summary")]

**NGS Run QC Summary: NR-2024-0156**

Run Metrics:
  - Instrument: NovaSeqX
  - Completion Date: December 18, 2024
  - Total Samples: 24
  - Total Reads: 1.2B
  - Average Q30: 94.5%

Lane Performance:
  - Lane 1: 305M reads, 94.2% Q30 ✓
  - Lane 2: 298M reads, 94.8% Q30 ✓
  - Lane 3: 312M reads, 94.4% Q30 ✓
  - Lane 4: 285M reads, 94.6% Q30 ✓

**QC Status: ✓ PASS**

All lanes exceed the 90% Q30 threshold. Your data quality looks excellent!
Would you like to see per-sample QC details?
```

### Pattern 5: Error Recovery

```
User: Submit the run

Agent: [Calls validate_inputs]

I found 2 issues that need to be fixed before submission:

❌ **Missing FASTQ file**
   Sample LPS-012 is missing the R2 file
   Expected: gs://arc-ngs-data/NR-2024-0156/LPS-012_R2.fastq.gz

❌ **Invalid parameter**
   "genome" is set to "hg38" but should be "GRCh38"

How would you like to proceed?
1. Remove LPS-012 from the samplesheet
2. Let me check Benchling for the correct file path
3. I can fix the genome parameter for you
```

---

## State Management

### Conversation State

Each conversation maintains state through LangChain's checkpointer.

```python
# State persisted between turns
state = {
    "messages": [...],              # Full message history
    "current_ngs_run": "...",       # Active NGS run being configured
    "current_samples": [...],       # Samples from recent queries
    "generated_files": {
        "samplesheet": "...",
        "config": "...",
    },
    "validation_result": {...},
}
```

### Context Window Management

The agent uses several strategies to manage context:

1. **Automatic summarization**: At 85% context capacity, older messages are summarized
2. **Tool result offloading**: Large tool results (>20k tokens) are saved to agent state
3. **Selective context**: Only relevant past messages included in each turn

---

## Error Handling

### Tool Errors

| Error Type | Agent Response |
|------------|----------------|
| Benchling timeout | "I'm having trouble connecting to Benchling. Let me try again..." |
| No results found | "I couldn't find any NGS runs matching those criteria. Could you try..." |
| No samples found | "That run doesn't have any samples associated. Let me check the pooled sample..." |
| Invalid input | "That doesn't look like a valid [X]. The format should be..." |
| GCS access denied | "I don't have access to that storage location. Please check..." |
| SQL error | "That query couldn't be executed. The error was: [details]" |

### Graceful Degradation

If a tool fails, the agent:
1. Acknowledges the error clearly
2. Suggests alternative approaches
3. Offers to retry with different parameters
4. Never fabricates data

---

## Performance Considerations

### Latency Targets

| Operation | Target | Notes |
|-----------|--------|-------|
| First token | < 1s | Streaming starts immediately |
| search_ngs_runs | < 3s | Single optimized query |
| get_ngs_run_samples | < 5s | Includes metadata join |
| get_ngs_run_qc | < 5s | Aggregation query |
| Simple entity query | < 3s | Single get_entities call |
| Relationship traversal | < 8s | Depth-limited traversal |
| Complex query | < 15s | Multiple tool calls |
| File generation | < 10s | Includes GCS validation |

### Optimization Strategies

1. **Parallel tool calls**: When multiple independent tools are needed
2. **Caching**: Schema and dropdown lookups cached for 5 minutes
3. **Streaming**: All responses stream token-by-token
4. **Early validation**: Catch errors before expensive operations
5. **Result limiting**: Default limits on all queries to prevent overwhelming responses

### Query Optimization

```python
# Good: Specific filters reduce warehouse load
search_ngs_runs(
    pooled_sample="SspArc0050",
    include_qc_summary=False,  # Only if needed
)

# Good: Date range limits result set
search_ngs_runs(
    submitter="Jane Smith",
    days_back=30,
    limit=20,
)

# Avoid: Broad queries without filters
search_ngs_runs(
    use_wildcards=True,
    ngs_run="%",  # Too broad
    limit=1000,   # Too many results
)
```

---

## Security Considerations

### Data Access

- Agent can only read Benchling data (no writes)
- Agent can only access GCS buckets user has permission for
- All actions logged with user identity
- SQL queries restricted to SELECT statements only

### Prompt Injection Protection

- User input sanitized before inclusion in prompts
- Tool parameters validated before execution
- No arbitrary code execution
- SQL injection prevented via parameterized queries

### Human-in-the-Loop

Critical operations require explicit user approval:
- Pipeline submission (always)
- Run cancellation
- Any tool that modifies or deletes GCS files (samplesheet/config/params)
- Removing samples from a samplesheet (if implemented)
- Cost-incurring or expensive Benchling queries (large date ranges, wide searches)

**Required HITL tools:**
- `submit_run`
- `cancel_run`
- `delete_file`
- `clear_samplesheet`

**Policy:**
- Tools that write to external systems or incur significant cost must request approval.
- The agent must summarize the impact and ask for confirmation before execution.
