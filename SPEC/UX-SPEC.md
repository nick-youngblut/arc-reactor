# Arc Reactor - User Experience Specification

## Overview

This document defines the user experience principles, workflows, and interface design for the Arc Reactor. The platform is designed for wet lab scientists who need to run bioinformatics pipelines without deep computational expertise.

## Design Principles

### 1. Progressive Disclosure

Reveal complexity only when needed. Start simple, allow users to dive deeper.

| Level | User Sees | Example |
|-------|-----------|---------|
| **Surface** | High-level actions | "Run scRNA-seq analysis" |
| **Intermediate** | Key parameters | Genome, protocol, aligner |
| **Advanced** | Full configuration | Complete nextflow.config |

### 2. Conversational First

The AI assistant is the primary interface, not a secondary feature.

- Users describe what they want in natural language
- AI handles the translation to technical configuration
- Manual editing available but not required

### 3. Safety Through Visibility

Users should always understand what will happen before it happens.

- Preview all generated files before submission
- Clear validation with actionable error messages
- Confirmation step with cost/time estimates

### 4. Forgiveness

Make it easy to recover from mistakes.

- Undo support for edits
- Re-run with modifications
- Clear history of all runs

## User Personas

### Primary: Research Associate (Sarah)

**Background:**
- PhD in molecular biology
- 3 years wet lab experience
- Comfortable with spreadsheets, basic command line
- Runs 2-3 sequencing experiments per month

**Goals:**
- Get analysis results without waiting for computational support
- Understand what parameters affect her results
- Track all her analyses for publications

**Pain Points:**
- Command line feels intimidating
- Configuration files are confusing
- Hard to remember what parameters she used last time

### Secondary: Staff Scientist (Michael)

**Background:**
- Postdoc + 5 years industry experience
- Moderate computational skills (R, basic Python)
- Runs complex experiments with many samples
- Often helps junior lab members

**Goals:**
- Fine-tune pipeline parameters for specific experiments
- Run batch analyses across multiple projects
- Maintain reproducibility for publications

**Pain Points:**
- Existing tools too rigid or too complex
- Hard to share configurations with collaborators

## Core User Flows

### Flow 1: First-Time Run (10 minutes)

```
1. User lands on workspace
   └── Sees welcome message + suggested prompts

2. User types: "Run scRNA-seq on my samples from last week"
   └── AI searches Benchling, presents matching runs

3. User selects run
   └── AI asks clarifying questions (genome, protocol)

4. AI generates files
   └── Samplesheet and config appear in editor panels

5. User reviews files
   └── Can edit directly or ask AI for changes

6. User clicks Submit
   └── Validation runs, confirmation dialog shown

7. Run starts
   └── User redirected to run detail view
```

### Flow 2: Re-run with Modifications

```
1. User views previous run in history
   └── Clicks "Re-run with changes"

2. Workspace populated with previous config
   └── Chat shows context from original run

3. User requests changes
   └── "Add 10 more samples from pool XYZ"

4. AI modifies samplesheet
   └── User reviews changes

5. Submit new run
```

### Flow 3: Troubleshooting Failed Run

```
1. User sees failed run notification
   └── Clicks to view details

2. Error summary shown
   └── "3 samples failed: missing R2 files"

3. User asks AI for help
   └── AI explains issue and suggests fixes

4. User chooses resolution
   └── Remove samples, fix in Benchling, or retry
```

## Interface Components

### Workspace Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│  Arc Reactor                            sarah@arc... ▼    │
├──────────┬──────────────────────────────────────────────────────────┤
│          │  Pipeline: [nf-core/scrnaseq ▼]  Version: [2.7.1 ▼]      │
│  Sidebar │──────────────────────────────────────────────────────────│
│          │                                                          │
│  • Work- │  ┌─────────────────┐  ┌──────────────────────────────┐   │
│    space │  │                 │  │  [samplesheet] [config]      │   │
│          │  │   Chat Panel    │  │                              │   │
│  • Runs  │  │                 │  │     File Editor Panel        │   │
│          │  │                 │  │                              │   │
│          │  │                 │  │                              │   │
│          │  │                 │  │                              │   │
│          │  │  [Input...]     │  │                              │   │
│          │  └─────────────────┘  └──────────────────────────────┘   │
│          │──────────────────────────────────────────────────────────│
│          │  ⚠ 2 warnings found          [Validate] [Submit Run →]   │
└──────────┴──────────────────────────────────────────────────────────┘
```

### Chat Panel States

| State | Display |
|-------|---------|
| **Empty** | Welcome message + suggested prompts |
| **Loading** | Typing indicator with tool status |
| **Tool executing** | Tool name badge + spinner |
| **Message** | User/assistant message bubbles |
| **Error** | Red error banner with retry option |

### File Editor States

| State | Display |
|-------|---------|
| **Empty** | Placeholder with instructions |
| **Populated** | Active tab with content |
| **Modified** | Dot indicator on tab |
| **Error** | Red highlight on invalid cells/lines |
| **Validated** | Green checkmark |

### Run Status Indicators

| Status | Icon | Color | Description |
|--------|------|-------|-------------|
| Pending | ○ | Gray | Created, not submitted |
| Submitted | ◐ | Blue | Sent to Batch, queued |
| Running | ● | Blue (animated) | Actively executing |
| Completed | ✓ | Green | Finished successfully |
| Failed | ✗ | Red | Finished with error |
| Cancelled | ⊘ | Gray | User cancelled |

## Interaction Patterns

### Chat Interactions

**Message Submission:**
- Enter key sends message
- Shift+Enter for newline
- Disabled while AI is responding

**Tool Display:**
- Tool calls shown as collapsible cards
- Show tool name, brief status
- Expandable for full details

**File References:**
- Generated files announced in chat
- "View in editor" links
- Auto-scroll to relevant tab

### File Editing

**Samplesheet (Handsontable):**
- Click cell to edit
- Tab/arrow keys for navigation
- Ctrl+C/V for copy/paste
- Right-click for context menu
- Drag to select ranges

**Config (Monaco):**
- Standard code editor shortcuts
- Syntax highlighting
- Line numbers
- Search/replace (Ctrl+F)

**AI Modification:**
- "Ask AI to modify" button
- Opens chat with file context
- Changes highlighted when applied

### Validation

**Inline Validation:**
- Red borders on invalid cells
- Tooltip on hover with error
- Error count in footer

**Pre-submit Validation:**
- Full validation on Submit click
- Modal with all errors/warnings
- Cannot submit with errors
- Can submit with warnings (confirmation)

## Error Handling UX

### Error Categories

| Category | Example | User Action |
|----------|---------|-------------|
| **Fixable** | Missing FASTQ file | Remove sample or check Benchling |
| **Configuration** | Invalid parameter | Edit config or ask AI |
| **System** | Benchling unavailable | Retry later |
| **Fatal** | Pipeline crash | Contact support |

### Error Message Format

```
┌─────────────────────────────────────────────────────────────────┐
│  ✗ Validation Failed                                            │
│                                                                 │
│  2 errors must be fixed before submission:                      │
│                                                                 │
│  1. Missing file                                                │
│     Sample: LPS-012                                             │
│     File: gs://arc-ngs-data/NR-2024-0156/LPS-012_R2.fastq.gz    │
│     → [Remove sample] [Check Benchling]                         │
│                                                                 │
│  2. Invalid parameter                                           │
│     Parameter: genome                                           │
│     Value: "hg38" (should be "GRCh38" or "GRCm39")              │
│     → [Fix in config] [Ask AI to fix]                           │
│                                                                 │
│  1 warning (can proceed):                                       │
│                                                                 │
│  ⚠ Low expected cells                                           │
│    3 samples have expected_cells < 5000                         │
│                                                                 │
│                                              [Cancel] [Fix All] │
└─────────────────────────────────────────────────────────────────┘
```

## Empty States

### No Runs Yet

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│                    📊 No runs yet                               │
│                                                                 │
│     Start your first analysis in the Workspace tab              │
│                                                                 │
│                    [Go to Workspace]                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### No Files Generated

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│                    📄 No files yet                              │
│                                                                 │
│     Chat with the assistant to find your samples                │
│     and generate pipeline configuration files                   │
│                                                                 │
│     Try: "Find my samples from last week"                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Loading States

### Chat Loading

```
Assistant: [●●● typing...]

Tool executing: search_ngs_runs
└── Searching Benchling for your samples...
```

### Run Submission

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│                    ⏳ Submitting run...                         │
│                                                                 │
│     ✓ Uploading samplesheet                                     │
│     ✓ Uploading configuration                                   │
│     ● Creating batch job...                                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Accessibility

### Keyboard Navigation

| Key | Action |
|-----|--------|
| Tab | Move between major sections |
| Arrow keys | Navigate within lists/tables |
| Enter | Activate buttons/links |
| Escape | Close modals/cancel |
| Ctrl+/ | Focus chat input |

### Screen Reader Support

- All interactive elements labeled
- Status changes announced
- Tables have proper headers
- Form errors associated with fields

### Color Independence

- Status never indicated by color alone
- Icons accompany all status indicators
- Sufficient contrast ratios (4.5:1+)

## Responsive Behavior

### Desktop (1200px+)

- Full two-panel layout
- Sidebar always visible
- Side-by-side chat and editor

### Tablet (768px-1199px)

- Collapsible sidebar
- Stacked chat and editor (tabbed)
- Touch-friendly targets

### Mobile (< 768px)

- Single panel view
- Bottom navigation
- Simplified editor (view-only for samplesheet)
- Full chat functionality

## Onboarding

### First Visit

1. **Welcome modal** (dismissible)
   - Brief intro to platform capabilities
   - Link to documentation
   - "Get Started" button

2. **Guided first run** (optional)
   - Highlighted suggested prompts
   - Tooltips on key UI elements
   - Success celebration on first submission

### Contextual Help

- `?` icon opens help panel
- Tooltips on hover for complex elements
- "Learn more" links to documentation
- AI can explain any feature

## Feedback Mechanisms

### Success Feedback

- Toast notifications for quick actions
- Success modals for major completions
- Confetti animation for first run (subtle)

### Error Feedback

- Inline errors appear immediately
- Toast for transient errors
- Modal for blocking errors
- Clear recovery actions

### Progress Feedback

- Loading spinners for short waits (<3s)
- Progress bars for long operations
- Status text for multi-step processes

## Performance Expectations

| Action | Expected Time | Feedback |
|--------|---------------|----------|
| Page load | < 2s | Skeleton loading |
| Chat response start | < 1s | Typing indicator |
| Tool execution | 2-10s | Tool status card |
| File generation | < 5s | Immediate display |
| Validation | < 3s | Loading state |
| Submission | < 5s | Progress modal |