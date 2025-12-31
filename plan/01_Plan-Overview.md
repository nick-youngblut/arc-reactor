# Arc Reactor - Implementation Plan Overview

## Executive Summary

This document provides a high-level implementation plan for the Arc Reactor application, a web platform enabling wet lab scientists at Arc Institute to run Nextflow bioinformatics pipelines on Google Cloud Platform through an AI-powered conversational interface.

The implementation is organized into **6 major sprints**, each containing **2-5 phases**. Each sprint builds upon the previous, progressing from foundational infrastructure through core features to advanced capabilities and polish.

---

## Sprint 1: Foundation & Infrastructure Setup

**Goal:** Establish the foundational infrastructure, project scaffolding, CI/CD pipelines, and core service integrations required for development.

**Estimated Duration:** 3-4 phases

### Phase 1.1: Project Scaffolding & Development Environment
- Initialize monorepo structure (`backend/`, `frontend/`)
- Set up FastAPI backend with Dynaconf configuration per [03-backend-spec.md](../SPEC/03-backend-spec.md)
- Set up Next.js 14 frontend with App Router and static export configuration per [04-frontend-spec.md](../SPEC/04-frontend-spec.md)
- Configure development tooling (Black, Ruff, ESLint, Prettier)
- Create Docker development environment
- Establish `GEMINI.md` repository guidelines

### Phase 1.2: GCP Infrastructure & CI/CD
- Set up GCP project resources (Cloud Run, Cloud SQL, GCS buckets, Secret Manager)
- Configure service accounts and IAM permissions per [08-security-spec.md](../SPEC/08-security-spec.md)
- Implement GitHub Actions CI/CD pipeline per [09-deployment-spec.md](../SPEC/09-deployment-spec.md)
- Set up dev and prod environments with Terraform
- Configure Cloud SQL PostgreSQL instances
- Enable GCP IAP authentication

### Phase 1.3: Core Service Integrations
- Implement Benchling data warehouse connection service per [07-integration-spec.md](../SPEC/07-integration-spec.md)
- Set up Cloud SQL (PostgreSQL) connection with async SQLAlchemy
- Implement GCS storage service for file operations
- Configure Google Gemini API integration
- Implement circuit breakers for external service calls
- Create health check and readiness endpoints with degraded mode support

**Key Deliverables:**
- Deployable skeleton application on Cloud Run (dev environment)
- Working CI/CD pipeline
- All external service connections verified
- Basic health monitoring

**References:**
- [02-architecture-overview.md](../SPEC/02-architecture-overview.md) - System architecture
- [03-backend-spec.md](../SPEC/03-backend-spec.md) - Backend configuration
- [07-integration-spec.md](../SPEC/07-integration-spec.md) - Service integrations
- [09-deployment-spec.md](../SPEC/09-deployment-spec.md) - Deployment procedures

---

## Sprint 2: Data Layer & Core Backend APIs

**Goal:** Implement the data models, persistence layer, and core REST API endpoints for run management and pipeline configuration.

**Estimated Duration:** 2-3 phases

### Phase 2.1: Data Models & Persistence Layer
- Implement PostgreSQL schema for `runs`, `users`, and `checkpoints` tables per [06-data-model-spec.md](../SPEC/06-data-model-spec.md)
- Create SQLAlchemy async models with Pydantic validation
- Implement `RunStoreService` for run persistence
- Implement user profile persistence (on-login upsert)
- Set up database migrations with Alembic

### Phase 2.2: Core REST API Endpoints
- Implement run management endpoints (`/api/runs`) per [03-backend-spec.md](../SPEC/03-backend-spec.md)
  - List runs with filtering and pagination
  - Get run details
  - Create run (pending state)
  - Cancel run
  - Recover run (`POST /api/runs/{id}/recover`)
- Implement pipeline registry endpoints (`/api/pipelines`)
  - List available pipelines
  - Get pipeline details and schema
- Implement Benchling data endpoints (`/api/benchling`)
- Implement SSE endpoint for run status updates (`/api/runs/{id}/events`)

### Phase 2.3: Log Service & File Management
- Implement log service per [03-backend-spec.md](../SPEC/03-backend-spec.md)
  - Workflow log streaming from GCS
  - Task list parsing from trace.txt
  - Per-task log retrieval from Cloud Logging
  - Log download archive generation
- Implement GCS file operations (upload, download, signed URLs)
- Create GCS bucket lifecycle policies for work directory cleanup

**Key Deliverables:**
- Complete REST API for run management
- Pipeline registry with nf-core/scrnaseq configuration
- Real-time run status updates via SSE
- Log access and streaming

**References:**
- [03-backend-spec.md](../SPEC/03-backend-spec.md) - API specifications
- [06-data-model-spec.md](../SPEC/06-data-model-spec.md) - Data models
- [12-recovery-spec.md](../SPEC/12-recovery-spec.md) - Recovery workflow

---

## Sprint 3: AI Agent & Agentic Features

**Goal:** Implement the core AI agent with LangChain/DeepAgents, including all Benchling discovery tools, file generation tools, and conversation management.

**Estimated Duration:** 4-5 phases

### Phase 3.1: Agent Foundation
- Set up LangChain v1 with DeepAgents framework per [05-agentic-features-spec.md](../SPEC/05-agentic-features-spec.md)
- Configure Gemini 3 Flash model with thinking levels per [11-conf-spec.md](../SPEC/11-conf-spec.md)
- Implement system prompt and agent configuration
- Set up AsyncPostgresSaver checkpointer for conversation state
- Implement WebSocket chat endpoint with AI SDK streaming format

### Phase 3.2: NGS Data Discovery Tools
- Implement core NGS discovery tools:
  - `search_ngs_runs` - Comprehensive NGS run search
  - `get_ngs_run_samples` - Detailed sample retrieval with FASTQ paths
  - `get_ngs_run_qc` - QC metrics (summary, lane, sample levels)
  - `get_fastq_paths` - Quick FASTQ path lookup
- Reference `external-repos/arc-benchling-mcp/` for implementation patterns
- Use `benchling-py` as the Benchling interface dependency

### Phase 3.3: Benchling Discovery & Schema Tools
- Implement entity discovery tools:
  - `get_entities` - Entity search with filtering
  - `get_entity_relationships` - Lineage traversal
  - `list_entries` - Notebook entry listing
  - `get_entry_content` - Entry content retrieval
  - `get_entry_entities` - Entry-associated entities
- Implement schema/metadata tools:
  - `get_schemas`, `get_schema_field_info`
  - `get_dropdown_values`, `list_projects`
- Implement `execute_warehouse_query` for advanced SQL queries

### Phase 3.4: Pipeline & File Generation Tools
- Implement pipeline info tools:
  - `list_pipelines` - Available pipeline catalog
  - `get_pipeline_schema` - Parameter schemas
- Implement file generation tools:
  - `generate_samplesheet` - CSV generation from samples
  - `generate_config` - Nextflow configuration generation
- Implement validation tool (`validate_inputs`)
- Implement GCS file existence validation

### Phase 3.5: Submission Tools & HITL Middleware
- Implement submission tools with Human-in-the-Loop approval:
  - `submit_run` - Pipeline submission to GCP Batch
  - `cancel_run` - Running job cancellation
  - `delete_file` - GCS file deletion
  - `clear_samplesheet` - Samplesheet reset
- Implement HITL middleware for approval workflows
- Implement subagents:
  - `benchling_expert` - Complex multi-step Benchling queries
  - `config_expert` - Pipeline parameter recommendations
- Implement middleware stack (TodoList, Filesystem offloading, Summarization)

**Key Deliverables:**
- Fully functional AI agent with streaming responses
- Complete Benchling discovery tool suite
- File generation and validation
- HITL-protected submission workflow
- Conversation state persistence

**References:**
- [05-agentic-features-spec.md](../SPEC/05-agentic-features-spec.md) - Agent architecture and tools
- [11-conf-spec.md](../SPEC/11-conf-spec.md) - AI model configuration
- [07-integration-spec.md](../SPEC/07-integration-spec.md) - Gemini API integration

---

## Sprint 4: Frontend Implementation

**Goal:** Build the complete frontend UI with chat interface, file editors, run management, and log viewer.

**Estimated Duration:** 4-5 phases

### Phase 4.1: Layout & Core Components
- Implement root layout with providers per [04-frontend-spec.md](../SPEC/04-frontend-spec.md)
- Create layout components (Header, Sidebar, Footer)
- Set up Tailwind CSS with Arc brand colors
- Configure HeroUI component library
- Implement Zustand stores (workspace, chat, UI)
- Set up TanStack Query with API client

### Phase 4.2: Pipeline Workspace - Chat Panel
- Implement PipelineWorkspace container
- Build ChatPanel component with:
  - MessageList and MessageBubble components
  - Streaming message display
  - ToolIndicator with collapsible accordions
  - Reasoning block filtering (hidden from user)
  - SuggestedPrompts for onboarding
  - ChatInput with submit handling
- Implement `useAgentChat` hook for AI communication

### Phase 4.3: Pipeline Workspace - File Editors
- Implement FileEditorPanel with tabbed interface
- Build SamplesheetEditor with Handsontable:
  - Column configuration from pipeline schema
  - Cell validation (required fields, GCS paths)
  - Copy/paste, row add/remove, context menu
- Build ConfigEditor with Monaco Editor:
  - Groovy/Nextflow syntax highlighting
  - Line numbers and minimap
- Implement SubmitPanel with validation display

### Phase 4.4: Run Management Pages
- Implement Runs page (`/runs`) per [04-frontend-spec.md](../SPEC/04-frontend-spec.md):
  - RunList with sortable columns and filtering
  - RunCard components
  - Pagination
  - Real-time status updates via SSE
- Implement Run Detail page (`/runs/[id]`):
  - RunDetail with tabbed interface (Overview, Logs, Files, Parameters)
  - RunStatus badge components
  - RunFiles browser with signed URL downloads
  - Action buttons (Cancel, Re-run, Recover)

### Phase 4.5: Log Viewer & Run Recovery UI
- Implement RunLogs component:
  - WorkflowLogViewer with real-time streaming
  - TaskList sidebar with task metadata
  - TaskLogViewer for per-task stdout/stderr
  - Log search/filter
  - LogLine with syntax highlighting
  - Download logs action
- Implement recovery modal per [12-recovery-spec.md](../SPEC/12-recovery-spec.md):
  - Recovery confirmation with work directory reuse
  - Optional notes and parameter overrides
  - Recovery submission flow

**Key Deliverables:**
- Complete workspace UI with chat and file editors
- Run history and detail pages
- Real-time log streaming
- Run recovery workflow
- Responsive design (desktop, tablet, mobile)

**References:**
- [04-frontend-spec.md](../SPEC/04-frontend-spec.md) - Frontend components and state
- [10-ux-spec.md](../SPEC/10-ux-spec.md) - UX patterns and interaction design
- [12-recovery-spec.md](../SPEC/12-recovery-spec.md) - Recovery UI requirements

---

## Sprint 5: GCP Batch Integration & Pipeline Execution

**Goal:** Implement the complete pipeline execution workflow including GCP Batch job submission, orchestrator container, and status update mechanism.

**Estimated Duration:** 2-3 phases

### Phase 5.1: GCP Batch Job Management
- Implement BatchService per [07-integration-spec.md](../SPEC/07-integration-spec.md):
  - Job submission with proper configuration
  - Job status monitoring
  - Job cancellation
- Configure orchestrator job specifications:
  - Machine type, spot instances, retry policies
  - Environment variable passing
  - Service account assignment
- Implement job label strategy for log filtering

### Phase 5.2: Nextflow Orchestrator Container
- Build orchestrator Docker image per [09-deployment-spec.md](../SPEC/09-deployment-spec.md)
- Implement entrypoint script with:
  - Configuration download from GCS
  - Nextflow execution
  - `-resume` support for recovery runs
- Implement `update_status.py` script for PostgreSQL status updates
- Configure Nextflow hooks (onStart, onComplete, onError)
- Implement work directory configuration per run

### Phase 5.3: End-to-End Pipeline Flow
- Integrate BatchService with run submission workflow
- Implement complete status update flow:
  - pending → submitted → running → completed/failed
  - SSE status propagation to frontend
- Test with nf-core/scrnaseq pipeline
- Implement Nextflow GCP Batch executor configuration
- Verify GCS file lifecycle (inputs → work → results → logs)

**Key Deliverables:**
- Working pipeline submission and execution
- Real-time status updates from orchestrator to frontend
- Recovery with `-resume` functionality
- Proper cleanup and lifecycle management

**References:**
- [07-integration-spec.md](../SPEC/07-integration-spec.md) - GCP Batch integration
- [06-data-model-spec.md](../SPEC/06-data-model-spec.md) - Status update mechanism
- [12-recovery-spec.md](../SPEC/12-recovery-spec.md) - Recovery orchestration

---

## Sprint 6: Security, Testing, Polish & Launch

**Goal:** Implement security hardening, comprehensive testing, performance optimization, and prepare for production launch.

**Estimated Duration:** 2-3 phases

### Phase 6.1: Security Hardening
- Implement complete IAP integration per [08-security-spec.md](../SPEC/08-security-spec.md):
  - JWT verification
  - User context extraction
  - Session management
- Configure authorization rules (own runs vs. others' runs)
- Implement prompt injection protection
- Set up audit logging with structured format
- Configure VPC, firewall rules, and egress controls
- Conduct security review and vulnerability scanning

### Phase 6.2: Testing & Quality Assurance
- Implement backend unit tests with pytest:
  - API route tests
  - Service layer tests
  - Agent tool tests
- Implement frontend tests with Jest and Testing Library
- Integration testing with mocked external services
- End-to-end testing of critical workflows:
  - Sample discovery → samplesheet generation → submission
  - Run monitoring → log viewing
  - Recovery workflow
- Performance testing and optimization

### Phase 6.3: Polish & Production Launch
- Implement UX polish per [10-ux-spec.md](../SPEC/10-ux-spec.md):
  - Onboarding flow for first-time users
  - Empty states and loading states
  - Toast notifications and feedback
  - Accessibility improvements (WCAG 2.1 AA)
- Set up monitoring and alerting per [09-deployment-spec.md](../SPEC/09-deployment-spec.md)
- Documentation (user guide, API docs, runbooks)
- Production deployment and DNS configuration
- Gradual rollout to pilot users

**Key Deliverables:**
- Secure, production-ready application
- Comprehensive test coverage
- Polished user experience
- Monitoring and alerting
- User documentation

**References:**
- [08-security-spec.md](../SPEC/08-security-spec.md) - Security requirements
- [09-deployment-spec.md](../SPEC/09-deployment-spec.md) - Production deployment
- [10-ux-spec.md](../SPEC/10-ux-spec.md) - UX polish

---

## Implementation Dependencies

```
Sprint 1 (Foundation)
    ↓
Sprint 2 (Data Layer)
    ↓
    ├──────────────────────────┐
    ↓                          ↓
Sprint 3 (AI Agent)       Sprint 4 (Frontend)
    │                          │
    └──────────┬───────────────┘
               ↓
        Sprint 5 (Pipeline Execution)
               ↓
        Sprint 6 (Security & Launch)
```

**Notes:**
- Sprints 3 and 4 can be developed in parallel after Sprint 2
- Sprint 5 requires both frontend and backend agent features
- Sprint 6 activities can partially overlap with Sprint 5

---

## Risk Mitigation

| Risk | Mitigation Strategy |
|------|---------------------|
| Benchling schema changes | Abstraction layer, monitoring, versioned queries |
| GCP Batch quotas | Early quota requests, queue management |
| LLM response quality | Extensive prompt engineering, output validation |
| Complex Nextflow configurations | Start with single pipeline (scrnaseq), expand later |
| User adoption | Gradual rollout, training, gather feedback early |
| Cost overruns | Spot instances, resource limits, monitoring |

---

## Out of Scope for MVP

Per [01-project-overview.md](../SPEC/01-project-overview.md), the following are explicitly out of scope:

- Multiple pipeline support (beyond nf-core/scrnaseq)
- Collaborative editing
- Advanced scheduling/queuing
- Cost estimation and budgeting
- Automated re-runs on failure
- Slack/email notifications
- Custom pipeline uploads
- Result visualization

---

## Success Criteria

1. Wet lab scientists can discover their samples through natural language
2. AI agent generates valid samplesheets and configurations
3. Pipeline runs execute successfully on GCP Batch
4. Users can monitor run progress and view logs
5. Failed runs can be recovered with `-resume`
6. Authentication via GCP IAP works correctly
7. All critical operations require explicit user approval (HITL)
8. Application is responsive and meets performance targets

---

## Document References

| Specification | Primary Sprints |
|---------------|-----------------|
| [01-project-overview.md](../SPEC/01-project-overview.md) | All sprints (scope) |
| [02-architecture-overview.md](../SPEC/02-architecture-overview.md) | Sprint 1, 2, 5 |
| [03-backend-spec.md](../SPEC/03-backend-spec.md) | Sprint 1, 2, 3 |
| [04-frontend-spec.md](../SPEC/04-frontend-spec.md) | Sprint 4 |
| [05-agentic-features-spec.md](../SPEC/05-agentic-features-spec.md) | Sprint 3 |
| [06-data-model-spec.md](../SPEC/06-data-model-spec.md) | Sprint 2, 5 |
| [07-integration-spec.md](../SPEC/07-integration-spec.md) | Sprint 1, 3, 5 |
| [08-security-spec.md](../SPEC/08-security-spec.md) | Sprint 1, 6 |
| [09-deployment-spec.md](../SPEC/09-deployment-spec.md) | Sprint 1, 5, 6 |
| [10-ux-spec.md](../SPEC/10-ux-spec.md) | Sprint 4, 6 |
| [11-conf-spec.md](../SPEC/11-conf-spec.md) | Sprint 3 |
| [12-recovery-spec.md](../SPEC/12-recovery-spec.md) | Sprint 2, 4, 5 |
