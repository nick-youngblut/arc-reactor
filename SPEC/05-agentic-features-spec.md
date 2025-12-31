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
│  │  Benchling Discovery:       │  │  benchling_expert:                  │   │
│  │  • get_entities             │  │  • Complex multi-step queries       │   │
│  │  • get_entity_relationships │  │  • Relationship traversal           │   │
│  │  • list_entries             │  │  • Data reconciliation              │   │
│  │  • get_entry_content        │  │                                     │   │
│  │  • get_entry_entities       │  │  config_expert:                     │   │
│  │                             │  │  • Protocol recommendations         │   │
│  │  Schema & Metadata:         │  │  • Parameter optimization           │   │
│  │  • get_schemas              │  │  • Resource estimation              │   │
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
│  │  • FilesystemMiddleware - Context offloading (for large results)      │  │
│  │  • SummarizationMiddleware - Auto-summarize at 85% context            │  │
│  │  • HumanInTheLoopMiddleware - Approval for destructive/costly tools   │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Reference code repositories

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

1. **Find samples**: Search Benchling for entities and samples by name, schema, project, or other criteria
2. **Explore relationships**: Trace sample lineage through entity relationships
3. **Access protocols**: Read notebook entries for experimental context
4. **Generate files**: Create samplesheet CSV files and Nextflow configuration files
5. **Configure pipelines**: Help users choose appropriate pipeline parameters
6. **Validate inputs**: Check that all required files exist and parameters are valid
7. **Submit runs**: Submit validated pipeline runs to GCP Batch

## Guidelines

- Be conversational and guide users step-by-step
- Many users have limited computational experience; explain things clearly
- Always confirm understanding before generating files
- Present options when there are multiple valid choices
- Validate configurations before allowing submission
- If you're unsure, ask clarifying questions

## Workflow

A typical interaction follows this pattern:

1. User describes what they want to analyze
2. You search Benchling to find matching samples
3. You present options and ask for confirmation
4. You generate samplesheet and config files
5. User reviews/edits the files
6. You validate and submit the run

## Important Rules

- Never fabricate sample data; always query Benchling; always validate any data in your responses
- Always show the user what files you've generated
- Require explicit user confirmation before submission
- If a validation fails, explain clearly what's wrong and how to fix it
```

## Tool Specifications

### Benchling Service Dependency

All Benchling tools use the `benchling-py` library for warehouse access. The service
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

### Benchling Discovery Tools

#### get_entities

Search for entities in the Benchling data warehouse with flexible filtering.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `entity_names` | string | Yes | Entity names (semicolon-delimited) |
| `schema_names` | string | No | Filter by schema names (semicolon-delimited) |
| `project_names` | string | No | Filter by project names (semicolon-delimited) |
| `use_wildcards` | boolean | No | Treat names as SQL wildcard patterns (default: false) |
| `limit` | integer | No | Maximum results to return (default: 100) |

**Returns:**
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
    
    Args:
        entity_names: Entity names (semicolon-delimited)
        schema_names: Filter by schema names (semicolon-delimited)
        project_names: Filter by project names (semicolon-delimited)
        use_wildcards: Treat names as SQL wildcard patterns
        limit: Maximum results to return
    
    Returns:
        Formatted table of matching entities
    """
    # Parse semicolon-delimited inputs
    names = [n.strip() for n in entity_names.split(";") if n.strip()]
    schemas = [s.strip() for s in schema_names.split(";")] if schema_names else None
    projects = [p.strip() for p in project_names.split(";")] if project_names else None
    
    # Query warehouse via benchling-py
    result = benchling_service.warehouse.entity.get(
        entity_names=names,
        schema_names=schemas,
        project_names=projects,
        use_wildcards=use_wildcards,
        limit=limit,
        return_format="dataframe",
    )
    
    # Format for display
    return format_entity_table(result)
```

#### get_entity_relationships

Discover and traverse relationships between Benchling entities through custom entity link (CEL) fields.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `entity_name` | string | Yes | Name of the entity to analyze |
| `relationship_depth` | integer | No | How many levels deep to traverse (1-10, default: 4) |
| `relationship_types` | string | No | Field names to follow (semicolon-delimited; None = all) |
| `include_reverse_links` | boolean | No | Include entities that link TO this entity (default: true) |
| `schema_name` | string | No | Schema name if known (improves disambiguation) |
| `output_format` | string | No | Output format: tree, yaml, or json (default: tree) |
| `max_results` | integer | No | Maximum relationships to return (default: 500) |

**Returns (tree format):**
```
Entity Relationships for LPS-001 (NGS Library Prep Sample)

LPS-001 (NGS Library Prep Sample)
├── [→ NGS Pooled Sample] LPS-001-P1
│   └── [→ NGS Run] NR-2024-0156
│       └── [→ NGS Run Output v2] LPS-001-R1
│           ├── fastq_r1: gs://arc-ngs-data/NR-2024-0156/LPS-001_R1.fastq.gz
│           └── fastq_r2: gs://arc-ngs-data/NR-2024-0156/LPS-001_R2.fastq.gz
└── [← Cell Line Lot] HeLa-Lot-2024-001
    └── [← Cell Line] HeLa
```

**Implementation Notes:**
- Uses `benchling_py.warehouse.RelationshipNavigator` for traversal
- Forward links (→) follow CEL fields from source entity
- Reverse links (←) find entities that reference this entity
- High `relationship_depth` (4-10) often needed for full NGS workflow traversal

#### list_entries

List Benchling notebook entries with flexible filtering.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `entry_names` | string | No | Entry names (semicolon-delimited) |
| `project_names` | string | No | Project names (semicolon-delimited) |
| `folder_names` | string | No | Folder names (semicolon-delimited) |
| `creator_names` | string | No | Creator names (semicolon-delimited) |
| `min_date` | string | No | Minimum date (YYYY-MM-DD) |
| `max_date` | string | No | Maximum date (YYYY-MM-DD) |
| `archived` | boolean | No | Include archived entries (default: false) |
| `allow_wildcards` | boolean | No | Recognize SQL wildcards (%, _) in names |
| `limit` | integer | No | Maximum results (default: 50) |

**Returns:**
```
Found 5 entries in project "Smith_RNAseq":

entry_name                    | project        | folder    | creator          | modified_at
------------------------------|----------------|-----------|------------------|------------------
10X Library Prep Protocol v3  | Smith_RNAseq   | Protocols | jane.smith       | 2024-12-15
NR-2024-0156 QC Report        | Smith_RNAseq   | QC        | lab.automation   | 2024-12-18
HeLa Perturbation Experiment  | Smith_RNAseq   | Data      | jane.smith       | 2024-12-10
```

**Implementation:**
```python
@tool
def list_entries(
    entry_names: str | None = None,
    project_names: str | None = None,
    folder_names: str | None = None,
    creator_names: str | None = None,
    min_date: str | None = None,
    max_date: str | None = None,
    archived: bool = False,
    allow_wildcards: bool = False,
    limit: int = 50,
) -> str:
    """List Benchling notebook entries filtered by optional criteria.
    
    Returns entry metadata only, not content. Use get_entry_content
    to retrieve the full notebook content.
    """
    # Parse dates
    min_dt = datetime.strptime(min_date, "%Y-%m-%d") if min_date else None
    max_dt = datetime.strptime(max_date, "%Y-%m-%d") if max_date else None
    
    result = benchling_service.warehouse.entry.get(
        entry_names=parse_semicolon(entry_names),
        project_names=parse_semicolon(project_names),
        folder_names=parse_semicolon(folder_names),
        creator_names=parse_semicolon(creator_names),
        min_modified_date=min_dt,
        max_modified_date=max_dt,
        archived=archived,
        use_wildcards=allow_wildcards,
        limit=limit,
        return_format="dataframe",
    )
    
    return format_entry_table(result)
```

#### get_entry_content

Retrieve the full content of a Benchling notebook entry as markdown.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `entry_names` | string | Yes | Entry names (semicolon-delimited) |
| `head` | integer | No | Number of lines from the beginning |
| `tail` | integer | No | Number of lines from the end |

**Returns:**
```markdown
# 10X Library Prep Protocol v3

## Materials
- 10X Genomics Chromium Controller
- Chromium Single Cell 3' Reagent Kit v3
- ...

## Procedure
1. Cell Preparation
   - Harvest cells at 80-90% confluency
   - ...

## Quality Control
- Target cell viability: >90%
- Target cell concentration: 700-1200 cells/µL
```

**Implementation Notes:**
- Uses Benchling API to fetch entry content
- Converts structured entry content to markdown
- `head`/`tail` parameters useful for long protocols

#### get_entry_entities

Get entities associated with a Benchling notebook entry.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `entry_name` | string | Yes | Entry name |
| `limit` | integer | No | Maximum entities to return (default: 50) |

**Returns:**
```
Entities registered from entry "HeLa Perturbation Experiment":

entity_name | entity_schema           | entity_type | entity_url
------------|-------------------------|-------------|---------------------------
LPS-001     | NGS Library Prep Sample | custom      | https://arcinstitute...
LPS-002     | NGS Library Prep Sample | custom      | https://arcinstitute...
LPS-003     | NGS Library Prep Sample | custom      | https://arcinstitute...
```

**Use Cases:**
- Find all samples registered from a specific experiment
- Trace which entities originated from a protocol run
- Link experimental context to pipeline inputs

### Schema & Metadata Tools

#### get_schemas

Get information about Benchling schemas.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `schema_names` | string | No | Schema names (semicolon-delimited) |
| `list_all` | boolean | No | Return list of all schema names (default: false) |

**Returns:**
```
Schema information:

name                    | system_name               | schema_type | field_count
------------------------|---------------------------|-------------|------------
NGS Library Prep Sample | ngs_library_prep_sample   | entity      | 24
NGS Pooled Sample       | ngs_pooled_sample         | entity      | 12
NGS Run                 | ngs_run                   | entity      | 18
NGS Run Output v2       | ngs_run_output_v2         | entity      | 15
```

#### get_schema_field_info

Get detailed field information for a specific schema.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `schema_name` | string | Yes | Name of the schema |

**Returns:**
```
Fields for schema "NGS Library Prep Sample":

field_name         | field_type           | linked_schema      | linked_dropdown    | required
-------------------|----------------------|--------------------|--------------------|---------
Sample_ID          | text                 |                    |                    | true
Project            | entity_link          | Project            |                    | true
Cell_Line          | entity_link          | Cell Line          |                    | false
Lib_Prep_Kit_Used  | dropdown             |                    | NGS_Lib_Prep_Kits  | true
Protocol_Version   | dropdown             |                    | Protocol_Versions  | false
Parent_Sample      | custom_entity_link   | NGS Library Prep   |                    | false
Concentration      | decimal              |                    |                    | false
```

**Use Cases:**
- Understand required vs optional fields before generating samplesheets
- Discover entity relationships for lineage traversal
- Identify dropdown fields for valid value lookup

#### get_dropdown_values

Get available values for a Benchling dropdown.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `dropdown_name` | string | Yes | Name of the dropdown |

**Returns:**
```
Dropdown "NGS_Lib_Prep_Kits" values:

10X Genomics 3' v2, 10X Genomics 3' v3, 10X Genomics 3' v4, 10X Genomics 5' v2, 
Smart-seq2, Smart-seq3, Drop-seq, SHARE-seq
```

**Use Cases:**
- Validate protocol/kit selections
- Auto-suggest valid values to users
- Map sample metadata to pipeline parameters

#### list_projects

List all projects in the Benchling data warehouse.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `filter_pattern` | string | No | Wildcard pattern to filter project names |

**Returns:**
```
Available projects:

Smith_RNAseq, Garcia_TimeCourse, Chen_CRISPR_Screen, Johnson_DrugDiscovery,
Lee_NeuralOrganoids, Kim_TCellEngineering, Park_GenomeEditing, ...
```

### Pipeline Information Tools

#### list_pipelines

List all available pipelines.

**Parameters:** None

**Returns:**
```
Available Pipelines:

1. **nf-core/scrnaseq** (v2.7.1)
   Single-cell RNA sequencing analysis
   Supports: 10X Genomics, Drop-seq, Smart-seq

2. **nf-core/rnaseq** (v3.14.0) [Coming Soon]
   Bulk RNA sequencing analysis
```

#### get_pipeline_schema

Get the input requirements for a specific pipeline.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `pipeline` | string | Yes | Pipeline name |
| `version` | string | No | Pipeline version (default: latest) |

**Returns:**
```
**nf-core/scrnaseq v2.7.1** Input Requirements:

Samplesheet Columns:
• sample (required): Sample identifier
• fastq_1 (required): Path to R1 FASTQ file
• fastq_2 (required): Path to R2 FASTQ file
• expected_cells (optional): Expected number of cells

Required Parameters:
• genome: Reference genome (GRCh38 or GRCm39)
• protocol: 10X protocol version (10XV2, 10XV3, 10XV4)

Optional Parameters:
• aligner: Alignment tool (simpleaf, star, kallisto, cellranger)
  Default: simpleaf
• expected_cells: Default expected cells per sample
  Default: 10000
```

### File Generation Tools

#### generate_samplesheet

Generate a samplesheet CSV from Benchling entity data.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `entity_names` | string | Yes | Entity names to include (semicolon-delimited) |
| `schema_name` | string | No | Schema to filter entities |
| `pipeline` | string | Yes | Target pipeline (for column format) |
| `additional_columns` | dict | No | Extra column values to add |

**Returns:**
```json
{
  "csv_content": "sample,fastq_1,fastq_2,expected_cells\nLPS-001,gs://...,gs://...,10000\n...",
  "sample_count": 24,
  "columns": ["sample", "fastq_1", "fastq_2", "expected_cells"],
  "warnings": ["3 samples missing expected_cells, using default 10000"]
}
```

**Implementation Notes:**
- Uses `get_entity_relationships` internally to find FASTQ paths
- Maps Benchling metadata to pipeline-specific columns
- Validates required columns before returning

**Side Effects:**
- Updates frontend state with generated CSV
- Displays samplesheet in editor panel

#### generate_config

Generate a Nextflow configuration file.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `pipeline` | string | Yes | Pipeline name |
| `params` | dict | Yes | Pipeline parameters |
| `run_id` | string | Yes | Unique run identifier |

**Returns:**
```json
{
  "config_content": "params {\n  input = \"gs://...\"\n  ...\n}",
  "params_summary": {
    "genome": "GRCh38",
    "protocol": "10XV3",
    "aligner": "simpleaf"
  }
}
```

**Side Effects:**
- Updates frontend state with generated config
- Displays config in editor panel

### Validation Tools

#### validate_inputs

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

**Validation Checks:**
1. All required samplesheet columns present
2. All FASTQ files exist in GCS
3. All required parameters provided
4. Parameter values are valid (enums, ranges)
5. Config syntax is valid Groovy

### Submission Tools

#### submit_run

Submit a validated pipeline run to GCP Batch.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `samplesheet_csv` | string | Yes | Validated CSV content |
| `config_content` | string | Yes | Validated config content |
| `pipeline` | string | Yes | Pipeline name |
| `pipeline_version` | string | Yes | Pipeline version |

**Human-in-the-Loop:**
This tool requires explicit user approval before execution.

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

#### cancel_run

Cancel a running pipeline job.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `run_id` | string | Yes | Run identifier |

**Human-in-the-Loop:**
This tool requires explicit user approval before execution.

**Returns:**
```json
{
  "run_id": "run-abc123",
  "status": "cancelled",
  "message": "Run cancellation requested. It may take a few minutes to stop all tasks."
}
```

#### delete_file

Delete a run file from GCS (dangerous operation).

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `run_id` | string | Yes | Run identifier |
| `file_path` | string | Yes | Path relative to the run root (e.g., `inputs/samplesheet.csv`) |

**Human-in-the-Loop:**
This tool requires explicit user approval before execution.

**Returns:**
```json
{
  "run_id": "run-abc123",
  "deleted": "inputs/samplesheet.csv",
  "message": "File deleted successfully."
}
```

#### clear_samplesheet

Remove all rows from the current samplesheet.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `confirm` | boolean | Yes | Must be true to proceed |

**Human-in-the-Loop:**
This tool requires explicit user approval before execution.

**Returns:**
```json
{
  "cleared": true,
  "message": "Samplesheet cleared. You can undo by regenerating from Benchling."
}
```

### Advanced Tools

#### execute_warehouse_query

Execute a read-only SQL query against the Benchling data warehouse. This is an
escape hatch for complex queries that cannot be expressed through the standard tools.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `sql` | string | Yes | SQL query (SELECT only) |
| `params` | dict | No | Query parameters (for parameterized queries) |
| `limit` | integer | No | Maximum rows to return (default: 100, max: 1000) |

**Human-in-the-Loop:**
This tool does NOT require explicit user approval

**Returns:**
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
    "tools": [get_entities, get_entity_relationships, list_entries, get_entry_entities, execute_warehouse_query],
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

## Conversation Patterns

### Pattern 1: Guided Discovery

```
User: I want to run scRNA-seq analysis

Agent: I'd be happy to help you set up a single-cell RNA-seq analysis! 

To find your samples, I'll need a bit more information:
- Do you have specific sample names or an NGS run in mind?
- Or would you like me to search by project, date, or cell type?

User: Search for my HeLa samples from last week

Agent: [Calls get_entities with schema="NGS Library Prep Sample" and wildcards]
[Calls get_entity_relationships to find associated NGS runs]

I found 24 HeLa samples from 2 NGS runs last week:

1. **NR-2024-0156** (Dec 18) - 12 samples, Project: Smith_RNAseq
2. **NR-2024-0152** (Dec 16) - 12 samples, Project: Garcia_TimeCourse

All samples have FASTQ files available. Which run would you like to analyze?
```

### Pattern 2: Direct Request

```
User: Create a samplesheet for samples LPS-001 through LPS-024

Agent: [Calls get_entities with entity_names and wildcards]
[Calls get_entity_relationships to find FASTQ paths]
[Calls generate_samplesheet]

I've created a samplesheet with 24 samples:

The samplesheet includes:
- 24 samples with FASTQ paths
- Expected cells set to 10,000 (default)
- All samples from NGS Run NR-2024-0156

You can review and edit the samplesheet in the panel on the right. 

Would you like me to generate the pipeline configuration next?
```

### Pattern 3: Sample Lineage Investigation

```
User: Show me the full history for sample LPS-001

Agent: [Calls get_entity_relationships with depth=5]

Here's the complete lineage for LPS-001:

**Sample Lineage:**
```
Cell Line: HeLa
  └─ Cell Line Lot: HeLa-Lot-2024-001
      └─ NGS Library Prep Sample: LPS-001
          ├─ Protocol: 10X Library Prep Protocol v3
          ├─ Lib_Prep_Kit: 10X Genomics 3' v3
          └─ NGS Pooled Sample: Pool-2024-156-A
              └─ NGS Run: NR-2024-0156
                  └─ NGS Run Output v2: LPS-001-R1
                      ├─ fastq_r1: gs://arc-ngs-data/.../LPS-001_R1.fastq.gz
                      └─ fastq_r2: gs://arc-ngs-data/.../LPS-001_R2.fastq.gz
```

Would you like me to include this sample in a samplesheet?
```

### Pattern 4: Protocol Context

```
User: What protocol was used for these samples?

Agent: [Calls list_entries with project filter]
[Calls get_entry_content]

These samples were prepared using the **10X Library Prep Protocol v3** (last updated Dec 15, 2024).

Key parameters from the protocol:
- Target cell viability: >90%
- Target cell concentration: 700-1200 cells/µL
- GEM generation: 10,000 cells target

Would you like me to show the full protocol or proceed with configuration?
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

## State Management

### Conversation State

Each conversation maintains state through LangChain's checkpointer.

```python
# State persisted between turns
state = {
    "messages": [...],              # Full message history
    "current_entities": [...],      # Entities from recent queries
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
2. **Tool result offloading**: Large tool results (>20k tokens) are saved to filesystem
3. **Selective context**: Only relevant past messages included in each turn

## Error Handling

### Tool Errors

| Error Type | Agent Response |
|------------|----------------|
| Benchling timeout | "I'm having trouble connecting to Benchling. Let me try again..." |
| No results found | "I couldn't find any entities matching those criteria. Could you try..." |
| Invalid input | "That doesn't look like a valid [X]. The format should be..." |
| GCS access denied | "I don't have access to that storage location. Please check..." |
| SQL error | "That query couldn't be executed. The error was: [details]" |

### Graceful Degradation

If a tool fails, the agent:
1. Acknowledges the error clearly
2. Suggests alternative approaches
3. Offers to retry with different parameters
4. Never fabricates data

## Performance Considerations

### Latency Targets

| Operation | Target | Notes |
|-----------|--------|-------|
| First token | < 1s | Streaming starts immediately |
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

### Benchling Query Optimization

```python
# Good: Specific filters reduce warehouse load
get_entities(
    entity_names="LPS-%",
    schema_names="NGS Library Prep Sample",
    project_names="Smith_RNAseq",
    use_wildcards=True,
    limit=100,
)

# Avoid: Broad queries without filters
get_entities(
    entity_names="%",  # Too broad
    use_wildcards=True,
    limit=10000,  # Too many results
)
```

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