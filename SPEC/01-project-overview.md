# Arc Reactor - Project Overview

## Executive Summary

Arc Reactor is a web application that enables wet lab scientists at Arc Institute to run Nextflow bioinformatics pipelines on Google Cloud Platform without requiring command-line expertise. The platform combines an AI-powered assistant with a user-friendly interface to bridge the gap between sample data in Benchling LIMS and computational analysis pipelines.

## Project Goals

### Primary Goals

1. **Democratize pipeline access**: Enable wet lab scientists to run complex bioinformatics pipelines without computational expertise
2. **Streamline sample-to-analysis workflow**: Automatically connect Benchling sample data to pipeline inputs
3. **Reduce errors**: Use AI assistance and validation to prevent common configuration mistakes
4. **Maintain auditability**: Track all pipeline runs with full provenance

### Secondary Goals

1. **Reduce support burden**: Minimize requests to computational biologists for routine pipeline runs
2. **Standardize workflows**: Ensure consistent pipeline configurations across the institute
3. **Enable self-service**: Allow users to monitor, troubleshoot, and re-run analyses independently

## Target Users

### Primary Users: Wet Lab Scientists

- **Technical level**: Comfortable with web applications, limited command-line experience
- **Domain expertise**: Deep understanding of their experimental data and expected results
- **Typical tasks**: 
  - Running standard analysis pipelines on their sequencing data
  - Checking run status and results
  - Re-running failed analyses with adjusted parameters

### Secondary Users: Computational Biologists

- **Technical level**: Expert command-line and programming skills
- **Role**: 
  - Configure new pipelines for the platform
  - Troubleshoot complex failures
  - Optimize pipeline configurations

## Core Capabilities

### 1. Sample Discovery

Users can find their samples through natural language queries to an AI assistant:
- "Find my samples from last week's NovaSeq run"
- "Show me the HeLa samples from the Smith project"
- "What samples are in NGS run NR-2024-0156?"

The assistant queries Benchling's data warehouse to locate samples, FASTQ file paths, and associated metadata.

### 2. Pipeline Configuration

The AI assistant helps users configure pipeline runs by:
- Generating samplesheet CSV files from Benchling data
- Creating Nextflow configuration files with appropriate parameters
- Recommending settings based on sample metadata (organism, protocol, etc.)
- Validating configurations before submission

### 3. Human-in-the-Loop Editing

Before submission, users can:
- Review and edit generated samplesheets in a spreadsheet interface
- Modify Nextflow configuration in a code editor
- Ask the AI to make specific changes ("Remove samples 5-10", "Change genome to GRCm39")

### 4. Pipeline Execution

The platform submits pipelines to GCP Batch, which:
- Runs the Nextflow orchestrator as a long-running job
- Spawns individual task jobs for each pipeline step
- Stores intermediate and final results in GCS

### 5. Run Monitoring

Users can track their pipeline runs through:
- Real-time status updates (pending, running, completed, failed)
- Access to Nextflow execution logs
- Links to output files in GCS
- Run history with filtering and search

## System Context

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Arc Institute                                  │
│                                                                             │
│  ┌─────────────┐     ┌─────────────────────┐     ┌─────────────────────┐    │
│  │  Wet Lab    │     │  Arc Nextflow       │     │  Computational      │    │
│  │  Scientists │────▶│  Platform           │◀────│  Biologists         │    │
│  │             │     │                     │     │  (config/support)   │    │
│  └─────────────┘     └──────────┬──────────┘     └─────────────────────┘    │
│                                 │                                           │
└─────────────────────────────────┼───────────────────────────────────────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
          ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Benchling     │    │  Google Cloud   │    │   nf-core       │
│   LIMS          │    │  Platform       │    │   Pipelines     │
│                 │    │                 │    │                 │
│  • Sample data  │    │  • Cloud Run    │    │  • scrnaseq     │
│  • FASTQ paths  │    │  • Batch        │    │  • rnaseq       │
│  • Metadata     │    │  • Storage      │    │  • (future)     │
│                 │    │  • Cloud SQL    │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Key Workflows

### Workflow 1: New Pipeline Run

```
1. User opens platform → sees chat interface + empty file panels
2. User describes samples → "Run scRNA-seq on my NovaSeq samples from Dec 15"
3. AI searches Benchling → finds matching NGS run and samples
4. AI presents options → "Found 48 samples. Include all or filter?"
5. User refines → "Just the HeLa samples"
6. AI generates files → samplesheet.csv + nextflow.config appear in editors
7. User reviews/edits → makes any needed changes
8. User clicks Submit → AI validates, then submits to GCP Batch
9. User monitors → sees status updates in run history
10. Run completes → user accesses results in GCS
```

### Workflow 2: Re-run with Modifications

```
1. User views run history → finds previous run
2. User clicks "Re-run" → chat + files populated from previous run
3. User requests changes → "Add 10 more samples from pool XYZ"
4. AI modifies files → updates samplesheet
5. User submits → new run starts
```

### Workflow 3: Troubleshooting Failed Run

```
1. User sees failed run in history
2. User clicks to view details → sees error message and logs
3. User asks AI → "Why did this fail?"
4. AI analyzes logs → "Sample S12 has no R2 file"
5. User decides → remove sample or fix in Benchling
6. User re-runs with fix
```

## Technology Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| **Frontend** | Next.js 14 (App Router) | Modern React, static export capability |
| **UI Components** | Tailwind CSS (custom components) | Clean, accessible components |
| **Data Tables** | Handsontable | Excel-like editing for samplesheets |
| **Code Editor** | Monaco Editor | VS Code-quality config editing |
| **Chat Interface** | Vercel AI SDK | Streaming, tool calls, great DX |
| **Backend** | FastAPI | Async, OpenAPI docs, Python ecosystem |
| **AI Framework** | LangChain + DeepAgents | Tool use, streaming, state management |
| **LLM** | Gemini 3 Flash (`gemini-3-flash-preview`) | Best balance of speed, capability, and cost (see `SPEC/11-conf-spec.md`) |
| **Database** | Cloud SQL (PostgreSQL) | ACID transactions, rich queries |
| **File Storage** | Google Cloud Storage | Native Nextflow integration |
| **Job Execution** | GCP Batch | Long-running jobs, native GCP |
| **Hosting** | Cloud Run | Serverless, auto-scaling |
| **Auth** | GCP IAP | Google Workspace SSO |

## Project Scope

### In Scope (MVP)

- Single-cell RNA-seq pipeline (nf-core/scrnaseq)
- Benchling integration for sample discovery
- AI-assisted samplesheet generation
- AI-assisted config generation
- Manual file editing
- GCP Batch job submission and monitoring
- Run history and status tracking
- Basic error reporting

### Out of Scope (MVP)

- Multiple pipeline support (future: rnaseq, atacseq, etc.)
- Collaborative editing
- Advanced scheduling/queuing
- Cost estimation and budgeting
- Automated re-runs on failure
- Manual recovery with Nextflow `-resume` (see `SPEC/12-recovery-spec.md`)
- Slack/email notifications
- Custom pipeline uploads
- Result visualization

### Future Considerations

- Integration with Asana for project tracking
- Integration with Google Drive for result sharing
- Support for Ultima sequencing data
- Multi-tenancy for different research groups
- Pipeline marketplace for custom workflows

## Risks and Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| AI generates incorrect configs | High | Medium | Validation layer, human review required |
| GCP Batch job failures | Medium | Low | Retry logic, clear error messages |
| Benchling schema changes | Medium | Low | Abstraction layer, monitoring |
| Cost overruns | Medium | Medium | Spot instances, resource limits |
| User adoption resistance | Medium | Medium | Training, gradual rollout |

## Document Index

1. **Project Overview** (this document)
2. [Architecture Overview](./02-architecture-overview.md)
3. [Backend Specification](./03-backend-spec.md)
4. [Frontend Specification](./04-frontend-spec.md)
5. [Agentic Features Specification](./05-agentic-features-spec.md)
6. [Data Model Specification](./06-data-model-spec.md)
7. [Integration Specification](./07-integration-spec.md)
8. [Security Specification](./08-security-spec.md)
9. [Deployment Specification](./09-deployment-spec.md)
10. [User Experience Specification](./10-ux-spec.md)
11. [Configuration Specification](./11-conf-spec.md)
12. [Recovery Specification](./12-recovery-spec.md)
