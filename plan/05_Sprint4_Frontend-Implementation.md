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

- [ ] Update `frontend/app/layout.tsx` — *See [04-frontend-spec.md#root-layout](../spec/04-frontend-spec.md)*:
  - [ ] Configure HTML structure with proper lang attribute
  - [ ] Add metadata (title, description, favicon)
  - [ ] Wrap with QueryClientProvider (TanStack Query) — *See [04-frontend-spec.md#tanstack-query](../spec/04-frontend-spec.md)*
  - [ ] Wrap with HeroUI provider
  - [ ] Add ThemeProvider for dark/light mode
  - [ ] Add global error boundary

- [ ] Create `frontend/lib/queryClient.ts`:
  - [ ] Configure QueryClient with defaults:
    - [ ] Stale time: 5 minutes
    - [ ] Retry: 3 times with backoff
    - [ ] Refetch on window focus: true
  - [ ] Export QueryClientProvider setup

### Header Component

> **Spec References:**
> - [10-ux-spec.md#interface-components](../spec/10-ux-spec.md) - Component layout

- [ ] Create `frontend/components/Header.tsx`:
  - [ ] Display Arc Reactor logo and title
  - [ ] Navigation links (Workspace, Runs)
  - [ ] User menu dropdown:
    - [ ] User avatar/initials
    - [ ] User email
    - [ ] Settings link
    - [ ] Logout action
  - [ ] Theme toggle (dark/light mode)

### Sidebar Component

- [ ] Create `frontend/components/Sidebar.tsx`:
  - [ ] Navigation items with icons:
    - [ ] Workspace (chat + editors)
    - [ ] Runs (run history)
  - [ ] Active state highlighting
  - [ ] Collapsible on smaller screens — *See [10-ux-spec.md#responsive-behavior](../spec/10-ux-spec.md)*
  - [ ] Arc Institute branding at bottom

### Main Layout Component

> **Spec References:**
> - [10-ux-spec.md#workspace-layout](../spec/10-ux-spec.md) - Layout structure

- [ ] Create `frontend/components/MainLayout.tsx` — *See [10-ux-spec.md#workspace-layout](../spec/10-ux-spec.md)*:
  - [ ] Integrate Header and Sidebar
  - [ ] Main content area with routing
  - [ ] Responsive grid layout — *See [10-ux-spec.md#responsive-behavior](../spec/10-ux-spec.md)*:
    - [ ] Desktop: Sidebar + main content
    - [ ] Tablet: Collapsible sidebar
    - [ ] Mobile: Bottom navigation

### Tailwind CSS Configuration

> **Spec References:**
> - [04-frontend-spec.md#styling](../spec/04-frontend-spec.md) - CSS configuration

- [ ] Update `tailwind.config.js` — *See [04-frontend-spec.md#styling](../spec/04-frontend-spec.md)*:
  - [ ] Define Arc brand colors:
    - [ ] Primary (arc-blue)
    - [ ] Secondary
    - [ ] Success, Warning, Error, Info
    - [ ] Neutral grays
  - [ ] Configure dark mode (class-based)
  - [ ] Add custom spacing and typography
  - [ ] Configure HeroUI plugin

- [ ] Update `frontend/styles/globals.css`:
  - [ ] Tailwind directives
  - [ ] Base styles and resets
  - [ ] Custom utility classes
  - [ ] CSS variables for theming

### HeroUI Configuration

- [ ] Create `frontend/lib/heroui.ts`:
  - [ ] Configure HeroUI theme
  - [ ] Set default component variants
  - [ ] Configure modal/toast defaults

### Zustand Stores

> **Spec References:**
> - [04-frontend-spec.md#state-management](../spec/04-frontend-spec.md) - Store definitions
> - [04-frontend-spec.md#workspace-store](../spec/04-frontend-spec.md) - Workspace state

- [ ] Create `frontend/stores/workspaceStore.ts` — *See [04-frontend-spec.md#workspace-store](../spec/04-frontend-spec.md)*:
  - [ ] State:
    - [ ] `selectedPipeline`: Pipeline name
    - [ ] `selectedVersion`: Pipeline version
    - [ ] `samplesheet`: CSV content
    - [ ] `config`: Config content
    - [ ] `validationResult`: Validation state
    - [ ] `isDirty`: Unsaved changes flag
  - [ ] Actions:
    - [ ] `setPipeline()`
    - [ ] `setSamplesheet()`
    - [ ] `setConfig()`
    - [ ] `clearWorkspace()`
    - [ ] `setValidationResult()`

- [ ] Create `frontend/stores/chatStore.ts` — *See [04-frontend-spec.md#chat-store](../spec/04-frontend-spec.md)*:
  - [ ] State:
    - [ ] `messages`: Chat message array
    - [ ] `isLoading`: Agent responding flag
    - [ ] `threadId`: Conversation thread ID
    - [ ] `error`: Error state
  - [ ] Actions:
    - [ ] `addMessage()`
    - [ ] `updateLastMessage()`
    - [ ] `clearMessages()`
    - [ ] `setError()`

- [ ] Create `frontend/stores/uiStore.ts`:
  - [ ] State:
    - [ ] `sidebarOpen`: Sidebar visibility
    - [ ] `activeTab`: Current file tab
    - [ ] `theme`: Light/dark mode
  - [ ] Actions:
    - [ ] `toggleSidebar()`
    - [ ] `setActiveTab()`
    - [ ] `setTheme()`

### TanStack Query Setup

> **Spec References:**
> - [04-frontend-spec.md#api-client](../spec/04-frontend-spec.md) - API client configuration
> - [04-frontend-spec.md#relative-paths](../spec/04-frontend-spec.md) - Relative path requirement

- [ ] Create `frontend/lib/api.ts` — *See [04-frontend-spec.md#api-client](../spec/04-frontend-spec.md)*:
  - [ ] Configure Axios instance:
    - [ ] Base URL: relative paths (e.g., `/api`) — *See [04-frontend-spec.md#relative-paths](../spec/04-frontend-spec.md)*
    - [ ] Request interceptors for auth
    - [ ] Response interceptors for errors
  - [ ] Export typed API functions:
    - [ ] `fetchRuns()`
    - [ ] `fetchRun(id)`
    - [ ] `createRun()`
    - [ ] `cancelRun(id)`
    - [ ] `recoverRun(id, options)` — *See [12-recovery-spec.md#frontend-workflow](../spec/12-recovery-spec.md)*
    - [ ] `fetchPipelines()`
    - [ ] `fetchPipeline(name)`

---

## Phase 4.2: Pipeline Workspace - Chat Panel

> **Spec References:**
> - [04-frontend-spec.md#pipelineworkspace](../spec/04-frontend-spec.md) - Workspace container
> - [04-frontend-spec.md#chatpanel](../spec/04-frontend-spec.md) - Chat component
> - [10-ux-spec.md#chat-panel-states](../spec/10-ux-spec.md) - Chat UX states

### PipelineWorkspace Container

- [ ] Create `frontend/components/workspace/PipelineWorkspace.tsx` — *See [04-frontend-spec.md#pipelineworkspace](../spec/04-frontend-spec.md)*:
  - [ ] Two-column layout — *See [10-ux-spec.md#workspace-layout](../spec/10-ux-spec.md)*:
    - [ ] Left: ChatPanel (40% width)
    - [ ] Right: FileEditorPanel (60% width)
  - [ ] Pipeline selector in header:
    - [ ] Dropdown for pipeline selection
    - [ ] Version dropdown
  - [ ] Status bar at bottom:
    - [ ] Validation status indicators
    - [ ] Submit Run button
  - [ ] Responsive: Stack panels on smaller screens

### Chat Panel Component

> **Spec References:**
> - [04-frontend-spec.md#chatpanel](../spec/04-frontend-spec.md) - Complete chat specification
> - [10-ux-spec.md#chat-panel-states](../spec/10-ux-spec.md) - Chat states

- [ ] Create `frontend/components/chat/ChatPanel.tsx` — *See [04-frontend-spec.md#chatpanel](../spec/04-frontend-spec.md)*:
  - [ ] Panel header with title and clear button
  - [ ] MessageList component
  - [ ] ChatInput at bottom
  - [ ] Loading state indicator — *See [10-ux-spec.md#loading-states](../spec/10-ux-spec.md)*

### Message List Component

- [ ] Create `frontend/components/chat/MessageList.tsx`:
  - [ ] Scrollable message container
  - [ ] Auto-scroll to bottom on new messages
  - [ ] Map messages to MessageBubble components
  - [ ] Handle empty state with welcome message — *See [10-ux-spec.md#empty-states](../spec/10-ux-spec.md)*

### Message Bubble Component

> **Spec References:**
> - [04-frontend-spec.md#messagebubble](../spec/04-frontend-spec.md) - Message rendering
> - [04-frontend-spec.md#tool-indicator](../spec/04-frontend-spec.md) - Tool call display

- [ ] Create `frontend/components/chat/MessageBubble.tsx` — *See [04-frontend-spec.md#messagebubble](../spec/04-frontend-spec.md)*:
  - [ ] Differentiate user vs assistant messages:
    - [ ] User: Right-aligned, primary color
    - [ ] Assistant: Left-aligned, secondary color
  - [ ] Render markdown content
  - [ ] Support streaming text display
  - [ ] Render tool calls as ToolIndicator — *See [04-frontend-spec.md#tool-indicator](../spec/04-frontend-spec.md)*
  - [ ] Display message timestamp

### Tool Indicator Component

> **Spec References:**
> - [04-frontend-spec.md#toolindicator](../spec/04-frontend-spec.md) - Tool call display
> - [05-agentic-features-spec.md#tool-output-handling](../spec/05-agentic-features-spec.md) - Tool output format

- [ ] Create `frontend/components/chat/ToolIndicator.tsx` — *See [04-frontend-spec.md#toolindicator](../spec/04-frontend-spec.md)*:
  - [ ] Collapsible accordion for tool calls
  - [ ] Tool name badge with icon
  - [ ] Status indicator (pending, running, completed, error)
  - [ ] Expandable details:
    - [ ] Tool parameters (formatted JSON/YAML)
    - [ ] Tool result summary
  - [ ] Distinct styling per tool category

### Streaming Message Display

- [ ] Create `frontend/components/chat/StreamingMessage.tsx`:
  - [ ] Accept streaming text content
  - [ ] Display with typing cursor effect
  - [ ] Handle markdown rendering incrementally
  - [ ] Smooth text reveal animation

### Suggested Prompts Component

> **Spec References:**
> - [10-ux-spec.md#onboarding](../spec/10-ux-spec.md) - First-time user experience

- [ ] Create `frontend/components/chat/SuggestedPrompts.tsx` — *See [10-ux-spec.md#onboarding](../spec/10-ux-spec.md)*:
  - [ ] Display when chat is empty
  - [ ] Predefined prompt suggestions:
    - [ ] "Find my samples from last week"
    - [ ] "Search for SspArc0050"
    - [ ] "Run scRNA-seq analysis"
    - [ ] "Show available pipelines"
  - [ ] Click to populate chat input
  - [ ] Fade out after first message

### Chat Input Component

> **Spec References:**
> - [10-ux-spec.md#chat-interaction](../spec/10-ux-spec.md) - Chat input behavior

- [ ] Create `frontend/components/chat/ChatInput.tsx` — *See [10-ux-spec.md#chat-interaction](../spec/10-ux-spec.md)*:
  - [ ] Textarea with auto-resize
  - [ ] Submit button
  - [ ] Keyboard handling — *See [10-ux-spec.md#keyboard-navigation](../spec/10-ux-spec.md)*:
    - [ ] Enter to send
    - [ ] Shift+Enter for newline
  - [ ] Disabled state while loading
  - [ ] Character count indicator

### useAgentChat Hook

> **Spec References:**
> - [04-frontend-spec.md#useagentchat](../spec/04-frontend-spec.md) - Chat hook specification
> - [04-frontend-spec.md#ai-sdk-protocol](../spec/04-frontend-spec.md) - Streaming protocol

- [ ] Create `frontend/hooks/useAgentChat.ts` — *See [04-frontend-spec.md#useagentchat](../spec/04-frontend-spec.md)*:
  - [ ] Integrate with Vercel AI SDK `useChat` or custom implementation
  - [ ] WebSocket connection management:
    - [ ] Connect on mount
    - [ ] Reconnect on disconnect
    - [ ] Handle connection errors
  - [ ] Message handling — *See [04-frontend-spec.md#ai-sdk-protocol](../spec/04-frontend-spec.md)*:
    - [ ] Parse AI SDK streaming format
    - [ ] Handle text chunks (type 0)
    - [ ] Handle tool calls (type 9)
    - [ ] Handle tool results (type a)
    - [ ] Handle finish (type d)
  - [ ] State management:
    - [ ] Update chat store on messages
    - [ ] Update workspace store on file generation
  - [ ] Return:
    - [ ] `messages`: Message array
    - [ ] `sendMessage()`: Send function
    - [ ] `isLoading`: Loading state
    - [ ] `error`: Error state
    - [ ] `stop()`: Cancel response

---

## Phase 4.3: Pipeline Workspace - File Editors

> **Spec References:**
> - [04-frontend-spec.md#samplesheeteditor](../spec/04-frontend-spec.md) - Handsontable editor
> - [04-frontend-spec.md#configeditor](../spec/04-frontend-spec.md) - Monaco editor
> - [10-ux-spec.md#file-editor-states](../spec/10-ux-spec.md) - Editor states

### File Editor Panel Component

- [ ] Create `frontend/components/editors/FileEditorPanel.tsx`:
  - [ ] Tabbed interface — *See [10-ux-spec.md#file-editor-states](../spec/10-ux-spec.md)*:
    - [ ] Samplesheet tab
    - [ ] Config tab
  - [ ] Tab badges:
    - [ ] Modified indicator (dot)
    - [ ] Error indicator (red)
    - [ ] Valid indicator (green check)
  - [ ] Content area for editors
  - [ ] "Ask AI to modify" button

### Samplesheet Editor Component

> **Spec References:**
> - [04-frontend-spec.md#samplesheeteditor](../spec/04-frontend-spec.md) - Handsontable configuration
> - [10-ux-spec.md#file-editing](../spec/10-ux-spec.md) - Editing patterns

- [ ] Create `frontend/components/editors/SamplesheetEditor.tsx` — *See [04-frontend-spec.md#samplesheeteditor](../spec/04-frontend-spec.md)*:
  - [ ] Handsontable integration
  - [ ] Configuration:
    - [ ] Column headers from pipeline schema
    - [ ] Column types (text, dropdown, numeric)
    - [ ] Required column indicators
  - [ ] Features — *See [10-ux-spec.md#file-editing](../spec/10-ux-spec.md)*:
    - [ ] Cell editing with validation
    - [ ] Copy/paste support
    - [ ] Row add/remove
    - [ ] Column resize
    - [ ] Context menu
  - [ ] Validation — *See [10-ux-spec.md#validation](../spec/10-ux-spec.md)*:
    - [ ] Required fields not empty
    - [ ] GCS path format validation
    - [ ] Highlight invalid cells (red border)
  - [ ] Export to CSV function
  - [ ] Import from CSV function

- [ ] Create `frontend/lib/handsontable/columnConfig.ts`:
  - [ ] Define column configurations per pipeline
  - [ ] nf-core/scrnaseq columns — *See [03-backend-spec.md#pipelineregistry](../spec/03-backend-spec.md)*:
    - [ ] `sample` (text, required)
    - [ ] `fastq_1` (text, required, GCS path)
    - [ ] `fastq_2` (text, required, GCS path)
    - [ ] `expected_cells` (numeric, optional, default 10000)

- [ ] Create `frontend/lib/handsontable/validators.ts`:
  - [ ] `validateRequired()`: Cell not empty
  - [ ] `validateGcsPath()`: gs:// format
  - [ ] `validateNumeric()`: Positive integer

### Config Editor Component

> **Spec References:**
> - [04-frontend-spec.md#configeditor](../spec/04-frontend-spec.md) - Monaco configuration

- [ ] Create `frontend/components/editors/ConfigEditor.tsx` — *See [04-frontend-spec.md#configeditor](../spec/04-frontend-spec.md)*:
  - [ ] Monaco Editor integration
  - [ ] Configuration:
    - [ ] Language: "groovy" or custom Nextflow mode
    - [ ] Theme: Match app theme
    - [ ] Line numbers: enabled
    - [ ] Minimap: enabled
    - [ ] Word wrap: off
  - [ ] Features:
    - [ ] Syntax highlighting
    - [ ] Search/replace (Ctrl+F)
    - [ ] Multiple cursors
    - [ ] Bracket matching
  - [ ] Read-only mode option

- [ ] Create `frontend/lib/monaco/nextflowLanguage.ts`:
  - [ ] Define Nextflow syntax highlighting:
    - [ ] Keywords (params, process, workflow)
    - [ ] Comments
    - [ ] Strings
    - [ ] Numbers

### Submit Panel Component

> **Spec References:**
> - [10-ux-spec.md#validation](../spec/10-ux-spec.md) - Validation display

- [ ] Create `frontend/components/workspace/SubmitPanel.tsx` — *See [10-ux-spec.md#validation](../spec/10-ux-spec.md)*:
  - [ ] Validation status display:
    - [ ] Green checkmark if valid
    - [ ] Error count if invalid
    - [ ] Warning count with icon
  - [ ] Error list (expandable):
    - [ ] Error type and message
    - [ ] Affected field/sample
    - [ ] Fix action buttons
  - [ ] Warning list (expandable)
  - [ ] Validate button
  - [ ] Submit Run button (disabled if errors)

### Validation Display Component

- [ ] Create `frontend/components/workspace/ValidationDisplay.tsx`:
  - [ ] Summarize validation results
  - [ ] List errors with details — *See [10-ux-spec.md#error-handling-ux](../spec/10-ux-spec.md)*:
    - [ ] Icon for error type
    - [ ] Description
    - [ ] Location (sample, field)
    - [ ] Quick action (remove sample, fix value)
  - [ ] List warnings
  - [ ] Sample count and file verification summary

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
