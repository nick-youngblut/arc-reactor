# Arc Reactor - Frontend Specification

## Overview

The frontend is a Next.js 14 application using the App Router with static export. It provides a conversational interface for pipeline configuration combined with direct editing capabilities for generated files. The UI is designed for wet lab scientists who may have limited computational experience.

## Project Structure

```
frontend/
├── app/
│   ├── layout.tsx              # Root layout with providers
│   ├── page.tsx                # Home/redirect to workspace
│   ├── workspace/
│   │   └── page.tsx            # Main pipeline workspace
│   ├── runs/
│   │   ├── page.tsx            # Run history list
│   │   └── [id]/
│   │       └── page.tsx        # Run detail view
│   └── not-found.tsx           # 404 page
│
├── components/
│   ├── layout/
│   │   ├── Header.tsx          # App header with user info
│   │   ├── Sidebar.tsx         # Navigation sidebar
│   │   └── Footer.tsx          # App footer
│   │
│   ├── workspace/
│   │   ├── PipelineWorkspace.tsx   # Main workspace container
│   │   ├── PipelineSelector.tsx    # Pipeline dropdown
│   │   ├── ChatPanel.tsx           # AI chat interface
│   │   ├── FileEditorPanel.tsx     # Tabbed file editors
│   │   ├── SamplesheetEditor.tsx   # Handsontable wrapper
│   │   ├── ConfigEditor.tsx        # Monaco editor wrapper
│   │   └── SubmitPanel.tsx         # Validation + submit
│   │
│   ├── runs/
│   │   ├── RunList.tsx             # Run history table
│   │   ├── RunCard.tsx             # Individual run card
│   │   ├── RunDetail.tsx           # Full run details
│   │   ├── RunStatus.tsx           # Status badge component
│   │   ├── RunLogs.tsx             # Log viewer with tabs
│   │   ├── WorkflowLogViewer.tsx   # Nextflow log streaming
│   │   ├── TaskLogViewer.tsx       # Per-task log viewer
│   │   ├── TaskList.tsx            # Task list sidebar
│   │   ├── LogLine.tsx             # Log line with highlighting
│   │   └── StreamingIndicator.tsx  # Live stream status
│   │   └── RunFiles.tsx            # File browser
│   │
│   ├── chat/
│   │   ├── MessageList.tsx         # Chat message display
│   │   ├── MessageBubble.tsx       # Individual message
│   │   ├── ToolIndicator.tsx       # Tool execution display
│   │   ├── ChatInput.tsx           # Message input
│   │   └── SuggestedPrompts.tsx    # Starter prompts
│   │
│   └── ui/
│       ├── Button.tsx              # Styled button
│       ├── Input.tsx               # Form input
│       ├── Select.tsx              # Dropdown select
│       ├── Modal.tsx               # Modal dialog
│       ├── Toast.tsx               # Toast notifications
│       ├── Spinner.tsx             # Loading spinner
│       └── Badge.tsx               # Status badge
│
├── hooks/
│   ├── useAgentChat.ts             # AI chat hook
│   ├── useRuns.ts                  # Run management hooks
│   ├── usePipelines.ts             # Pipeline data hooks
│   └── useUser.ts                  # User context hook
│
├── lib/
│   ├── api/
│   │   ├── client.ts               # Axios client setup
│   │   ├── runs.ts                 # Run API functions
│   │   ├── pipelines.ts            # Pipeline API functions
│   │   └── benchling.ts            # Benchling API functions
│   │
│   ├── utils/
│   │   ├── csv.ts                  # CSV parsing utilities
│   │   ├── validation.ts           # Input validation
│   │   └── formatting.ts           # Display formatting
│   │
│   └── query-client.ts             # TanStack Query setup
│
├── stores/
│   ├── workspaceStore.ts           # Workspace state (Zustand)
│   ├── chatStore.ts                # Chat history state
│   └── uiStore.ts                  # UI state (modals, toasts)
│
├── types/
│   ├── runs.ts                     # Run type definitions
│   ├── pipelines.ts                # Pipeline type definitions
│   ├── chat.ts                     # Chat type definitions
│   └── api.ts                      # API response types
│
├── styles/
│   └── globals.css                 # Global styles + Tailwind
│
├── public/
│   ├── favicon.ico
│   └── logo.svg
│
├── next.config.js                  # Next.js configuration
├── tailwind.config.js              # Tailwind configuration
├── tsconfig.json                   # TypeScript configuration
└── package.json
```

## Page Structure

### Workspace Page (`/workspace`)

The primary interface where users interact with the AI and configure pipelines.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Header                                                      User | Logout  │
├────────────────┬────────────────────────────────────────────────────────────┤
│                │  Pipeline: [nf-core/scrnaseq ▼]  [v2.7.1 ▼]                │
│   Sidebar      ├────────────────────────────────────────────────────────────┤
│                │                                                            │
│   • Workspace  │  ┌─────────────────────┐  ┌────────────────────────────┐   │
│   • Runs       │  │   Chat Panel        │  │   File Editor Panel        │   │
│                │  │                     │  │                            │   │
│                │  │   [AI messages]     │  │   [samplesheet] [config]   │   │
│                │  │                     │  │   ┌────────────────────┐   │   │
│                │  │                     │  │   │                    │   │   │
│                │  │                     │  │   │   Handsontable /   │   │   │
│                │  │                     │  │   │   Monaco Editor    │   │   │
│                │  │                     │  │   │                    │   │   │
│                │  │                     │  │   └────────────────────┘   │   │
│                │  │   [Input box]       │  │                            │   │
│                │  └─────────────────────┘  └────────────────────────────┘   │
│                ├────────────────────────────────────────────────────────────┤
│                │  [Validate]                              [Submit Run →]    │
└────────────────┴────────────────────────────────────────────────────────────┘
```

### Runs Page (`/runs`)

History of all pipeline runs with filtering and search.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Header                                                      User | Logout  │
├────────────────┬────────────────────────────────────────────────────────────┤
│                │  Run History                           [Search...] [Filter]│
│   Sidebar      ├────────────────────────────────────────────────────────────┤
│                │                                                            │
│   • Workspace  │  ┌──────────────────────────────────────────────────────┐  │
│   • Runs       │  │ Run ID    Pipeline    Status    Created    Samples   │  │
│                │  ├──────────────────────────────────────────────────────┤  │
│                │  │ abc123    scrnaseq    ● Running  2h ago     48       │  │
│                │  │ def456    scrnaseq    ✓ Done     1d ago     24       │  │
│                │  │ ghi789    scrnaseq    ✗ Failed   2d ago     96       │  │
│                │  │ ...                                                  │  │
│                │  └──────────────────────────────────────────────────────┘  │
│                │                                                            │
│                │  [← Prev]  Page 1 of 5  [Next →]                           │
└────────────────┴────────────────────────────────────────────────────────────┘
```

### Run Detail Page (`/runs/[id]`)

Detailed view of a specific run with logs and files.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Header                                                      User | Logout  │
├────────────────┬────────────────────────────────────────────────────────────┤
│                │  ← Back to Runs                                            │
│   Sidebar      │                                                            │
│                │  Run: abc123                              ● Running        │
│   • Workspace  │  Pipeline: nf-core/scrnaseq v2.7.1                         │
│   • Runs       │  Started: Dec 15, 2024 2:30 PM                             │
│                │                                                            │
│                │  ┌─────────────────────────────────────────────────────┐   │
│                │  │  [Overview] [Logs] [Files] [Parameters]             │   │
│                │  ├─────────────────────────────────────────────────────┤   │
│                │  │                                                     │   │
│                │  │  ... tab content ...                                │   │
│                │  │                                                     │   │
│                │  └─────────────────────────────────────────────────────┘   │
│                │                                                            │
│                │  [Cancel Run]  [Re-run with Changes]                       │
└────────────────┴────────────────────────────────────────────────────────────┘
```

**Status Updates:**
- Primary: SSE stream from `GET /api/runs/{id}/events` for real-time status changes
- Fallback: Poll `GET /api/runs/{id}` every 5-30 seconds if SSE is unavailable

**Log Viewing:**
- Workflow logs stream in real time while a run is `running` via `GET /api/runs/{id}/logs/stream?source=workflow`
- Task logs pull from `GET /api/runs/{id}/tasks` and `GET /api/runs/{id}/tasks/{task_id}/logs`
- Download logs archive from `GET /api/runs/{id}/logs/download`

## Key Components

### PipelineWorkspace

The main container component that orchestrates the workspace.

**Responsibilities:**
- Manages overall workspace state
- Coordinates between chat and file editors
- Handles submit flow

**State Management:**
```typescript
interface WorkspaceState {
  selectedPipeline: string;
  selectedVersion: string;
  generatedFiles: {
    samplesheet: string | null;
    config: string | null;
  };
  validationErrors: ValidationError[];
  isSubmitting: boolean;
}
```

### ChatPanel

The AI conversation interface.

**Features:**
- Streaming message display
- Tool execution indicators
- Suggested prompts for new users
- Message history persistence (per session)

**Message Types:**
```typescript
type MessageRole = "user" | "assistant";

interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  toolInvocations?: ToolInvocation[];
  createdAt: Date;
}

interface ToolInvocation {
  toolCallId: string;
  toolName: string;
  args: Record<string, unknown>;
  state: "pending" | "result";
  result?: string;
}
```

### SamplesheetEditor

Spreadsheet interface for editing samplesheets.

**Technology:** Handsontable (Excel-like grid)

**Features:**
- Column headers from pipeline schema
- Cell validation (required fields, file paths)
- Row add/remove
- Copy/paste from Excel
- CSV export

**Configuration:**
```typescript
const handsontableConfig = {
  licenseKey: "non-commercial-and-evaluation",
  columns: [
    { data: "sample", type: "text" },
    { data: "fastq_1", type: "text", validator: gcsPathValidator },
    { data: "fastq_2", type: "text", validator: gcsPathValidator },
    { data: "expected_cells", type: "numeric" },
  ],
  colHeaders: ["Sample", "FASTQ R1", "FASTQ R2", "Expected Cells"],
  rowHeaders: true,
  contextMenu: true,
  manualColumnResize: true,
};
```

### ConfigEditor

Code editor for Nextflow configuration.

**Technology:** Monaco Editor (VS Code editor)

**Features:**
- Groovy/Nextflow syntax highlighting
- Basic autocompletion for common params
- Error highlighting for invalid syntax
- Line numbers and minimap

**Configuration:**
```typescript
const monacoConfig = {
  language: "groovy",
  theme: "vs-light",
  minimap: { enabled: false },
  lineNumbers: "on",
  automaticLayout: true,
  fontSize: 14,
};
```

### RunList

Table displaying run history.

**Features:**
- Sortable columns
- Status filtering
- Search by run ID or pipeline
- Pagination
- Real-time status updates

**Columns:**
| Column | Description | Sortable |
|--------|-------------|----------|
| Run ID | Truncated run identifier | No |
| Pipeline | Pipeline name + version | Yes |
| Status | Current run status | Yes |
| Created | Creation timestamp | Yes |
| Samples | Sample count | Yes |
| Actions | View, Re-run, Cancel | No |

### RunLogs

Log viewer for workflow and task-level debugging.

**Tabs:**
- **Workflow Log**: Streams `nextflow.log` while running, fetches full log when complete
- **Task Logs**: Task list from `trace.txt` with per-task stdout/stderr

**Features:**
- Real-time streaming via SSE for active runs
- Search/filter across visible log lines
- Auto-scroll toggle while streaming
- Log download action (zip/tar archive)

**Data Sources:**
- `GET /api/runs/{id}/logs/stream?source=workflow`
- `GET /api/runs/{id}/tasks`
- `GET /api/runs/{id}/tasks/{task_id}/logs`
- `GET /api/runs/{id}/logs/download`

## State Management

### Zustand Stores

#### workspaceStore

Manages the pipeline configuration workspace.

```typescript
interface WorkspaceStore {
  // Pipeline selection
  pipeline: string;
  version: string;
  setPipeline: (pipeline: string) => void;
  setVersion: (version: string) => void;
  
  // Generated files
  samplesheet: string | null;
  config: string | null;
  setSamplesheet: (csv: string) => void;
  setConfig: (config: string) => void;
  
  // Validation
  errors: ValidationError[];
  setErrors: (errors: ValidationError[]) => void;
  
  // Reset
  reset: () => void;
}
```

#### chatStore

Manages chat history and state.

```typescript
interface ChatStore {
  messages: ChatMessage[];
  threadId: string | null;
  isLoading: boolean;
  
  addMessage: (message: ChatMessage) => void;
  updateMessage: (id: string, updates: Partial<ChatMessage>) => void;
  setThreadId: (id: string) => void;
  setLoading: (loading: boolean) => void;
  clearHistory: () => void;
}
```

### TanStack Query

Used for server state management (API data).

**Query Keys:**
```typescript
const queryKeys = {
  runs: {
    all: ["runs"] as const,
    list: (filters: RunFilters) => ["runs", "list", filters] as const,
    detail: (id: string) => ["runs", "detail", id] as const,
  },
  pipelines: {
    all: ["pipelines"] as const,
    detail: (name: string) => ["pipelines", name] as const,
  },
  benchling: {
    runs: (filters: BenchlingFilters) => ["benchling", "runs", filters] as const,
    samples: (runId: string) => ["benchling", "samples", runId] as const,
  },
};
```

**Example Hook:**
```typescript
function useRuns(filters: RunFilters) {
  return useQuery({
    queryKey: queryKeys.runs.list(filters),
    queryFn: () => api.runs.list(filters),
    refetchInterval: 30000, // Poll for status updates
  });
}
```

## Custom Hooks

### useAgentChat

Integrates with the AI chat backend using Vercel AI SDK patterns.

```typescript
function useAgentChat() {
  const { messages, input, handleInputChange, handleSubmit, isLoading } = useChat({
    api: "/api/chat",
    onToolCall: async ({ toolCall }) => {
      // Handle file generation tools
      if (toolCall.toolName === "generate_samplesheet") {
        workspaceStore.setSamplesheet(toolCall.result);
      }
    },
  });
  
  return {
    messages,
    input,
    handleInputChange,
    handleSubmit,
    isLoading,
    // ... additional helpers
  };
}
```

### useRuns

Manages run list and individual run data.

```typescript
function useRuns(filters: RunFilters = {}) {
  const listQuery = useQuery(/* ... */);
  
  const submitMutation = useMutation({
    mutationFn: api.runs.submit,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.runs.all });
    },
  });
  
  const cancelMutation = useMutation({
    mutationFn: api.runs.cancel,
    // ...
  });
  
  return {
    runs: listQuery.data,
    isLoading: listQuery.isLoading,
    submit: submitMutation.mutate,
    cancel: cancelMutation.mutate,
  };
}
```

### useRunEvents

SSE-based hook for real-time run status updates.

```typescript
function useRunEvents(runId: string, enabled: boolean = true) {
  const [status, setStatus] = useState<RunStatus | null>(null);

  useEffect(() => {
    if (!enabled || !runId) return;

    const eventSource = new EventSource(`/api/runs/${runId}/events`);

    eventSource.addEventListener("status", (event) => {
      const data = JSON.parse(event.data);
      setStatus(data);
    });

    eventSource.addEventListener("done", () => {
      eventSource.close();
    });

    eventSource.onerror = () => {
      // EventSource auto-reconnects by default
      console.warn("Run events stream error, reconnecting...");
    };

    return () => eventSource.close();
  }, [runId, enabled]);

  return status;
}
```

### useRunStatus (alternative)

Polling-based hook using TanStack Query `refetchInterval`.

```typescript
function useRunStatus(runId: string) {
  return useQuery({
    queryKey: queryKeys.runs.detail(runId),
    queryFn: () => api.runs.get(runId),
    refetchInterval: (data) => {
      if (!data) return 5000;
      if (["completed", "failed", "cancelled"].includes(data.status)) {
        return false;
      }
      return 5000;
    },
    enabled: !!runId,
  });
}
```

### usePipelines

Provides pipeline configuration data.

```typescript
function usePipelines() {
  const listQuery = useQuery({
    queryKey: queryKeys.pipelines.all,
    queryFn: api.pipelines.list,
    staleTime: Infinity, // Pipelines rarely change
  });
  
  return {
    pipelines: listQuery.data,
    isLoading: listQuery.isLoading,
  };
}

function usePipelineSchema(pipelineName: string) {
  return useQuery({
    queryKey: queryKeys.pipelines.detail(pipelineName),
    queryFn: () => api.pipelines.getSchema(pipelineName),
    enabled: !!pipelineName,
  });
}
```

## API Client

### Configuration

```typescript
// lib/api/client.ts
import axios from "axios";

const apiClient = axios.create({
  baseURL: "/api",
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Redirect to login
      window.location.href = "/";
    }
    return Promise.reject(error);
  }
);
```

### API Functions

```typescript
// lib/api/runs.ts
export const runsApi = {
  list: async (filters: RunFilters): Promise<RunListResponse> => {
    const { data } = await apiClient.get("/runs", { params: filters });
    return data;
  },
  
  get: async (id: string): Promise<Run> => {
    const { data } = await apiClient.get(`/runs/${id}`);
    return data;
  },
  
  submit: async (request: RunSubmitRequest): Promise<Run> => {
    const { data } = await apiClient.post("/runs", request);
    return data;
  },
  
  cancel: async (id: string): Promise<void> => {
    await apiClient.delete(`/runs/${id}`);
  },
};
```

## Styling

### Tailwind Configuration

```javascript
// tailwind.config.js
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: "#f0f9ff",
          500: "#0ea5e9",
          600: "#0284c7",
          700: "#0369a1",
        },
        // Arc brand colors
        arc: {
          blue: "#1e3a5f",
          teal: "#2dd4bf",
        },
      },
    },
  },
  plugins: [
    require("@tailwindcss/forms"),
    require("@tailwindcss/typography"),
  ],
};
```

### Component Styling Patterns

- **Utility-first**: Use Tailwind classes directly
- **Component variants**: Use `clsx` for conditional classes
- **Shared styles**: Extract to component-level constants
- **No CSS modules**: Keep styling in component files

## Accessibility

### Requirements

- WCAG 2.1 AA compliance
- Keyboard navigation for all interactions
- Screen reader support
- Color contrast ratios > 4.5:1

### Implementation

- All interactive elements are focusable
- ARIA labels for non-text content
- Focus trapping in modals
- Skip links for main content

## Performance

### Optimization Strategies

| Strategy | Implementation |
|----------|----------------|
| Code splitting | Next.js automatic per-page |
| Lazy loading | `dynamic()` for heavy components (Monaco, Handsontable) |
| Image optimization | Next.js Image component |
| Bundle analysis | `@next/bundle-analyzer` |

### Bundle Size Targets

| Bundle | Target | Current Libraries |
|--------|--------|-------------------|
| Main | < 200KB | React, Next.js core |
| Workspace | < 500KB | Monaco, Handsontable |
| Run History | < 100KB | Table component |

## Error Handling

### Error Boundaries

```typescript
// components/ErrorBoundary.tsx
class ErrorBoundary extends React.Component {
  state = { hasError: false, error: null };
  
  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }
  
  render() {
    if (this.state.hasError) {
      return <ErrorFallback error={this.state.error} />;
    }
    return this.props.children;
  }
}
```

### API Error Display

```typescript
// hooks/useApiError.ts
function useApiError() {
  const { addToast } = useUIStore();
  
  const handleError = useCallback((error: unknown) => {
    const message = error instanceof ApiError 
      ? error.message 
      : "An unexpected error occurred";
    
    addToast({
      type: "error",
      message,
      duration: 5000,
    });
  }, [addToast]);
  
  return { handleError };
}
```

## Testing Strategy

### Unit Tests

- **Framework**: Jest + React Testing Library
- **Coverage target**: 80% for hooks and utilities
- **Focus**: Business logic, state management

### Integration Tests

- **Framework**: Playwright
- **Scope**: Critical user flows
- **Flows to test**:
  - Complete pipeline submission
  - Chat interaction
  - File editing
  - Run monitoring

### Component Tests

- **Framework**: Storybook
- **Scope**: All UI components
- **Benefits**: Visual regression, documentation
