# Sprint 4: Frontend Implementation

## Overview

This sprint builds the complete frontend UI with chat interface, file editors, run management pages, log viewer, and run recovery workflow.

## References

- [04-frontend-spec.md](../spec/04-frontend-spec.md) - Frontend components and state
- [10-ux-spec.md](../spec/10-ux-spec.md) - UX patterns and interaction design
- [12-recovery-spec.md](../spec/12-recovery-spec.md) - Recovery UI requirements

---

## Phase 4.1: Layout & Core Components

> **Spec References:**
> - [04-frontend-spec.md#root-layout](../spec/04-frontend-spec.md) - Layout structure
> - [04-frontend-spec.md#state-management](../spec/04-frontend-spec.md) - Zustand and TanStack Query
> - [04-frontend-spec.md#styling](../spec/04-frontend-spec.md) - Tailwind CSS and HeroUI

### Root Layout & Providers

- [x] Update `frontend/app/layout.tsx` — *See [04-frontend-spec.md#root-layout](../spec/04-frontend-spec.md)*:
  - [x] Configure HTML structure with proper lang attribute
  - [x] Add metadata (title, description, favicon)
  - [x] Wrap with QueryClientProvider (TanStack Query) — *See [04-frontend-spec.md#tanstack-query](../spec/04-frontend-spec.md)*
  - [x] Wrap with HeroUI provider
  - [x] Add ThemeProvider for dark/light mode
  - [x] Add global error boundary

- [x] Create `frontend/lib/queryClient.ts`:
  - [x] Configure QueryClient with defaults:
    - [x] Stale time: 5 minutes
    - [x] Retry: 3 times with backoff
    - [x] Refetch on window focus: true
  - [x] Export QueryClientProvider setup

### Header Component

> **Spec References:**
> - [10-ux-spec.md#interface-components](../spec/10-ux-spec.md) - Component layout

- [x] Create `frontend/components/Header.tsx`:
  - [x] Display Arc Reactor logo and title
  - [x] Navigation links (Workspace, Runs)
  - [x] User menu dropdown:
    - [x] User avatar/initials
    - [x] User email
    - [x] Settings link
    - [x] Logout action
  - [x] Theme toggle (dark/light mode)

### Sidebar Component

- [x] Create `frontend/components/Sidebar.tsx`:
  - [x] Navigation items with icons:
    - [x] Workspace (chat + editors)
    - [x] Runs (run history)
  - [x] Active state highlighting
  - [x] Collapsible on smaller screens — *See [10-ux-spec.md#responsive-behavior](../spec/10-ux-spec.md)*
  - [x] Arc Institute branding at bottom

### Main Layout Component

> **Spec References:**
> - [10-ux-spec.md#workspace-layout](../spec/10-ux-spec.md) - Layout structure

- [x] Create `frontend/components/MainLayout.tsx` — *See [10-ux-spec.md#workspace-layout](../spec/10-ux-spec.md)*:
  - [x] Integrate Header and Sidebar
  - [x] Main content area with routing
  - [x] Responsive grid layout — *See [10-ux-spec.md#responsive-behavior](../spec/10-ux-spec.md)*:
    - [x] Desktop: Sidebar + main content
    - [x] Tablet: Collapsible sidebar
    - [x] Mobile: Bottom navigation

### Tailwind CSS Configuration

> **Spec References:**
> - [04-frontend-spec.md#styling](../spec/04-frontend-spec.md) - CSS configuration

- [x] Update `tailwind.config.js` — *See [04-frontend-spec.md#styling](../spec/04-frontend-spec.md)*:
  - [x] Define Arc brand colors:
    - [x] Primary (arc-blue)
    - [x] Secondary
    - [x] Success, Warning, Error, Info
    - [x] Neutral grays
  - [x] Configure dark mode (class-based)
  - [x] Add custom spacing and typography
  - [x] Configure HeroUI plugin

- [x] Update `frontend/styles/globals.css`:
  - [x] Tailwind directives
  - [x] Base styles and resets
  - [x] Custom utility classes
  - [x] CSS variables for theming

### HeroUI Configuration

- [x] Create `frontend/lib/heroui.ts`:
  - [x] Configure HeroUI theme
  - [x] Set default component variants
  - [x] Configure modal/toast defaults

### Zustand Stores

> **Spec References:**
> - [04-frontend-spec.md#state-management](../spec/04-frontend-spec.md) - Store definitions
> - [04-frontend-spec.md#workspace-store](../spec/04-frontend-spec.md) - Workspace state

- [x] Create `frontend/stores/workspaceStore.ts` — *See [04-frontend-spec.md#workspace-store](../spec/04-frontend-spec.md)*:
  - [x] State:
    - [x] `selectedPipeline`: Pipeline name
    - [x] `selectedVersion`: Pipeline version
    - [x] `samplesheet`: CSV content
    - [x] `config`: Config content
    - [x] `validationResult`: Validation state
    - [x] `isDirty`: Unsaved changes flag
  - [x] Actions:
    - [x] `setPipeline()`
    - [x] `setSamplesheet()`
    - [x] `setConfig()`
    - [x] `clearWorkspace()`
    - [x] `setValidationResult()`

- [x] Create `frontend/stores/chatStore.ts` — *See [04-frontend-spec.md#chat-store](../spec/04-frontend-spec.md)*:
  - [x] State:
    - [x] `messages`: Chat message array
    - [x] `isLoading`: Agent responding flag
    - [x] `threadId`: Conversation thread ID
    - [x] `error`: Error state
  - [x] Actions:
    - [x] `addMessage()`
    - [x] `updateLastMessage()`
    - [x] `clearMessages()`
    - [x] `setError()`

- [x] Create `frontend/stores/uiStore.ts`:
  - [x] State:
    - [x] `sidebarOpen`: Sidebar visibility
    - [x] `activeTab`: Current file tab
    - [x] `theme`: Light/dark mode
  - [x] Actions:
    - [x] `toggleSidebar()`
    - [x] `setActiveTab()`
    - [x] `setTheme()`

### TanStack Query Setup

> **Spec References:**
> - [04-frontend-spec.md#api-client](../spec/04-frontend-spec.md) - API client configuration
> - [04-frontend-spec.md#relative-paths](../spec/04-frontend-spec.md) - Relative path requirement

- [x] Create `frontend/lib/api.ts` — *See [04-frontend-spec.md#api-client](../spec/04-frontend-spec.md)*:
  - [x] Configure Axios instance:
    - [x] Base URL: relative paths (e.g., `/api`) — *See [04-frontend-spec.md#relative-paths](../spec/04-frontend-spec.md)*
    - [x] Request interceptors for auth
    - [x] Response interceptors for errors
  - [x] Export typed API functions:
    - [x] `fetchRuns()`
    - [x] `fetchRun(id)`
    - [x] `createRun()`
    - [x] `cancelRun(id)`
    - [x] `recoverRun(id, options)` — *See [12-recovery-spec.md#frontend-workflow](../spec/12-recovery-spec.md)*
    - [x] `fetchPipelines()`
    - [x] `fetchPipeline(name)`

---

## Phase 4.2: Pipeline Workspace - Chat Panel

> **Spec References:**
> - [04-frontend-spec.md#pipelineworkspace](../spec/04-frontend-spec.md) - Workspace container
> - [04-frontend-spec.md#chatpanel](../spec/04-frontend-spec.md) - Chat component
> - [10-ux-spec.md#chat-panel-states](../spec/10-ux-spec.md) - Chat UX states

### PipelineWorkspace Container

- [x] Create `frontend/components/workspace/PipelineWorkspace.tsx` — *See [04-frontend-spec.md#pipelineworkspace](../spec/04-frontend-spec.md)*:
  - [x] Two-column layout — *See [10-ux-spec.md#workspace-layout](../spec/10-ux-spec.md)*:
    - [x] Left: ChatPanel (40% width)
    - [x] Right: FileEditorPanel (60% width)
  - [x] Pipeline selector in header:
    - [x] Dropdown for pipeline selection
    - [x] Version dropdown
  - [x] Status bar at bottom:
    - [x] Validation status indicators
    - [x] Submit Run button
  - [x] Responsive: Stack panels on smaller screens

### Chat Panel Component

> **Spec References:**
> - [04-frontend-spec.md#chatpanel](../spec/04-frontend-spec.md) - Complete chat specification
> - [10-ux-spec.md#chat-panel-states](../spec/10-ux-spec.md) - Chat states

- [x] Create `frontend/components/chat/ChatPanel.tsx` — *See [04-frontend-spec.md#chatpanel](../spec/04-frontend-spec.md)*:
  - [x] Panel header with title and clear button
  - [x] MessageList component
  - [x] ChatInput at bottom
  - [x] Loading state indicator — *See [10-ux-spec.md#loading-states](../spec/10-ux-spec.md)*

### Message List Component

- [x] Create `frontend/components/chat/MessageList.tsx`:
  - [x] Scrollable message container
  - [x] Auto-scroll to bottom on new messages
  - [x] Map messages to MessageBubble components
  - [x] Handle empty state with welcome message — *See [10-ux-spec.md#empty-states](../spec/10-ux-spec.md)*

### Message Bubble Component

> **Spec References:**
> - [04-frontend-spec.md#messagebubble](../spec/04-frontend-spec.md) - Message rendering
> - [04-frontend-spec.md#tool-indicator](../spec/04-frontend-spec.md) - Tool call display

- [x] Create `frontend/components/chat/MessageBubble.tsx` — *See [04-frontend-spec.md#messagebubble](../spec/04-frontend-spec.md)*:
  - [x] Differentiate user vs assistant messages:
    - [x] User: Right-aligned, primary color
    - [x] Assistant: Left-aligned, secondary color
  - [x] Render markdown content
  - [x] Support streaming text display
  - [x] Render tool calls as ToolIndicator — *See [04-frontend-spec.md#tool-indicator](../spec/04-frontend-spec.md)*
  - [x] Display message timestamp

### Tool Indicator Component

> **Spec References:**
> - [04-frontend-spec.md#toolindicator](../spec/04-frontend-spec.md) - Tool call display
> - [05-agentic-features-spec.md#tool-output-handling](../spec/05-agentic-features-spec.md) - Tool output format

- [x] Create `frontend/components/chat/ToolIndicator.tsx` — *See [04-frontend-spec.md#toolindicator](../spec/04-frontend-spec.md)*:
  - [x] Collapsible accordion for tool calls
  - [x] Tool name badge with icon
  - [x] Status indicator (pending, running, completed, error)
  - [x] Expandable details:
    - [x] Tool parameters (formatted JSON/YAML)
    - [x] Tool result summary
  - [x] Distinct styling per tool category

### Streaming Message Display

- [x] Create `frontend/components/chat/StreamingMessage.tsx`:
  - [x] Accept streaming text content
  - [x] Display with typing cursor effect
  - [x] Handle markdown rendering incrementally
  - [x] Smooth text reveal animation

### Suggested Prompts Component

> **Spec References:**
> - [10-ux-spec.md#onboarding](../spec/10-ux-spec.md) - First-time user experience

- [x] Create `frontend/components/chat/SuggestedPrompts.tsx` — *See [10-ux-spec.md#onboarding](../spec/10-ux-spec.md)*:
  - [x] Display when chat is empty
  - [x] Predefined prompt suggestions:
    - [x] "Find my samples from last week"
    - [x] "Search for SspArc0050"
    - [x] "Run scRNA-seq analysis"
    - [x] "Show available pipelines"
  - [x] Click to populate chat input
  - [x] Fade out after first message

### Chat Input Component

> **Spec References:**
> - [10-ux-spec.md#chat-interaction](../spec/10-ux-spec.md) - Chat input behavior

- [x] Create `frontend/components/chat/ChatInput.tsx` — *See [10-ux-spec.md#chat-interaction](../spec/10-ux-spec.md)*:
  - [x] Textarea with auto-resize
  - [x] Submit button
  - [x] Keyboard handling — *See [10-ux-spec.md#keyboard-navigation](../spec/10-ux-spec.md)*:
    - [x] Enter to send
    - [x] Shift+Enter for newline
  - [x] Disabled state while loading
  - [x] Character count indicator

### useAgentChat Hook

> **Spec References:**
> - [04-frontend-spec.md#useagentchat](../spec/04-frontend-spec.md) - Chat hook specification
> - [04-frontend-spec.md#ai-sdk-protocol](../spec/04-frontend-spec.md) - Streaming protocol

- [x] Create `frontend/hooks/useAgentChat.ts` — *See [04-frontend-spec.md#useagentchat](../spec/04-frontend-spec.md)*:
  - [x] Integrate with Vercel AI SDK `useChat` or custom implementation
  - [x] WebSocket connection management:
    - [x] Connect on mount
    - [x] Reconnect on disconnect
    - [x] Handle connection errors
  - [x] Message handling — *See [04-frontend-spec.md#ai-sdk-protocol](../spec/04-frontend-spec.md)*:
    - [x] Parse AI SDK streaming format
    - [x] Handle text chunks (type 0)
    - [x] Handle tool calls (type 9)
    - [x] Handle tool results (type a)
    - [x] Handle finish (type d)
  - [x] State management:
    - [x] Update chat store on messages
    - [x] Update workspace store on file generation
  - [x] Return:
    - [x] `messages`: Message array
    - [x] `sendMessage()`: Send function
    - [x] `isLoading`: Loading state
    - [x] `error`: Error state
    - [x] `stop()`: Cancel response

---

## Phase 4.3: Pipeline Workspace - File Editors

> **Spec References:**
> - [04-frontend-spec.md#samplesheeteditor](../spec/04-frontend-spec.md) - Handsontable editor
> - [04-frontend-spec.md#configeditor](../spec/04-frontend-spec.md) - Monaco editor
> - [10-ux-spec.md#file-editor-states](../spec/10-ux-spec.md) - Editor states

### File Editor Panel Component

- [x] Create `frontend/components/editors/FileEditorPanel.tsx`:
  - [x] Tabbed interface — *See [10-ux-spec.md#file-editor-states](../spec/10-ux-spec.md)*:
    - [x] Samplesheet tab
    - [x] Config tab
  - [x] Tab badges:
    - [x] Modified indicator (dot)
    - [x] Error indicator (red)
    - [x] Valid indicator (green check)
  - [x] Content area for editors
  - [x] "Ask AI to modify" button

### Samplesheet Editor Component

> **Spec References:**
> - [04-frontend-spec.md#samplesheeteditor](../spec/04-frontend-spec.md) - Handsontable configuration
> - [10-ux-spec.md#file-editing](../spec/10-ux-spec.md) - Editing patterns

- [x] Create `frontend/components/editors/SamplesheetEditor.tsx` — *See [04-frontend-spec.md#samplesheeteditor](../spec/04-frontend-spec.md)*:
  - [x] Handsontable integration
  - [x] Configuration:
    - [x] Column headers from pipeline schema
    - [x] Column types (text, dropdown, numeric)
    - [x] Required column indicators
  - [x] Features — *See [10-ux-spec.md#file-editing](../spec/10-ux-spec.md)*:
    - [x] Cell editing with validation
    - [x] Copy/paste support
    - [x] Row add/remove
    - [x] Column resize
    - [x] Context menu
  - [x] Validation — *See [10-ux-spec.md#validation](../spec/10-ux-spec.md)*:
    - [x] Required fields not empty
    - [x] GCS path format validation
    - [x] Highlight invalid cells (red border)
  - [x] Export to CSV function
  - [x] Import from CSV function

- [x] Create `frontend/lib/handsontable/columnConfig.ts`:
  - [x] Define column configurations per pipeline
  - [x] nf-core/scrnaseq columns — *See [03-backend-spec.md#pipelineregistry](../spec/03-backend-spec.md)*:
    - [x] `sample` (text, required)
    - [x] `fastq_1` (text, required, GCS path)
    - [x] `fastq_2` (text, required, GCS path)
    - [x] `expected_cells` (numeric, optional, default 10000)

- [x] Create `frontend/lib/handsontable/validators.ts`:
  - [x] `validateRequired()`: Cell not empty
  - [x] `validateGcsPath()`: gs:// format
  - [x] `validateNumeric()`: Positive integer

### Config Editor Component

> **Spec References:**
> - [04-frontend-spec.md#configeditor](../spec/04-frontend-spec.md) - Monaco configuration

- [x] Create `frontend/components/editors/ConfigEditor.tsx` — *See [04-frontend-spec.md#configeditor](../spec/04-frontend-spec.md)*:
  - [x] Monaco Editor integration
  - [x] Configuration:
    - [x] Language: "groovy" or custom Nextflow mode
    - [x] Theme: Match app theme
    - [x] Line numbers: enabled
    - [x] Minimap: enabled
    - [x] Word wrap: off
  - [x] Features:
    - [x] Syntax highlighting
    - [x] Search/replace (Ctrl+F)
    - [x] Multiple cursors
    - [x] Bracket matching
  - [x] Read-only mode option

- [x] Create `frontend/lib/monaco/nextflowLanguage.ts`:
  - [x] Define Nextflow syntax highlighting:
    - [x] Keywords (params, process, workflow)
    - [x] Comments
    - [x] Strings
    - [x] Numbers

### Submit Panel Component

> **Spec References:**
> - [10-ux-spec.md#validation](../spec/10-ux-spec.md) - Validation display

- [x] Create `frontend/components/workspace/SubmitPanel.tsx` — *See [10-ux-spec.md#validation](../spec/10-ux-spec.md)*:
  - [x] Validation status display:
    - [x] Green checkmark if valid
    - [x] Error count if invalid
    - [x] Warning count with icon
  - [x] Error list (expandable):
    - [x] Error type and message
    - [x] Affected field/sample
    - [x] Fix action buttons
  - [x] Warning list (expandable)
  - [x] Validate button
  - [x] Submit Run button (disabled if errors)

### Validation Display Component

- [x] Create `frontend/components/workspace/ValidationDisplay.tsx`:
  - [x] Summarize validation results
  - [x] List errors with details — *See [10-ux-spec.md#error-handling-ux](../spec/10-ux-spec.md)*:
    - [x] Icon for error type
    - [x] Description
    - [x] Location (sample, field)
    - [x] Quick action (remove sample, fix value)
  - [x] List warnings
  - [x] Sample count and file verification summary

---

## Phase 4.4: Run Management Pages

> **Spec References:**
> - [04-frontend-spec.md#runlist](../spec/04-frontend-spec.md) - Run list component
> - [04-frontend-spec.md#rundetail](../spec/04-frontend-spec.md) - Run detail component
> - [10-ux-spec.md#run-status-indicators](../spec/10-ux-spec.md) - Status display

### Runs Page

- [ ] Create `frontend/app/runs/page.tsx` — *See [04-frontend-spec.md#page-structure](../spec/04-frontend-spec.md)*:
  - [ ] Page title and description
  - [ ] RunList component
  - [ ] Empty state when no runs — *See [10-ux-spec.md#empty-states](../spec/10-ux-spec.md)*

### Run List Component

> **Spec References:**
> - [04-frontend-spec.md#runlist](../spec/04-frontend-spec.md) - RunList specification

- [ ] Create `frontend/components/runs/RunList.tsx` — *See [04-frontend-spec.md#runlist](../spec/04-frontend-spec.md)*:
  - [ ] Fetch runs with TanStack Query
  - [ ] Sortable table columns:
    - [ ] Run ID
    - [ ] Pipeline
    - [ ] Status
    - [ ] Sample Count
    - [ ] Created At
    - [ ] Duration
  - [ ] Filtering:
    - [ ] Status dropdown
    - [ ] Pipeline dropdown
    - [ ] Date range picker
  - [ ] Pagination controls
  - [ ] Click row to navigate to detail

### Run Card Component

- [ ] Create `frontend/components/runs/RunCard.tsx`:
  - [ ] Alternative card-based display
  - [ ] Run summary:
    - [ ] Run ID and status badge
    - [ ] Pipeline name and version
    - [ ] Sample count
    - [ ] Created timestamp
  - [ ] Quick actions:
    - [ ] View details
    - [ ] Cancel (if running)

### Run Status Badge Component

> **Spec References:**
> - [10-ux-spec.md#run-status-indicators](../spec/10-ux-spec.md) - Status badge design

- [ ] Create `frontend/components/runs/RunStatusBadge.tsx` — *See [10-ux-spec.md#run-status-indicators](../spec/10-ux-spec.md)*:
  - [ ] Status-specific styling:
    - [ ] Pending: Gray, circle icon
    - [ ] Submitted: Blue, half-filled icon
    - [ ] Running: Blue, animated spinner
    - [ ] Completed: Green, checkmark
    - [ ] Failed: Red, X icon
    - [ ] Cancelled: Gray, stop icon
  - [ ] Tooltip with status description

### useRuns Hook

> **Spec References:**
> - [04-frontend-spec.md#useruns](../spec/04-frontend-spec.md) - Hook specification

- [ ] Create `frontend/hooks/useRuns.ts` — *See [04-frontend-spec.md#useruns](../spec/04-frontend-spec.md)*:
  - [ ] TanStack Query wrapper for runs
  - [ ] Pagination state management
  - [ ] Filter state management
  - [ ] Auto-refetch for active runs
  - [ ] Return:
    - [ ] `runs`: Run array
    - [ ] `isLoading`
    - [ ] `error`
    - [ ] `pagination`
    - [ ] `filters`
    - [ ] `setFilters()`

### Run Detail Page

- [ ] Create `frontend/app/runs/[id]/page.tsx` — *See [04-frontend-spec.md#page-structure](../spec/04-frontend-spec.md)*:
  - [ ] Fetch run by ID
  - [ ] Error handling for not found
  - [ ] Loading skeleton — *See [10-ux-spec.md#loading-states](../spec/10-ux-spec.md)*
  - [ ] RunDetail component

### Run Detail Component

> **Spec References:**
> - [04-frontend-spec.md#rundetail](../spec/04-frontend-spec.md) - RunDetail specification

- [ ] Create `frontend/components/runs/RunDetail.tsx` — *See [04-frontend-spec.md#rundetail](../spec/04-frontend-spec.md)*:
  - [ ] Header section:
    - [ ] Run ID with copy button
    - [ ] Status badge
    - [ ] Action buttons (Cancel, Re-run, Recover)
  - [ ] Tabbed content:
    - [ ] Overview tab
    - [ ] Logs tab
    - [ ] Files tab
    - [ ] Parameters tab

### Run Overview Tab

- [ ] Create `frontend/components/runs/RunOverview.tsx`:
  - [ ] Run metadata:
    - [ ] Pipeline and version
    - [ ] User who submitted
    - [ ] Created, started, completed timestamps
    - [ ] Duration
    - [ ] Sample count
  - [ ] Source information:
    - [ ] NGS runs
    - [ ] Project
  - [ ] Error information (if failed) — *See [10-ux-spec.md#error-handling-ux](../spec/10-ux-spec.md)*:
    - [ ] Error message
    - [ ] Failed task
    - [ ] Exit code
  - [ ] Metrics (if completed):
    - [ ] Total runtime
    - [ ] Tasks completed
    - [ ] CPU/memory usage

### Run Files Tab

- [ ] Create `frontend/components/runs/RunFiles.tsx`:
  - [ ] File browser tree — *See [06-data-model-spec.md#bucket-structure](../spec/06-data-model-spec.md)*:
    - [ ] inputs/ directory
    - [ ] results/ directory (if completed)
    - [ ] logs/ directory
  - [ ] File list:
    - [ ] File name
    - [ ] Size
    - [ ] Last modified
    - [ ] Download button
  - [ ] Generate signed URLs for download — *See [07-integration-spec.md#signed-url-generation](../spec/07-integration-spec.md)*

### Run Parameters Tab

- [ ] Create `frontend/components/runs/RunParameters.tsx`:
  - [ ] Display pipeline parameters as JSON/YAML
  - [ ] Syntax highlighted view
  - [ ] Copy button
  - [ ] Expandable sections for nested params

### SSE Integration for Real-time Updates

> **Spec References:**
> - [04-frontend-spec.md#userunevents](../spec/04-frontend-spec.md) - SSE hook
> - [07-integration-spec.md#sse-integration](../spec/07-integration-spec.md) - SSE implementation

- [ ] Create `frontend/hooks/useRunEvents.ts` — *See [04-frontend-spec.md#userunevents](../spec/04-frontend-spec.md)*:
  - [ ] EventSource connection to `/api/runs/{id}/events`
  - [ ] Handle SSE events — *See [07-integration-spec.md#sse-integration](../spec/07-integration-spec.md)*:
    - [ ] "status" event: Update run status
    - [ ] "done" event: Close connection
  - [ ] Reconnection logic
  - [ ] Return:
    - [ ] `status`: Current status
    - [ ] `isConnected`: Connection state

- [ ] Create `frontend/hooks/useRunStatus.ts` — *See [04-frontend-spec.md#userunstatus](../spec/04-frontend-spec.md)*:
  - [ ] Polling fallback for run status
  - [ ] Poll every 10 seconds for active runs
  - [ ] Stop polling on terminal states
  - [ ] Use with useRunEvents for reliability

---

## Phase 4.5: Log Viewer & Run Recovery UI

> **Spec References:**
> - [04-frontend-spec.md#runlogs](../spec/04-frontend-spec.md) - Log viewer component
> - [10-ux-spec.md#log-viewer](../spec/10-ux-spec.md) - Log viewer UX
> - [12-recovery-spec.md#frontend-workflow](../spec/12-recovery-spec.md) - Recovery UI

### Run Logs Tab Component

- [ ] Create `frontend/components/runs/RunLogs.tsx` — *See [04-frontend-spec.md#runlogs](../spec/04-frontend-spec.md)*:
  - [ ] Tab navigation:
    - [ ] Workflow Log
    - [ ] Task Logs
  - [ ] Download logs button

### Workflow Log Viewer Component

> **Spec References:**
> - [10-ux-spec.md#log-viewer](../spec/10-ux-spec.md) - Log viewer design

- [ ] Create `frontend/components/logs/WorkflowLogViewer.tsx` — *See [10-ux-spec.md#log-viewer](../spec/10-ux-spec.md)*:
  - [ ] Virtualized log display (react-window)
  - [ ] Auto-scroll to bottom option
  - [ ] Search/filter functionality — *See [10-ux-spec.md#log-viewer](../spec/10-ux-spec.md)*:
    - [ ] Text search input
    - [ ] Severity filter (INFO, WARN, ERROR)
  - [ ] LogLine component for each entry
  - [ ] Streaming support for active runs

### Log Line Component

- [ ] Create `frontend/components/logs/LogLine.tsx`:
  - [ ] Timestamp display
  - [ ] Log level badge (color-coded)
  - [ ] Message content with:
    - [ ] Syntax highlighting for paths
    - [ ] Monospace font
    - [ ] Wrap on small screens

### Task List Sidebar

- [ ] Create `frontend/components/logs/TaskList.tsx`:
  - [ ] List of tasks from trace.txt — *See [03-backend-spec.md#task-list](../spec/03-backend-spec.md)*
  - [ ] Task item display:
    - [ ] Task name
    - [ ] Process name
    - [ ] Status icon
    - [ ] Duration
  - [ ] Click to select task
  - [ ] Active task highlighting
  - [ ] Group by process (collapsible)

### Task Log Viewer Component

- [ ] Create `frontend/components/logs/TaskLogViewer.tsx`:
  - [ ] Selected task header:
    - [ ] Task name and process
    - [ ] Status and duration
    - [ ] Resource usage
  - [ ] Tabbed stdout/stderr display
  - [ ] LogLine rendering for content
  - [ ] Loading state while fetching

### Log Search Component

- [ ] Create `frontend/components/logs/LogSearch.tsx`:
  - [ ] Search input field
  - [ ] Match count indicator
  - [ ] Next/previous match buttons
  - [ ] Highlight matches in log view

### Log Download Component

- [ ] Create `frontend/components/logs/LogDownload.tsx`:
  - [ ] Download all logs as ZIP
  - [ ] Progress indicator
  - [ ] Include — *See [06-data-model-spec.md#bucket-structure](../spec/06-data-model-spec.md)*:
    - [ ] nextflow.log
    - [ ] trace.txt
    - [ ] timeline.html
    - [ ] report.html

### Recovery Modal Component

> **Spec References:**
> - [12-recovery-spec.md#frontend-workflow](../spec/12-recovery-spec.md) - Complete recovery UI spec
> - [12-recovery-spec.md#recovery-confirmation](../spec/12-recovery-spec.md) - Confirmation requirements

- [ ] Create `frontend/components/runs/RecoveryModal.tsx` — *See [12-recovery-spec.md#frontend-workflow](../spec/12-recovery-spec.md)*:
  - [ ] Modal dialog for recovery confirmation
  - [ ] Header: "Recover run with `-resume`"
  - [ ] Explanation text:
    - [ ] "This will re-run the workflow and reuse completed tasks from the previous work directory."
  - [ ] Confirmation checkbox — *See [12-recovery-spec.md#recovery-confirmation](../spec/12-recovery-spec.md)*
  - [ ] Optional fields:
    - [ ] Notes textarea
    - [ ] Override parameters (advanced toggle)
    - [ ] Override config (advanced toggle)
  - [ ] Cancel and Confirm buttons

- [ ] Create `frontend/components/runs/RecoveryAdvancedOptions.tsx`:
  - [ ] Expandable section for advanced options
  - [ ] Parameter override form:
    - [ ] Key-value pairs
    - [ ] Add/remove rows
  - [ ] Config override editor:
    - [ ] Monaco editor for config changes
    - [ ] Show diff from original

### usePipelines Hook

> **Spec References:**
> - [04-frontend-spec.md#usepipelines](../spec/04-frontend-spec.md) - Hook specification

- [ ] Create `frontend/hooks/usePipelines.ts` — *See [04-frontend-spec.md#usepipelines](../spec/04-frontend-spec.md)*:
  - [ ] TanStack Query wrapper for pipelines
  - [ ] Cache pipeline schema
  - [ ] Return:
    - [ ] `pipelines`: Pipeline list
    - [ ] `getPipeline(name)`: Get specific pipeline
    - [ ] `isLoading`
    - [ ] `error`

### Responsive Design Implementation

> **Spec References:**
> - [10-ux-spec.md#responsive-behavior](../spec/10-ux-spec.md) - Responsive breakpoints

- [ ] Implement responsive layouts — *See [10-ux-spec.md#responsive-behavior](../spec/10-ux-spec.md)*:
  - [ ] Desktop (1200px+):
    - [ ] Full two-panel workspace
    - [ ] Sidebar always visible
    - [ ] Side-by-side chat and editor
  - [ ] Tablet (768px-1199px):
    - [ ] Collapsible sidebar
    - [ ] Stacked/tabbed chat and editor
    - [ ] Touch-friendly targets
  - [ ] Mobile (<768px):
    - [ ] Single panel view
    - [ ] Bottom navigation
    - [ ] Simplified samplesheet (view-only)
    - [ ] Full chat functionality

---

## Key Deliverables Checklist

- [ ] Root layout with providers (QueryClient, HeroUI, Theme)
- [ ] Header, Sidebar, and MainLayout components
- [ ] Tailwind CSS with Arc brand colors
- [ ] HeroUI component library configured
- [ ] Zustand stores (workspace, chat, UI)
- [ ] TanStack Query with API client
- [ ] PipelineWorkspace with two-panel layout
- [ ] ChatPanel with:
  - [ ] MessageList and MessageBubble
  - [ ] Streaming message display
  - [ ] ToolIndicator with accordions
  - [ ] SuggestedPrompts
  - [ ] ChatInput
- [ ] useAgentChat hook with WebSocket
- [ ] FileEditorPanel with tabs
- [ ] SamplesheetEditor with Handsontable:
  - [ ] Column configuration
  - [ ] Cell validation
  - [ ] Copy/paste support
- [ ] ConfigEditor with Monaco:
  - [ ] Nextflow syntax highlighting
- [ ] SubmitPanel with validation display
- [ ] Runs page with RunList
- [ ] Run Detail page with:
  - [ ] Overview tab
  - [ ] Logs tab
  - [ ] Files tab
  - [ ] Parameters tab
- [ ] Run status badges and real-time updates (SSE)
- [ ] WorkflowLogViewer with streaming
- [ ] TaskList and TaskLogViewer
- [ ] Log search and download
- [ ] RecoveryModal with advanced options
- [ ] Responsive design (desktop, tablet, mobile)
