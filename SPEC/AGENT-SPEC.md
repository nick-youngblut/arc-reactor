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
│  │  Sample Discovery:          │  │  benchling_expert:                  │   │
│  │  • search_ngs_runs          │  │  • Complex multi-step queries       │   │
│  │  • get_run_samples          │  │  • Relationship traversal           │   │
│  │  • get_sample_metadata      │  │  • Data reconciliation              │   │
│  │                             │  │                                     │   │
│  │  Pipeline Info:             │  │  config_expert:                     │   │
│  │  • list_pipelines           │  │  • Protocol recommendations         │   │
│  │  • get_pipeline_schema      │  │  • Parameter optimization           │   │
│  │                             │  │  • Resource estimation              │   │
│  │  File Generation:           │  │                                     │   │
│  │  • generate_samplesheet     │  │                                     │   │
│  │  • generate_config          │  │                                     │   │
│  │                             │  │                                     │   │
│  │  Validation & Submission:   │  │                                     │   │
│  │  • validate_inputs          │  │                                     │   │
│  │  • submit_run (HITL)        │  │                                     │   │
│  └─────────────────────────────┘  └─────────────────────────────────────┘   │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                       MIDDLEWARE STACK                                │  │
│  │                                                                       │  │
│  │  • TodoListMiddleware - Task planning and tracking                    │  │
│  │  • FilesystemMiddleware - Context offloading (for large results)      │  │
│  │  • SummarizationMiddleware - Auto-summarize at 85% context            │  │
│  │  • HumanInTheLoopMiddleware - Approval for submit_run                 │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Agent Configuration

### Model Selection

Model configuration values are defined in `SPEC/CONFIG-SPEC.md` and must be
referenced from there to avoid drift.

### System Prompt

```markdown
You are a helpful assistant for wet lab scientists at Arc Institute. Your job is to help users set up Nextflow bioinformatics pipeline runs.

## Your Capabilities

1. **Find samples**: Search Benchling for NGS runs and samples by date, project, instrument, or other criteria
2. **Generate files**: Create samplesheet CSV files and Nextflow configuration files
3. **Configure pipelines**: Help users choose appropriate pipeline parameters
4. **Validate inputs**: Check that all required files exist and parameters are valid
5. **Submit runs**: Submit validated pipeline runs to GCP Batch

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

- Never fabricate sample data; always query Benchling
- Always show the user what files you've generated
- Require explicit user confirmation before submission
- If a validation fails, explain clearly what's wrong and how to fix it
```

## Tool Specifications

### Sample Discovery Tools

#### search_ngs_runs

Search for NGS runs in Benchling by various criteria.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `days_back` | integer | No | How many days back to search (default: 30) |
| `instrument` | string | No | Filter by instrument (NovaSeq, NextSeq, etc.) |
| `project` | string | No | Filter by project name |
| `submitter` | string | No | Filter by submitter email |

**Returns:**
```
Found 3 NGS runs from the past 2 weeks:

• **NR-2024-0156** (Dec 18, 2024)
  - Instrument: NovaSeq X
  - Project: Smith_RNAseq
  - Samples: 48
  - Submitter: jane.smith@arcinstitute.org

• **NR-2024-0152** (Dec 16, 2024)
  - Instrument: NextSeq 2000
  - Project: Garcia_TimeCourse
  - Samples: 24
  - Submitter: carlos.garcia@arcinstitute.org

• **NR-2024-0148** (Dec 14, 2024)
  ...
```

**Implementation Notes:**
- Queries `benchling_service.get_lib_prep_samples()` with date filter
- Aggregates by `ngs_run` to provide summary
- Caches instrument/project lists for autocomplete suggestions

#### get_run_samples

Get detailed sample information for a specific NGS run.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `ngs_run` | string | Yes | NGS run name (e.g., "NR-2024-0156") |
| `include_metadata` | boolean | No | Include full metadata (default: true) |

**Returns:**
```
**NR-2024-0156** contains 48 library prep samples:

By Cell Line:
• 24 samples: Human, HeLa
• 24 samples: Human, HEK293

By Protocol:
• 48 samples: 10X Genomics 3' v3

FASTQ Status:
• 48/48 samples have FASTQ paths available
• Location: gs://arc-ngs-data/NR-2024-0156/

Sample IDs: LPS-001, LPS-002, LPS-003, ... (48 total)
```

#### get_sample_metadata

Get detailed metadata for specific samples.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `sample_ids` | list[string] | Yes | List of sample IDs |

**Returns:**
```
Sample: LPS-001
• Organism: Homo sapiens
• Cell Line: HeLa
• Tissue: Cervix
• Perturbation: DMSO control
• Replicate: 1
• FASTQ R1: gs://arc-ngs-data/NR-2024-0156/LPS-001_R1.fastq.gz
• FASTQ R2: gs://arc-ngs-data/NR-2024-0156/LPS-001_R2.fastq.gz
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

Generate a samplesheet CSV from Benchling samples.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `ngs_run` | string | Yes | NGS run to pull samples from |
| `sample_filter` | dict | No | Filters (cell_line, organism, etc.) |
| `pipeline` | string | Yes | Target pipeline (for column format) |
| `additional_columns` | dict | No | Extra column values to add |

**Returns:**
```json
{
  "csv_content": "sample,fastq_1,fastq_2,expected_cells\nLPS-001,gs://...,gs://...,10000\n...",
  "sample_count": 24,
  "columns": ["sample", "fastq_1", "fastq_2", "expected_cells"],
  "warnings": []
}
```

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
1. Query all runs from last month
2. Filter to HeLa samples
3. Cross-reference with existing pipeline runs
4. Return unprocessed samples
```

**Configuration:**
```python
benchling_expert = {
    "name": "benchling_expert",
    "description": "Expert at complex Benchling queries involving multiple data sources, relationship traversal, and data reconciliation",
    "prompt": """You are an expert at querying Arc Institute's Benchling database.
    
    You have deep knowledge of:
    - NGS workflow: samples → library prep → pooling → sequencing
    - Benchling schema relationships
    - Common data quality issues and how to handle them
    
    When given a complex query:
    1. Break it down into simpler sub-queries
    2. Execute each sub-query
    3. Combine and reconcile results
    4. Present a clear summary
    """,
    "tools": [search_ngs_runs, get_run_samples, get_sample_metadata],
    "model": "anthropic:claude-sonnet-4-5-20250929",
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
    "tools": [list_pipelines, get_pipeline_schema],
    "model": "anthropic:claude-sonnet-4-5-20250929",
}
```

## Conversation Patterns

### Pattern 1: Guided Discovery

```
User: I want to run scRNA-seq analysis

Agent: I'd be happy to help you set up a single-cell RNA-seq analysis! 

To find your samples, I'll need a bit more information:
- Do you have a specific NGS run in mind?
- Or would you like me to search by project, date, or submitter?

User: Search for my runs from last week

Agent: [Calls search_ngs_runs with days_back=7 and submitter=current_user]

I found 2 NGS runs from last week:

1. **NR-2024-0156** (Dec 18) - 48 samples, Project: CellAtlas
2. **NR-2024-0152** (Dec 16) - 12 samples, Project: DrugScreen

Which run would you like to analyze?
```

### Pattern 2: Direct Request

```
User: Create a samplesheet for NR-2024-0156 with just the HeLa samples

Agent: [Calls get_run_samples]
[Calls generate_samplesheet with filter]

I've created a samplesheet with 24 HeLa samples from NR-2024-0156. 

The samplesheet includes:
- 24 samples with FASTQ paths
- Expected cells set to 10,000 (default)

You can review and edit the samplesheet in the panel on the right. 

Would you like me to generate the pipeline configuration next?
```

### Pattern 3: Error Recovery

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
2. Check Benchling for the correct file path
3. I can fix the genome parameter for you
```

### Pattern 4: Parameter Guidance

```
User: What aligner should I use?

Agent: [Calls config_expert subagent]

For your 24 10X Genomics v3 HeLa samples, here's my recommendation:

**Recommended: simpleaf** (default)

| Aspect | simpleaf | cellranger | STARsolo |
|--------|----------|------------|----------|
| Speed | ⭐⭐⭐ Fast | ⭐ Slow | ⭐⭐ Medium |
| Memory | ⭐⭐⭐ Low | ⭐ High | ⭐⭐ Medium |
| Accuracy | ⭐⭐⭐ High | ⭐⭐⭐ High | ⭐⭐⭐ High |

simpleaf is the best choice for most analyses. Would you like me to proceed with simpleaf, or do you have a specific reason to use a different aligner?
```

## State Management

### Conversation State

Each conversation maintains state through LangChain's checkpointer.

```python
# State persisted between turns
state = {
    "messages": [...],              # Full message history
    "current_ngs_run": "NR-2024-0156",  # Context from tools
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
| No results found | "I couldn't find any samples matching those criteria. Could you try..." |
| Invalid input | "That doesn't look like a valid [X]. The format should be..." |
| GCS access denied | "I don't have access to that storage location. Please check..." |

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
| Simple query | < 5s | Single tool call |
| Complex query | < 15s | Multiple tool calls |
| File generation | < 10s | Includes GCS validation |

### Optimization Strategies

1. **Parallel tool calls**: When multiple independent tools are needed
2. **Caching**: Metadata lookups cached for 5 minutes
3. **Streaming**: All responses stream token-by-token
4. **Early validation**: Catch errors before expensive operations

## Security Considerations

### Data Access

- Agent can only read Benchling data (no writes)
- Agent can only access GCS buckets user has permission for
- All actions logged with user identity

### Prompt Injection Protection

- User input sanitized before inclusion in prompts
- Tool parameters validated before execution
- No arbitrary code execution

### Human-in-the-Loop

Critical operations require explicit user approval:
- Pipeline submission (always)
- File deletion (if implemented)
- Cost-incurring operations
