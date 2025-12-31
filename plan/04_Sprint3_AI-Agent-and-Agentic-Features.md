# Sprint 3: AI Agent & Agentic Features

## Overview

This sprint implements the core AI agent with LangChain/DeepAgents, including all Benchling discovery tools, file generation tools, conversation management, and Human-in-the-Loop approval workflows.

## References

- [05-agentic-features-spec.md](../SPEC/05-agentic-features-spec.md) - Agent architecture and tools
- [07-integration-spec.md](../SPEC/07-integration-spec.md) - Gemini API integration
- [11-conf-spec.md](../SPEC/11-conf-spec.md) - AI model configuration

---

## Phase 3.1: Agent Foundation

### LangChain/DeepAgents Setup

- [ ] Create `backend/agents/__init__.py`:
  - [ ] Initialize agent module
  - [ ] Export main agent classes

- [ ] Create `backend/agents/pipeline_agent.py`:
  - [ ] Import LangChain DeepAgents framework
  - [ ] Create `PipelineAgent` class
  - [ ] Configure agent with tools and subagents

### Gemini Model Configuration

- [ ] Create `backend/agents/model.py`:
  - [ ] Implement `get_chat_model()` function:
    - [ ] Use `init_chat_model()` from langchain
    - [ ] Model: `google_genai:gemini-3-flash-preview`
    - [ ] Temperature: 1.0 (required for thinking)
    - [ ] Max output tokens: 8192
    - [ ] Thinking level from settings (default "low")
  - [ ] Support Vertex AI backend option:
    - [ ] Check for `GOOGLE_CLOUD_PROJECT` env var
    - [ ] Set `vertexai=True` if using Vertex AI
  - [ ] Implement streaming configuration

### System Prompt

- [ ] Create `backend/agents/prompts.py`:
  - [ ] Define `PIPELINE_AGENT_SYSTEM_PROMPT`:
    - [ ] Role description (Arc Reactor AI assistant)
    - [ ] Capabilities overview:
      - [ ] Discover NGS samples from Benchling
      - [ ] Generate pipeline configurations
      - [ ] Validate and submit runs
      - [ ] Provide guidance and troubleshooting
    - [ ] Workflow guidance:
      - [ ] Start by understanding user's data
      - [ ] Discover samples via NGS tools
      - [ ] Generate samplesheet and config
      - [ ] Validate before submission
      - [ ] Explain errors and suggest fixes
    - [ ] Important notes:
      - [ ] SspArc refers to NGS Pooled Sample name
      - [ ] Always verify data before generation
      - [ ] Human approval required for submissions
    - [ ] Schema knowledge:
      - [ ] NGS workflow: samples → library prep → pooling → sequencing
      - [ ] Key entities and relationships

### Conversation State Management

- [ ] Create `backend/agents/checkpointer.py`:
  - [ ] Implement AsyncPostgresSaver for LangGraph:
    - [ ] Use existing Cloud SQL connection
    - [ ] Store checkpoints in `checkpoints` table
  - [ ] Configure checkpoint serialization
  - [ ] Implement thread cleanup for old conversations

### Agent Graph Structure

- [ ] Create `backend/agents/graph.py`:
  - [ ] Define agent state schema:
    - [ ] `messages`: List of conversation messages
    - [ ] `current_ngs_run`: Active NGS run being configured
    - [ ] `current_samples`: Samples from recent queries
    - [ ] `generated_files`: Dict of filename -> content
    - [ ] `validation_result`: Latest validation output
  - [ ] Define agent nodes:
    - [ ] `agent`: Main reasoning node
    - [ ] `tools`: Tool execution node
    - [ ] `human_approval`: HITL approval node
  - [ ] Define conditional edges:
    - [ ] Route to tools when tool calls present
    - [ ] Route to human_approval for HITL tools
    - [ ] Route to END on completion
  - [ ] Compile graph with checkpointer

### WebSocket Chat Endpoint

- [ ] Create `backend/api/routes/chat.py`:
  - [ ] Implement `WebSocket /ws/chat` endpoint:
    - [ ] Accept WebSocket connection
    - [ ] Validate user authentication
    - [ ] Initialize or resume conversation thread
    - [ ] Handle incoming messages
  - [ ] Implement message handling:
    - [ ] Parse incoming AI SDK format messages
    - [ ] Invoke agent with message
    - [ ] Stream response back to client
  - [ ] Implement AI SDK streaming format:
    - [ ] Text chunks: `0:{content}\n`
    - [ ] Tool calls: `9:{tool_call}\n`
    - [ ] Tool results: `a:{tool_result}\n`
    - [ ] Finish: `d:{finish_reason}\n`
  - [ ] Implement reasoning block filtering:
    - [ ] Check content block type
    - [ ] Filter out "reasoning" blocks
    - [ ] Only stream "text" blocks to frontend

- [ ] Create `backend/api/routes/chat_rest.py`:
  - [ ] Implement `POST /api/chat` endpoint (REST fallback):
    - [ ] Accept message in request body
    - [ ] Return streamed response with SSE
    - [ ] Support same AI SDK format

### Streaming Response Handler

- [ ] Create `backend/agents/streaming.py`:
  - [ ] Implement `stream_agent_response()` generator:
    - [ ] Accept agent graph and messages
    - [ ] Use `astream_events()` with version "v2"
    - [ ] Parse event types and route appropriately
    - [ ] Format output in AI SDK protocol
  - [ ] Handle event types:
    - [ ] `on_chat_model_stream`: Text tokens
    - [ ] `on_tool_start`: Tool invocation started
    - [ ] `on_tool_end`: Tool result received
  - [ ] Implement error handling in stream

---

## Phase 3.2: NGS Data Discovery Tools

### Tool Base Infrastructure

- [ ] Create `backend/agents/tools/__init__.py`:
  - [ ] Export all tool functions
  - [ ] Define tool categories

- [ ] Create `backend/agents/tools/base.py`:
  - [ ] Define common tool utilities
  - [ ] Define result formatting helpers
  - [ ] Define error handling decorators

### search_ngs_runs Tool

- [ ] Create `backend/agents/tools/ngs_discovery.py`:
  - [ ] Implement `search_ngs_runs()` function with `@tool` decorator:
    - [ ] Parameters:
      - [ ] `ngs_run` (str, optional): NGS run name (supports wildcards)
      - [ ] `pooled_sample` (str, optional): SspArc name (supports wildcards)
      - [ ] `submitter` (str, optional): Submitter name
      - [ ] `project` (str, optional): Project name
      - [ ] `platform` (str, optional): Instrument platform
      - [ ] `days_back` (int, optional): Days to look back (default 30)
      - [ ] `min_date` (str, optional): Minimum date YYYY-MM-DD
      - [ ] `max_date` (str, optional): Maximum date YYYY-MM-DD
      - [ ] `status` (str, optional): Run status filter
      - [ ] `use_wildcards` (bool, optional): Enable SQL wildcards
      - [ ] `include_qc_summary` (bool, optional): Include QC metrics
      - [ ] `limit` (int, optional): Max results (default 20)
    - [ ] Query Benchling warehouse `ngs_run$raw` table
    - [ ] Join with `ngs_pooled_sample$raw` for SspArc info
    - [ ] Apply filters based on parameters
    - [ ] Format output as readable table
    - [ ] Include run name, SspArc, date, sample count, status, platform

### get_ngs_run_samples Tool

- [ ] Implement `get_ngs_run_samples()` function:
  - [ ] Parameters:
    - [ ] `ngs_run` (str, optional): NGS run name
    - [ ] `pooled_sample` (str, optional): SspArc name
    - [ ] `include_fastq_paths` (bool, optional): Include FASTQ URIs
    - [ ] `include_metadata` (bool, optional): Include sample metadata
    - [ ] `limit` (int, optional): Max samples (default 100)
  - [ ] Query `ngs_run_output_v2$raw` and `library_prep_sample$raw`
  - [ ] Join to get complete sample information
  - [ ] Include: sample name, organism, cell line, read counts
  - [ ] Optionally include FASTQ paths from GCS
  - [ ] Format as table with sample details

### get_ngs_run_qc Tool

- [ ] Implement `get_ngs_run_qc()` function:
  - [ ] Parameters:
    - [ ] `ngs_run` (str, optional): NGS run name
    - [ ] `pooled_sample` (str, optional): SspArc name
    - [ ] `level` (str, optional): Detail level (summary, lane, sample)
  - [ ] Query QC metrics from warehouse
  - [ ] Calculate aggregated metrics:
    - [ ] Total reads
    - [ ] Average Q30 percentage
    - [ ] Pass/fail status per sample
  - [ ] Format output based on level:
    - [ ] Summary: High-level metrics and status
    - [ ] Lane: Per-lane breakdown
    - [ ] Sample: Per-sample QC details

### get_fastq_paths Tool

- [ ] Implement `get_fastq_paths()` function:
  - [ ] Parameters:
    - [ ] `ngs_run` (str, optional): NGS run name
    - [ ] `pooled_sample` (str, optional): SspArc name
    - [ ] `sample_names` (str, optional): Specific samples (semicolon-delimited)
    - [ ] `verify_exists` (bool, optional): Check if files exist in GCS
  - [ ] Query `ngs_run_output_v2$raw` for FASTQ paths
  - [ ] Optionally verify file existence in GCS
  - [ ] Return formatted list of samples with R1/R2 paths

### Unit Tests for NGS Tools

- [ ] Create `backend/tests/test_ngs_tools.py`:
  - [ ] Test search_ngs_runs with various filters
  - [ ] Test get_ngs_run_samples with mocked warehouse
  - [ ] Test get_ngs_run_qc at different levels
  - [ ] Test get_fastq_paths with verification

---

## Phase 3.3: Benchling Discovery & Schema Tools

### Entity Discovery Tools

- [ ] Create `backend/agents/tools/benchling_discovery.py`:

- [ ] Implement `get_entities()` function:
  - [ ] Parameters:
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
  - [ ] Query appropriate schema table based on schema_name
  - [ ] Apply filters dynamically
  - [ ] Format output as YAML or table

- [ ] Implement `get_entity_relationships()` function:
  - [ ] Parameters:
    - [ ] `entity_name` (str, required): Entity to start from
    - [ ] `schema_name` (str, optional): Schema hint for performance
    - [ ] `relationship_depth` (int, optional): Traversal depth (default 4, max 10)
    - [ ] `relationship_types` (str, optional): Specific fields to follow
    - [ ] `include_reverse_links` (bool, optional): Include back-references
    - [ ] `output_format` (str, optional): tree, yaml, or json
  - [ ] Implement recursive relationship traversal
  - [ ] Handle circular references
  - [ ] Format output as tree structure

### Notebook Entry Tools

- [ ] Implement `list_entries()` function:
  - [ ] Parameters:
    - [ ] `entry_names` (str, optional): Entry names (semicolon-delimited)
    - [ ] `project_names` (str, optional): Project filter
    - [ ] `folder_names` (str, optional): Folder filter
    - [ ] `creator_names` (str, optional): Creator filter
    - [ ] `min_date` (str, optional): Min date
    - [ ] `max_date` (str, optional): Max date
    - [ ] `allow_wildcards` (bool, optional): Enable wildcards
    - [ ] `archived` (bool, optional): Include archived
  - [ ] Query `entry$raw` table
  - [ ] Format output as list with metadata

- [ ] Implement `get_entry_content()` function:
  - [ ] Parameters:
    - [ ] `entry_names` (str, required): Entry names
    - [ ] `head` (int, optional): Lines from beginning
    - [ ] `tail` (int, optional): Lines from end
  - [ ] Fetch entry content from warehouse
  - [ ] Apply head/tail truncation

- [ ] Implement `get_entry_entities()` function:
  - [ ] Parameters:
    - [ ] `entry_name` (str, required): Entry name
    - [ ] `limit` (int, optional): Max entities (default 40)
  - [ ] Query entities linked to entry
  - [ ] Return formatted list

### Schema & Metadata Tools

- [ ] Create `backend/agents/tools/schema_tools.py`:

- [ ] Implement `get_schemas()` function:
  - [ ] Parameters:
    - [ ] `schema_names` (str, optional): Specific schemas (semicolon-delimited)
    - [ ] `get_all_schemas` (bool, optional): Return all schema names
  - [ ] Query `schema$raw` table
  - [ ] Return schema names and descriptions

- [ ] Implement `get_schema_field_info()` function:
  - [ ] Parameters:
    - [ ] `schema_name` (str, required): Schema to inspect
  - [ ] Query `schema_field$raw` table
  - [ ] Return field names, types, required status, descriptions

- [ ] Implement `get_dropdown_values()` function:
  - [ ] Parameters:
    - [ ] `dropdown_name` (str, required): Dropdown to query
  - [ ] Query `dropdown$raw` and `dropdown_option$raw`
  - [ ] Return list of valid values

- [ ] Implement `list_projects()` function:
  - [ ] Parameters:
    - [ ] `wildcard_pattern` (str, optional): Filter pattern
  - [ ] Query `project$raw` table
  - [ ] Return project names and metadata

### Advanced Query Tool

- [ ] Implement `execute_warehouse_query()` function:
  - [ ] Parameters:
    - [ ] `sql` (str, required): SQL query (SELECT only)
    - [ ] `params` (dict, optional): Query parameters
    - [ ] `limit` (int, optional): Max rows (default 100, max 1000)
  - [ ] Validate query is SELECT only
  - [ ] Enforce limit clause
  - [ ] Execute with parameterized query
  - [ ] Format results as table
  - [ ] Include row count in output

---

## Phase 3.4: Pipeline & File Generation Tools

### Pipeline Info Tools

- [ ] Create `backend/agents/tools/pipeline_tools.py`:

- [ ] Implement `list_pipelines()` function:
  - [ ] Parameters:
    - [ ] `category` (str, optional): Filter by category
  - [ ] Query pipeline registry
  - [ ] Return formatted table with:
    - [ ] Pipeline name
    - [ ] Version
    - [ ] Description
    - [ ] Category

- [ ] Implement `get_pipeline_schema()` function:
  - [ ] Parameters:
    - [ ] `pipeline` (str, required): Pipeline name
    - [ ] `version` (str, optional): Specific version
  - [ ] Fetch from pipeline registry
  - [ ] Return formatted output with:
    - [ ] Required parameters with descriptions
    - [ ] Optional parameters with defaults
    - [ ] Samplesheet column definitions
    - [ ] Valid values for enum params (genome, protocol, aligner)

### File Generation Tools

- [ ] Create `backend/agents/tools/file_generation.py`:

- [ ] Implement `generate_samplesheet()` function:
  - [ ] Parameters:
    - [ ] `ngs_run` (str, optional): NGS run name
    - [ ] `pooled_sample` (str, optional): SspArc name
    - [ ] `sample_ids` (str, optional): Specific samples (semicolon-delimited)
    - [ ] `pipeline` (str, required): Target pipeline
    - [ ] `expected_cells` (int, optional): Expected cells per sample
  - [ ] Fetch sample data using NGS tools
  - [ ] Get samplesheet schema for pipeline
  - [ ] Build CSV with required columns:
    - [ ] sample
    - [ ] fastq_1
    - [ ] fastq_2
    - [ ] expected_cells (for scrnaseq)
  - [ ] Validate FASTQ paths exist
  - [ ] Store in agent state `generated_files`
  - [ ] Return summary with sample count

- [ ] Implement `generate_config()` function:
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

- [ ] Implement `validate_inputs()` function:
  - [ ] Parameters:
    - [ ] `samplesheet_csv` (str, required): CSV content
    - [ ] `config_content` (str, required): Config content
    - [ ] `pipeline` (str, required): Pipeline name
  - [ ] Validate samplesheet:
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

### Human-in-the-Loop Middleware

- [ ] Create `backend/agents/middleware/hitl.py`:
  - [ ] Implement `HumanInTheLoopMiddleware`:
    - [ ] Define list of HITL-required tools:
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

- [ ] Create `backend/agents/tools/submission.py`:

- [ ] Implement `submit_run()` function (HITL required):
  - [ ] Parameters:
    - [ ] `samplesheet_csv` (str, required): Validated CSV
    - [ ] `config_content` (str, required): Validated config
    - [ ] `pipeline` (str, required): Pipeline name
    - [ ] `pipeline_version` (str, required): Pipeline version
  - [ ] Upload files to GCS:
    - [ ] `inputs/samplesheet.csv`
    - [ ] `inputs/nextflow.config`
    - [ ] `inputs/params.yaml`
  - [ ] Create run record in database
  - [ ] Submit GCP Batch job (via BatchService)
  - [ ] Update run status to "submitted"
  - [ ] Return run information:
    - [ ] run_id
    - [ ] status
    - [ ] gcs_path
    - [ ] estimated_runtime

- [ ] Implement `cancel_run()` function (HITL required):
  - [ ] Parameters:
    - [ ] `run_id` (str, required): Run identifier
  - [ ] Verify run exists and is cancellable
  - [ ] Cancel GCP Batch job
  - [ ] Update run status to "cancelled"
  - [ ] Return confirmation

- [ ] Implement `delete_file()` function (HITL required):
  - [ ] Parameters:
    - [ ] `run_id` (str, required): Run identifier
    - [ ] `file_path` (str, required): Relative file path
  - [ ] Verify run ownership
  - [ ] Delete file from GCS
  - [ ] Return confirmation

- [ ] Implement `clear_samplesheet()` function (HITL required):
  - [ ] Parameters:
    - [ ] `confirm` (bool, required): Must be True
  - [ ] Clear samplesheet from agent state
  - [ ] Return confirmation

### Subagents

- [ ] Create `backend/agents/subagents/__init__.py`:
  - [ ] Export subagent configurations

- [ ] Create `backend/agents/subagents/benchling_expert.py`:
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

- [ ] Create `backend/agents/subagents/config_expert.py`:
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

- [ ] Create `backend/agents/middleware/todo.py`:
  - [ ] Implement `TodoListMiddleware`:
    - [ ] Track agent's planned actions
    - [ ] Log completed steps
    - [ ] Provide context for next steps

- [ ] Create `backend/agents/middleware/filesystem.py`:
  - [ ] Implement `FilesystemMiddleware`:
    - [ ] Offload large tool results (>20k tokens)
    - [ ] Store in agent state or temporary file
    - [ ] Replace with reference in message

- [ ] Create `backend/agents/middleware/summarization.py`:
  - [ ] Implement `SummarizationMiddleware`:
    - [ ] Monitor context window usage
    - [ ] Trigger summarization at 85% capacity
    - [ ] Summarize older messages
    - [ ] Replace with summary token

### Tool Registration

- [ ] Update `backend/agents/pipeline_agent.py`:
  - [ ] Register all tools:
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
