# Sprint 3: AI Agent & Agentic Features

## Overview

This sprint implements the core AI agent with LangChain/DeepAgents, including all Benchling discovery tools, file generation tools, conversation management, and Human-in-the-Loop approval workflows.

## References

- [05-agentic-features-spec.md](../spec/05-agentic-features-spec.md) - Agent architecture and tools
- [07-integration-spec.md](../spec/07-integration-spec.md) - Gemini API integration
- [11-conf-spec.md](../spec/11-conf-spec.md) - AI model configuration

---

## Phase 3.1: Agent Foundation

> **Spec References:**
> - [05-agentic-features-spec.md#agent-architecture](../spec/05-agentic-features-spec.md) - DeepAgents framework
> - [05-agentic-features-spec.md#agent-configuration](../spec/05-agentic-features-spec.md) - Model and prompt setup
> - [11-conf-spec.md#ai-model-configuration](../spec/11-conf-spec.md) - Gemini configuration values

### LangChain/DeepAgents Setup

- [x] Create `backend/agents/__init__.py`:
  - [x] Initialize agent module
  - [x] Export main agent classes

- [x] Create `backend/agents/pipeline_agent.py` — *See [05-agentic-features-spec.md#pipeline-agent](../spec/05-agentic-features-spec.md)*:
  - [x] Import LangChain DeepAgents framework
  - [x] Create `PipelineAgent` class
  - [x] Configure agent with tools and subagents

### Gemini Model Configuration

> **Spec References:**
> - [11-conf-spec.md#ai-model-configuration](../spec/11-conf-spec.md) - Model parameters
> - [07-integration-spec.md#google-gemini-api-integration](../spec/07-integration-spec.md) - API integration

- [x] Create `backend/agents/model.py` — *See [11-conf-spec.md#ai-model-configuration](../spec/11-conf-spec.md)*:
  - [x] Implement `get_chat_model()` function:
    - [x] Use `init_chat_model()` from langchain
    - [x] Model: `google_genai:gemini-3-flash-preview` — *See [11-conf-spec.md#model](../spec/11-conf-spec.md)*
    - [x] Temperature: 1.0 (required for thinking) — *See [11-conf-spec.md#temperature](../spec/11-conf-spec.md)*
    - [x] Max output tokens: 8192 — *See [11-conf-spec.md#max-output-tokens](../spec/11-conf-spec.md)*
    - [x] Thinking level from settings (default "low") — *See [11-conf-spec.md#thinking-level-options](../spec/11-conf-spec.md)*
  - [x] Support Vertex AI backend option — *See [07-integration-spec.md#authentication](../spec/07-integration-spec.md)*:
    - [x] Check for `GOOGLE_CLOUD_PROJECT` env var
    - [x] Set `vertexai=True` if using Vertex AI
  - [x] Implement streaming configuration

### System Prompt

> **Spec References:**
> - [05-agentic-features-spec.md#system-prompt](../spec/05-agentic-features-spec.md) - Complete system prompt

- [x] Create `backend/agents/prompts.py` — *See [05-agentic-features-spec.md#system-prompt](../spec/05-agentic-features-spec.md)*:
  - [x] Define `PIPELINE_AGENT_SYSTEM_PROMPT`:
    - [x] Role description (Arc Reactor AI assistant)
    - [x] Capabilities overview:
      - [x] Discover NGS samples from Benchling
      - [x] Generate pipeline configurations
      - [x] Validate and submit runs
      - [x] Provide guidance and troubleshooting
    - [x] Workflow guidance — *See [05-agentic-features-spec.md#common-conversation-patterns](../spec/05-agentic-features-spec.md)*:
      - [x] Start by understanding user's data
      - [x] Discover samples via NGS tools
      - [x] Generate samplesheet and config
      - [x] Validate before submission
      - [x] Explain errors and suggest fixes
    - [x] Important notes:
      - [x] SspArc refers to NGS Pooled Sample name
      - [x] Always verify data before generation
      - [x] Human approval required for submissions — *See [05-agentic-features-spec.md#human-in-the-loop](../spec/05-agentic-features-spec.md)*
    - [x] Schema knowledge:
      - [x] NGS workflow: samples → library prep → pooling → sequencing
      - [x] Key entities and relationships

### Conversation State Management

> **Spec References:**
> - [05-agentic-features-spec.md#state-management](../spec/05-agentic-features-spec.md) - Conversation persistence
> - [06-data-model-spec.md#checkpoints-table](../spec/06-data-model-spec.md) - Checkpoint storage

- [x] Create `backend/agents/checkpointer.py` — *See [05-agentic-features-spec.md#state-management](../spec/05-agentic-features-spec.md)*:
  - [x] Implement AsyncPostgresSaver for LangGraph:
    - [x] Use existing Cloud SQL connection
    - [x] Store checkpoints in `checkpoints` table — *See [06-data-model-spec.md#checkpoints-table](../spec/06-data-model-spec.md)*
  - [x] Configure checkpoint serialization
  - [x] Implement thread cleanup for old conversations

### DeepAgents Orchestration

> **Spec References:**
> - [05-agentic-features-spec.md#agent-architecture](../spec/05-agentic-features-spec.md) - DeepAgents framework

- [x] Configure DeepAgents (no explicit LangGraph graph):
  - [x] Create DeepAgent with tools, system prompt, and checkpointer
  - [x] Use agent-level streaming events for tool/text routing
  - [x] Keep HITL enforcement in tool layer (no graph routing)

### WebSocket Chat Endpoint

> **Spec References:**
> - [03-backend-spec.md#websocket-chat](../spec/03-backend-spec.md) - WebSocket specification
> - [05-agentic-features-spec.md#tool-output-handling](../spec/05-agentic-features-spec.md) - Response formatting

- [x] Create `backend/api/routes/chat.py` — *See [03-backend-spec.md#websocket-chat](../spec/03-backend-spec.md)*:
  - [x] Implement `WebSocket /ws/chat` endpoint:
    - [x] Accept WebSocket connection
    - [x] Validate user authentication
    - [x] Initialize or resume conversation thread
    - [x] Handle incoming messages
  - [x] Implement message handling:
    - [x] Parse incoming AI SDK format messages
    - [x] Invoke agent with message
    - [x] Stream response back to client
  - [x] Implement AI SDK streaming format — *See [04-frontend-spec.md#ai-sdk-protocol](../spec/04-frontend-spec.md)*:
    - [x] Text chunks: `0:{content}\n`
    - [x] Tool calls: `9:{tool_call}\n`
    - [x] Tool results: `a:{tool_result}\n`
    - [x] Finish: `d:{finish_reason}\n`
  - [x] Implement reasoning block filtering — *See [05-agentic-features-spec.md#tool-output-handling](../spec/05-agentic-features-spec.md)*:
    - [x] Check content block type
    - [x] Filter out "reasoning" blocks — *See [07-integration-spec.md#filtering-thinking-output](../spec/07-integration-spec.md)*
    - [x] Only stream "text" blocks to frontend

- [x] Create `backend/api/routes/chat_rest.py`:
  - [x] Implement `POST /api/chat` endpoint (REST fallback) — *See [03-backend-spec.md#chat-endpoint](../spec/03-backend-spec.md)*:
    - [x] Accept message in request body
    - [x] Return streamed response with SSE
    - [x] Support same AI SDK format

### Streaming Response Handler

> **Spec References:**
> - [07-integration-spec.md#streaming](../spec/07-integration-spec.md) - Streaming implementation

- [x] Create `backend/agents/streaming.py`:
  - [x] Implement `stream_agent_response()` generator:
    - [x] Accept agent graph and messages
    - [x] Use `astream_events()` with version "v2"
    - [x] Parse event types and route appropriately
    - [x] Format output in AI SDK protocol
  - [x] Handle event types:
    - [x] `on_chat_model_stream`: Text tokens
    - [x] `on_tool_start`: Tool invocation started
    - [x] `on_tool_end`: Tool result received
  - [x] Implement error handling in stream — *See [05-agentic-features-spec.md#error-handling](../spec/05-agentic-features-spec.md)*

---

## Phase 3.2: NGS Data Discovery Tools

> **Spec References:**
> - [05-agentic-features-spec.md#ngs-data-discovery-tools](../spec/05-agentic-features-spec.md) - Tool specifications
> - [06-data-model-spec.md#benchling-data-warehouse](../spec/06-data-model-spec.md) - Available tables

> **Codebase References:**
> - [external-repos/arc-benchling-mcp/](../external-repos/arc-benchling-mcp/) - Benchling tools reference

### Tool Base Infrastructure

- [x] Create `backend/agents/tools/__init__.py`:
  - [x] Export all tool functions
  - [x] Define tool categories

- [x] Create `backend/agents/tools/base.py`:
  - [x] Define common tool utilities
  - [x] Define result formatting helpers
  - [x] Define error handling decorators

### search_ngs_runs Tool

> **Spec References:**
> - [05-agentic-features-spec.md#search_ngs_runs](../spec/05-agentic-features-spec.md) - Complete tool spec

- [x] Create `backend/agents/tools/ngs_discovery.py`:
  - [x] Implement `search_ngs_runs()` function with `@tool` decorator — *See [05-agentic-features-spec.md#search_ngs_runs](../spec/05-agentic-features-spec.md)*:
    - [x] Parameters:
      - [x] `ngs_run` (str, optional): NGS run name (supports wildcards)
      - [x] `pooled_sample` (str, optional): SspArc name (supports wildcards)
      - [x] `submitter` (str, optional): Submitter name
      - [x] `project` (str, optional): Project name
      - [x] `platform` (str, optional): Instrument platform
      - [x] `days_back` (int, optional): Days to look back (default 30)
      - [x] `min_date` (str, optional): Minimum date YYYY-MM-DD
      - [x] `max_date` (str, optional): Maximum date YYYY-MM-DD
      - [x] `status` (str, optional): Run status filter
      - [x] `use_wildcards` (bool, optional): Enable SQL wildcards
      - [x] `include_qc_summary` (bool, optional): Include QC metrics
      - [x] `limit` (int, optional): Max results (default 20)
    - [x] Query Benchling warehouse `ngs_run$raw` table — *See [06-data-model-spec.md#key-tables](../spec/06-data-model-spec.md)*
    - [x] Join with `ngs_pooled_sample$raw` for SspArc info
    - [x] Apply filters based on parameters
    - [x] Format output as TOON table (toon library)
    - [x] Include run name, SspArc, date, sample count, status, platform

### get_ngs_run_samples Tool

> **Spec References:**
> - [05-agentic-features-spec.md#get_ngs_run_samples](../spec/05-agentic-features-spec.md) - Complete tool spec

- [x] Implement `get_ngs_run_samples()` function — *See [05-agentic-features-spec.md#get_ngs_run_samples](../spec/05-agentic-features-spec.md)*:
  - [x] Parameters:
    - [x] `ngs_run` (str, optional): NGS run name
    - [x] `pooled_sample` (str, optional): SspArc name
    - [x] `include_fastq_paths` (bool, optional): Include FASTQ URIs
    - [x] `include_metadata` (bool, optional): Include sample metadata
    - [x] `limit` (int, optional): Max samples (default 100)
  - [x] Query `ngs_run_output_v2$raw` and `library_prep_sample$raw` — *See [06-data-model-spec.md#query-patterns](../spec/06-data-model-spec.md)*
  - [x] Join to get complete sample information
  - [x] Include: sample name, organism, cell line, read counts
  - [x] Optionally include FASTQ paths from GCS
  - [x] Format as TOON table with sample details

### get_ngs_run_qc Tool

> **Spec References:**
> - [05-agentic-features-spec.md#get_ngs_run_qc](../spec/05-agentic-features-spec.md) - Complete tool spec

- [x] Implement `get_ngs_run_qc()` function — *See [05-agentic-features-spec.md#get_ngs_run_qc](../spec/05-agentic-features-spec.md)*:
  - [x] Parameters:
    - [x] `ngs_run` (str, optional): NGS run name
    - [x] `pooled_sample` (str, optional): SspArc name
    - [x] `level` (str, optional): Detail level (summary, lane, sample)
  - [x] Query QC metrics from warehouse
  - [x] Calculate aggregated metrics:
    - [x] Total reads
    - [x] Average Q30 percentage
    - [x] Pass/fail status per sample
  - [x] Format output based on level (TOON for tables):
    - [x] Summary: High-level metrics and status
    - [x] Lane: Per-lane breakdown
    - [x] Sample: Per-sample QC details

### get_fastq_paths Tool

> **Spec References:**
> - [05-agentic-features-spec.md#get_fastq_paths](../spec/05-agentic-features-spec.md) - Complete tool spec

- [x] Implement `get_fastq_paths()` function — *See [05-agentic-features-spec.md#get_fastq_paths](../spec/05-agentic-features-spec.md)*:
  - [x] Parameters:
    - [x] `ngs_run` (str, optional): NGS run name
    - [x] `pooled_sample` (str, optional): SspArc name
    - [x] `sample_names` (str, optional): Specific samples (semicolon-delimited)
    - [x] `verify_exists` (bool, optional): Check if files exist in GCS
  - [x] Query `ngs_run_output_v2$raw` for FASTQ paths
  - [x] Optionally verify file existence in GCS — *See [07-integration-spec.md#file-existence-check](../spec/07-integration-spec.md)*
  - [x] Return TOON-formatted list of samples with R1/R2 paths

### Unit Tests for NGS Tools

- [x] Create `backend/tests/test_ngs_tools.py`:
  - [x] Test search_ngs_runs with various filters
  - [x] Test get_ngs_run_samples with mocked warehouse
  - [x] Test get_ngs_run_qc at different levels
  - [x] Test get_fastq_paths with verification

---

## Phase 3.3: Benchling Discovery & Schema Tools

> **Spec References:**
> - [05-agentic-features-spec.md#benchling-discovery-tools](../spec/05-agentic-features-spec.md) - Entity discovery tools
> - [05-agentic-features-spec.md#schema-metadata-tools](../spec/05-agentic-features-spec.md) - Schema tools

### Entity Discovery Tools

- [x] Create `backend/agents/tools/benchling_discovery.py`:

- [x] Implement `get_entities()` function — *See [05-agentic-features-spec.md#get_entities](../spec/05-agentic-features-spec.md)*:
  - [x] Parameters:
    - [ ] `entity_names` (str, optional): Entity names (semicolon-delimited)
    - [ ] `entity_ids` (str, optional): Entity IDs (semicolon-delimited)
    - [ ] `schema_name` (str, optional): Filter by schema
    - [ ] `project_name` (str, optional): Filter by project
    - [ ] `folder_name` (str, optional): Filter by folder
    - [ ] `created_after` (str, optional): Min creation date
    - [ ] `created_before` (str, optional): Max creation date
    - [ ] `creator_name` (str, optional): Filter by creator
    - [ ] `archived` (bool, optional): Include archived
    - [ ] `fields` (str, optional): Fields to include (semicolon-delimited)
    - [ ] `allow_wildcards` (bool, optional): Enable SQL wildcards
    - [ ] `limit` (int, optional): Max results (default 40)
  - [x] Query appropriate schema table based on schema_name
  - [x] Apply filters dynamically
  - [x] Format output as YAML or table

- [x] Implement `get_entity_relationships()` function — *See [05-agentic-features-spec.md#get_entity_relationships](../spec/05-agentic-features-spec.md)*:
  - [x] Parameters:
    - [ ] `entity_name` (str, required): Entity to start from
    - [ ] `schema_name` (str, optional): Schema hint for performance
    - [ ] `relationship_depth` (int, optional): Traversal depth (default 4, max 10)
    - [ ] `relationship_types` (str, optional): Specific fields to follow
    - [ ] `include_reverse_links` (bool, optional): Include back-references
    - [ ] `output_format` (str, optional): tree, yaml, or json
  - [x] Implement recursive relationship traversal
  - [x] Handle circular references
  - [x] Format output as tree structure

### Notebook Entry Tools

> **Spec References:**
> - [05-agentic-features-spec.md#list_entries](../spec/05-agentic-features-spec.md) - Entry listing
> - [05-agentic-features-spec.md#get_entry_content](../spec/05-agentic-features-spec.md) - Entry content

- [x] Implement `list_entries()` function — *See [05-agentic-features-spec.md#list_entries](../spec/05-agentic-features-spec.md)*:
  - [x] Parameters:
    - [ ] `entry_names` (str, optional): Entry names (semicolon-delimited)
    - [ ] `project_names` (str, optional): Project filter
    - [ ] `folder_names` (str, optional): Folder filter
    - [ ] `creator_names` (str, optional): Creator filter
    - [ ] `min_date` (str, optional): Min date
    - [ ] `max_date` (str, optional): Max date
    - [ ] `allow_wildcards` (bool, optional): Enable wildcards
    - [ ] `archived` (bool, optional): Include archived
  - [x] Query `entry$raw` table — *See [06-data-model-spec.md#key-tables](../spec/06-data-model-spec.md)*
  - [x] Format output as list with metadata

- [x] Implement `get_entry_content()` function — *See [05-agentic-features-spec.md#get_entry_content](../spec/05-agentic-features-spec.md)*:
  - [x] Parameters:
    - [ ] `entry_names` (str, required): Entry names
    - [ ] `head` (int, optional): Lines from beginning
    - [ ] `tail` (int, optional): Lines from end
  - [x] Fetch entry content from warehouse
  - [x] Apply head/tail truncation

- [x] Implement `get_entry_entities()` function — *See [05-agentic-features-spec.md#get_entry_entities](../spec/05-agentic-features-spec.md)*:
  - [x] Parameters:
    - [ ] `entry_name` (str, required): Entry name
    - [ ] `limit` (int, optional): Max entities (default 40)
  - [x] Query entities linked to entry
  - [x] Return formatted list

### Schema & Metadata Tools

> **Spec References:**
> - [05-agentic-features-spec.md#schema-metadata-tools](../spec/05-agentic-features-spec.md) - Schema tools

- [x] Create `backend/agents/tools/schema_tools.py`:

- [x] Implement `get_schemas()` function — *See [05-agentic-features-spec.md#get_schemas](../spec/05-agentic-features-spec.md)*:
  - [x] Parameters:
    - [ ] `schema_names` (str, optional): Specific schemas (semicolon-delimited)
    - [ ] `get_all_schemas` (bool, optional): Return all schema names
  - [x] Query `schema$raw` table
  - [x] Return schema names and descriptions

- [x] Implement `get_schema_field_info()` function — *See [05-agentic-features-spec.md#get_schema_field_info](../spec/05-agentic-features-spec.md)*:
  - [x] Parameters:
    - [ ] `schema_name` (str, required): Schema to inspect
  - [x] Query `schema_field$raw` table
  - [x] Return field names, types, required status, descriptions

- [x] Implement `get_dropdown_values()` function — *See [05-agentic-features-spec.md#get_dropdown_values](../spec/05-agentic-features-spec.md)*:
  - [x] Parameters:
    - [ ] `dropdown_name` (str, required): Dropdown to query
  - [x] Query `dropdown$raw` and `dropdown_option$raw`
  - [x] Return list of valid values

- [x] Implement `list_projects()` function — *See [05-agentic-features-spec.md#list_projects](../spec/05-agentic-features-spec.md)*:
  - [x] Parameters:
    - [ ] `wildcard_pattern` (str, optional): Filter pattern
  - [x] Query `project$raw` table
  - [x] Return project names and metadata

### Advanced Query Tool

> **Spec References:**
> - [05-agentic-features-spec.md#execute_warehouse_query](../spec/05-agentic-features-spec.md) - Advanced SQL access
> - [08-security-spec.md#sql-injection-prevention](../spec/08-security-spec.md) - Query safety

- [x] Implement `execute_warehouse_query()` function — *See [05-agentic-features-spec.md#execute_warehouse_query](../spec/05-agentic-features-spec.md)*:
  - [x] Parameters:
    - [ ] `sql` (str, required): SQL query (SELECT only)
    - [ ] `params` (dict, optional): Query parameters
    - [ ] `limit` (int, optional): Max rows (default 100, max 1000)
  - [x] Validate query is SELECT only — *See [08-security-spec.md#sql-injection-prevention](../spec/08-security-spec.md)*
  - [x] Enforce limit clause
  - [x] Execute with parameterized query
  - [x] Format results as table
  - [x] Include row count in output

---

## Phase 3.4: Pipeline & File Generation Tools

> **Spec References:**
> - [05-agentic-features-spec.md#pipeline-info-tools](../spec/05-agentic-features-spec.md) - Pipeline tools
> - [05-agentic-features-spec.md#file-generation-tools](../spec/05-agentic-features-spec.md) - File generation

### Pipeline Info Tools

- [ ] Create `backend/agents/tools/pipeline_tools.py`:

- [ ] Implement `list_pipelines()` function — *See [05-agentic-features-spec.md#list_pipelines](../spec/05-agentic-features-spec.md)*:
  - [ ] Parameters:
    - [ ] `category` (str, optional): Filter by category
  - [ ] Query pipeline registry
  - [ ] Return formatted table with:
    - [ ] Pipeline name
    - [ ] Version
    - [ ] Description
    - [ ] Category

- [ ] Implement `get_pipeline_schema()` function — *See [05-agentic-features-spec.md#get_pipeline_schema](../spec/05-agentic-features-spec.md)*:
  - [ ] Parameters:
    - [ ] `pipeline` (str, required): Pipeline name
    - [ ] `version` (str, optional): Specific version
  - [ ] Fetch from pipeline registry — *See [03-backend-spec.md#pipelineregistry](../spec/03-backend-spec.md)*
  - [ ] Return formatted output with:
    - [ ] Required parameters with descriptions
    - [ ] Optional parameters with defaults
    - [ ] Samplesheet column definitions
    - [ ] Valid values for enum params (genome, protocol, aligner)

### File Generation Tools

> **Spec References:**
> - [05-agentic-features-spec.md#generate_samplesheet](../spec/05-agentic-features-spec.md) - Samplesheet generation
> - [05-agentic-features-spec.md#generate_config](../spec/05-agentic-features-spec.md) - Config generation

- [ ] Create `backend/agents/tools/file_generation.py`:

- [ ] Implement `generate_samplesheet()` function — *See [05-agentic-features-spec.md#generate_samplesheet](../spec/05-agentic-features-spec.md)*:
  - [ ] Parameters:
    - [ ] `ngs_run` (str, optional): NGS run name
    - [ ] `pooled_sample` (str, optional): SspArc name
    - [ ] `sample_ids` (str, optional): Specific samples (semicolon-delimited)
    - [ ] `pipeline` (str, required): Target pipeline
    - [ ] `expected_cells` (int, optional): Expected cells per sample
  - [ ] Fetch sample data using NGS tools
  - [ ] Get samplesheet schema for pipeline — *See [03-backend-spec.md#pipelineregistry](../spec/03-backend-spec.md)*
  - [ ] Build CSV with required columns:
    - [ ] sample
    - [ ] fastq_1
    - [ ] fastq_2
    - [ ] expected_cells (for scrnaseq)
  - [ ] Validate FASTQ paths exist — *See [07-integration-spec.md#file-existence-check](../spec/07-integration-spec.md)*
  - [ ] Store in agent state `generated_files`
  - [ ] Return summary with sample count

- [ ] Implement `generate_config()` function — *See [05-agentic-features-spec.md#generate_config](../spec/05-agentic-features-spec.md)*:
  - [ ] Parameters:
    - [ ] `pipeline` (str, required): Pipeline name
    - [ ] `params` (dict, optional): Pipeline parameters
    - [ ] `profile` (str, optional): Execution profile (default "gcp_batch")
  - [ ] Get pipeline schema
  - [ ] Render Nextflow config template:
    - [ ] params block with user values
    - [ ] process block with GCP Batch settings
    - [ ] google block with project/region/service account
  - [ ] Store in agent state `generated_files`
  - [ ] Return config summary

### Validation Tool

> **Spec References:**
> - [05-agentic-features-spec.md#validate_inputs](../spec/05-agentic-features-spec.md) - Validation tool

- [ ] Implement `validate_inputs()` function — *See [05-agentic-features-spec.md#validate_inputs](../spec/05-agentic-features-spec.md)*:
  - [ ] Parameters:
    - [ ] `samplesheet_csv` (str, required): CSV content
    - [ ] `config_content` (str, required): Config content
    - [ ] `pipeline` (str, required): Pipeline name
  - [ ] Validate samplesheet — *See [06-data-model-spec.md#data-integrity](../spec/06-data-model-spec.md)*:
    - [ ] Check required columns present
    - [ ] Validate required fields not empty
    - [ ] Validate FASTQ path format
    - [ ] Check FASTQ files exist in GCS
  - [ ] Validate config:
    - [ ] Parse Nextflow config format
    - [ ] Check required params present
    - [ ] Validate param values against schema
  - [ ] Return validation result:
    - [ ] `valid`: boolean
    - [ ] `errors`: list of error objects
    - [ ] `warnings`: list of warning strings
    - [ ] `summary`: sample count, files verified, estimated runtime

---

## Phase 3.5: Submission Tools & HITL Middleware

> **Spec References:**
> - [05-agentic-features-spec.md#human-in-the-loop](../spec/05-agentic-features-spec.md) - HITL requirements
> - [05-agentic-features-spec.md#validation-submission-tools](../spec/05-agentic-features-spec.md) - Submission tools
> - [08-security-spec.md#tool-execution-safety](../spec/08-security-spec.md) - Execution safety

### Human-in-the-Loop Middleware

> **Spec References:**
> - [05-agentic-features-spec.md#human-in-the-loop](../spec/05-agentic-features-spec.md) - HITL implementation

- [ ] Create `backend/agents/middleware/hitl.py` — *See [05-agentic-features-spec.md#human-in-the-loop](../spec/05-agentic-features-spec.md)*:
  - [ ] Implement `HumanInTheLoopMiddleware`:
    - [ ] Define list of HITL-required tools — *See [05-agentic-features-spec.md#hitl-required-tools](../spec/05-agentic-features-spec.md)*:
      - [ ] `submit_run`
      - [ ] `cancel_run`
      - [ ] `delete_file`
      - [ ] `clear_samplesheet`
    - [ ] Intercept tool calls before execution
    - [ ] Check if tool requires approval
    - [ ] Pause execution and request user confirmation
    - [ ] Resume or cancel based on user response
  - [ ] Define approval message format:
    - [ ] Tool name
    - [ ] Parameters summary
    - [ ] Expected impact
    - [ ] Approve/Reject options

### Submission Tools

> **Spec References:**
> - [05-agentic-features-spec.md#submit_run](../spec/05-agentic-features-spec.md) - Submit tool
> - [05-agentic-features-spec.md#cancel_run](../spec/05-agentic-features-spec.md) - Cancel tool

- [ ] Create `backend/agents/tools/submission.py`:

- [ ] Implement `submit_run()` function (HITL required) — *See [05-agentic-features-spec.md#submit_run](../spec/05-agentic-features-spec.md)*:
  - [ ] Parameters:
    - [ ] `samplesheet_csv` (str, required): Validated CSV
    - [ ] `config_content` (str, required): Validated config
    - [ ] `pipeline` (str, required): Pipeline name
    - [ ] `pipeline_version` (str, required): Pipeline version
  - [ ] Upload files to GCS — *See [06-data-model-spec.md#bucket-structure](../spec/06-data-model-spec.md)*:
    - [ ] `inputs/samplesheet.csv`
    - [ ] `inputs/nextflow.config`
    - [ ] `inputs/params.yaml`
  - [ ] Create run record in database
  - [ ] Submit GCP Batch job (via BatchService) — *See [07-integration-spec.md#job-submission](../spec/07-integration-spec.md)*
  - [ ] Update run status to "submitted"
  - [ ] Return run information:
    - [ ] run_id
    - [ ] status
    - [ ] gcs_path
    - [ ] estimated_runtime

- [ ] Implement `cancel_run()` function (HITL required) — *See [05-agentic-features-spec.md#cancel_run](../spec/05-agentic-features-spec.md)*:
  - [ ] Parameters:
    - [ ] `run_id` (str, required): Run identifier
  - [ ] Verify run exists and is cancellable
  - [ ] Cancel GCP Batch job — *See [07-integration-spec.md#job-cancellation](../spec/07-integration-spec.md)*
  - [ ] Update run status to "cancelled"
  - [ ] Return confirmation

- [ ] Implement `delete_file()` function (HITL required) — *See [05-agentic-features-spec.md#delete_file](../spec/05-agentic-features-spec.md)*:
  - [ ] Parameters:
    - [ ] `run_id` (str, required): Run identifier
    - [ ] `file_path` (str, required): Relative file path
  - [ ] Verify run ownership — *See [08-security-spec.md#resource-level-access](../spec/08-security-spec.md)*
  - [ ] Delete file from GCS
  - [ ] Return confirmation

- [ ] Implement `clear_samplesheet()` function (HITL required) — *See [05-agentic-features-spec.md#clear_samplesheet](../spec/05-agentic-features-spec.md)*:
  - [ ] Parameters:
    - [ ] `confirm` (bool, required): Must be True
  - [ ] Clear samplesheet from agent state
  - [ ] Return confirmation

### Subagents

> **Spec References:**
> - [05-agentic-features-spec.md#subagents](../spec/05-agentic-features-spec.md) - Subagent specifications

- [ ] Create `backend/agents/subagents/__init__.py`:
  - [ ] Export subagent configurations

- [ ] Create `backend/agents/subagents/benchling_expert.py` — *See [05-agentic-features-spec.md#benchling_expert](../spec/05-agentic-features-spec.md)*:
  - [ ] Define `benchling_expert` configuration:
    - [ ] Name: "benchling_expert"
    - [ ] Description: Complex Benchling queries and lineage traversal
    - [ ] Model: Same as main agent
    - [ ] Tools:
      - [ ] search_ngs_runs
      - [ ] get_ngs_run_samples
      - [ ] get_entities
      - [ ] get_entity_relationships
      - [ ] list_entries
      - [ ] get_entry_entities
      - [ ] execute_warehouse_query
    - [ ] Custom system prompt for Benchling expertise:
      - [ ] NGS workflow knowledge
      - [ ] Schema relationship understanding
      - [ ] Data quality handling

- [ ] Create `backend/agents/subagents/config_expert.py` — *See [05-agentic-features-spec.md#config_expert](../spec/05-agentic-features-spec.md)*:
  - [ ] Define `config_expert` configuration:
    - [ ] Name: "config_expert"
    - [ ] Description: Pipeline configuration assistance
    - [ ] Model: Same as main agent
    - [ ] Tools:
      - [ ] list_pipelines
      - [ ] get_pipeline_schema
      - [ ] get_dropdown_values
    - [ ] Custom system prompt for config expertise:
      - [ ] nf-core pipeline knowledge
      - [ ] Parameter trade-offs
      - [ ] Resource estimation

### Middleware Stack

> **Spec References:**
> - [05-agentic-features-spec.md#middleware-stack](../spec/05-agentic-features-spec.md) - Middleware components

- [ ] Create `backend/agents/middleware/todo.py` — *See [05-agentic-features-spec.md#todolistmiddleware](../spec/05-agentic-features-spec.md)*:
  - [ ] Implement `TodoListMiddleware`:
    - [ ] Track agent's planned actions
    - [ ] Log completed steps
    - [ ] Provide context for next steps

- [ ] Create `backend/agents/middleware/filesystem.py` — *See [05-agentic-features-spec.md#filesystemmiddleware](../spec/05-agentic-features-spec.md)*:
  - [ ] Implement `FilesystemMiddleware`:
    - [ ] Offload large tool results (>20k tokens)
    - [ ] Store in agent state or temporary file
    - [ ] Replace with reference in message

- [ ] Create `backend/agents/middleware/summarization.py` — *See [05-agentic-features-spec.md#summarizationmiddleware](../spec/05-agentic-features-spec.md)*:
  - [ ] Implement `SummarizationMiddleware`:
    - [ ] Monitor context window usage
    - [ ] Trigger summarization at 85% capacity
    - [ ] Summarize older messages
    - [ ] Replace with summary token

### Tool Registration

- [ ] Update `backend/agents/pipeline_agent.py`:
  - [ ] Register all tools — *See [05-agentic-features-spec.md#tool-suite](../spec/05-agentic-features-spec.md)*:
    - [ ] NGS discovery tools
    - [ ] Benchling discovery tools
    - [ ] Schema tools
    - [ ] Pipeline tools
    - [ ] File generation tools
    - [ ] Submission tools (with HITL)
  - [ ] Register subagents:
    - [ ] benchling_expert
    - [ ] config_expert
  - [ ] Apply middleware stack:
    - [ ] TodoListMiddleware
    - [ ] FilesystemMiddleware
    - [ ] SummarizationMiddleware
    - [ ] HumanInTheLoopMiddleware

---

## Key Deliverables Checklist

- [ ] LangChain/DeepAgents framework configured
- [ ] Gemini 3 Flash model integration with thinking levels
- [ ] System prompt defining agent capabilities
- [ ] AsyncPostgresSaver for conversation state
- [ ] WebSocket chat endpoint with AI SDK streaming format
- [ ] Reasoning block filtering (hidden from users)
- [ ] NGS data discovery tools:
  - [ ] search_ngs_runs
  - [ ] get_ngs_run_samples
  - [ ] get_ngs_run_qc
  - [ ] get_fastq_paths
- [ ] Benchling discovery tools:
  - [ ] get_entities
  - [ ] get_entity_relationships
  - [ ] list_entries
  - [ ] get_entry_content
  - [ ] get_entry_entities
- [ ] Schema tools:
  - [ ] get_schemas
  - [ ] get_schema_field_info
  - [ ] get_dropdown_values
  - [ ] list_projects
- [ ] Pipeline tools:
  - [ ] list_pipelines
  - [ ] get_pipeline_schema
- [ ] File generation tools:
  - [ ] generate_samplesheet
  - [ ] generate_config
  - [ ] validate_inputs
- [ ] HITL-protected submission tools:
  - [ ] submit_run
  - [ ] cancel_run
  - [ ] delete_file
  - [ ] clear_samplesheet
- [ ] Subagents:
  - [ ] benchling_expert
  - [ ] config_expert
- [ ] Middleware stack:
  - [ ] TodoListMiddleware
  - [ ] FilesystemMiddleware
  - [ ] SummarizationMiddleware
  - [ ] HumanInTheLoopMiddleware
- [ ] execute_warehouse_query for advanced SQL
- [ ] Unit tests for all tools
- [ ] Integration tests for agent workflows
