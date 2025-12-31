# Sprint 6: Security, Testing, Polish & Launch

## Overview

This sprint implements security hardening, comprehensive testing, performance optimization, UX polish, and prepares the application for production launch.

## References

- [08-security-spec.md](../spec/08-security-spec.md) - Security requirements
- [09-deployment-spec.md](../spec/09-deployment-spec.md) - Production deployment
- [10-ux-spec.md](../spec/10-ux-spec.md) - UX polish

---

## Phase 6.1: Security Hardening

### IAP Integration

- [ ] Update `backend/utils/auth.py`:
  - [ ] Implement complete JWT verification:
    - [ ] Fetch Google's public keys
    - [ ] Verify JWT signature
    - [ ] Check `iss` claim is `https://cloud.google.com/iap`
    - [ ] Verify `aud` matches expected audience
    - [ ] Check `exp` is in the future
    - [ ] Confirm `hd` (hosted domain) is `arcinstitute.org`
  - [ ] Cache public keys with expiration
  - [ ] Handle key rotation gracefully

- [ ] Implement user context extraction:
  - [ ] Extract `email` from JWT claims
  - [ ] Extract `name` from JWT claims (or default to email)
  - [ ] Create User object with extracted claims
  - [ ] Store user context in request state

- [ ] Implement session management:
  - [ ] Validate session on each request
  - [ ] Handle session expiration gracefully
  - [ ] Support re-authentication prompts

### Development Bypass

- [ ] Update authentication for development mode:
  - [ ] Check `settings.debug` flag
  - [ ] Allow bypass when debug=True
  - [ ] Use configurable dev user email
  - [ ] Log bypass usage for awareness
  - [ ] Document security implications

### Authorization Rules

- [ ] Create `backend/utils/authorization.py`:
  - [ ] Implement `authorize_run_access()`:
    - [ ] Owner: Full access to run
    - [ ] Admin: Full access to all runs
    - [ ] Other: Read status only, no files/logs
  - [ ] Implement `is_admin()` check:
    - [ ] Check group membership or config
    - [ ] Cache admin status per session

- [ ] Apply authorization to run endpoints:
  - [ ] `GET /api/runs/{id}`: Owner or status-only
  - [ ] `GET /api/runs/{id}/files`: Owner or admin only
  - [ ] `GET /api/runs/{id}/logs`: Owner or admin only
  - [ ] `DELETE /api/runs/{id}`: Owner or admin only
  - [ ] `POST /api/runs/{id}/recover`: Owner or admin only

- [ ] Apply authorization to file downloads:
  - [ ] Verify run ownership before generating signed URLs
  - [ ] Log access attempts for audit

### Prompt Injection Protection

- [ ] Create `backend/utils/sanitization.py`:
  - [ ] Implement `sanitize_user_input()`:
    - [ ] Remove dangerous patterns:
      - [ ] "ignore previous instructions"
      - [ ] "disregard.*system prompt"
      - [ ] "you are now"
      - [ ] "act as"
      - [ ] "forget everything"
    - [ ] Replace with `[filtered]` marker
    - [ ] Log sanitization events

- [ ] Apply sanitization to chat input:
  - [ ] Sanitize before passing to agent
  - [ ] Sanitize tool parameters before execution
  - [ ] Log sanitized content for security review

### Audit Logging

- [ ] Create `backend/utils/audit.py`:
  - [ ] Define `AuditEvent` model:
    - [ ] `timestamp`
    - [ ] `severity`
    - [ ] `service`
    - [ ] `user_email`
    - [ ] `action`
    - [ ] `resource`
    - [ ] `request_id`
    - [ ] `ip_address`
    - [ ] `user_agent`
    - [ ] `details` (JSON)
  - [ ] Implement `log_audit_event()`:
    - [ ] Format as structured JSON
    - [ ] Write to Cloud Logging
    - [ ] Include request context

- [ ] Define auditable events:
  - [ ] `user.login` - User authenticated
  - [ ] `run.create` - Run created
  - [ ] `run.submit` - Run submitted
  - [ ] `run.cancel` - Run cancelled
  - [ ] `run.recover` - Run recovered
  - [ ] `run.complete` - Run completed
  - [ ] `run.fail` - Run failed
  - [ ] `auth.fail` - Authentication failed
  - [ ] `auth.bypass` - Dev bypass used
  - [ ] `rate_limit.hit` - Rate limit exceeded
  - [ ] `error.system` - System error occurred

- [ ] Implement audit logging in endpoints:
  - [ ] Add audit calls to all state-changing operations
  - [ ] Include relevant details in each event
  - [ ] Capture user context automatically

### VPC and Firewall Configuration

- [ ] Verify VPC configuration:
  - [ ] Cloud Run uses VPC connector
  - [ ] All egress through Cloud NAT
  - [ ] Private Google Access enabled

- [ ] Verify firewall rules:
  - [ ] Allow IAP ranges to Cloud Run
  - [ ] Allow internal VPC traffic
  - [ ] Default deny all other ingress

- [ ] Verify egress controls:
  - [ ] Allow `*.googleapis.com`
  - [ ] Allow `generativelanguage.googleapis.com`
  - [ ] Allow `aiplatform.googleapis.com`
  - [ ] Allow Benchling warehouse host
  - [ ] Allow `github.com` for pipeline downloads
  - [ ] Allow container registries

### Security Review

- [ ] Conduct code security review:
  - [ ] Check for SQL injection vulnerabilities
  - [ ] Check for XSS vulnerabilities
  - [ ] Check for CSRF vulnerabilities
  - [ ] Check for path traversal issues
  - [ ] Check for secret exposure

- [ ] Run vulnerability scanning:
  - [ ] Scan Python dependencies with `safety`
  - [ ] Scan npm dependencies with `npm audit`
  - [ ] Scan Docker images with `trivy`

- [ ] Address identified vulnerabilities:
  - [ ] Update vulnerable dependencies
  - [ ] Apply security patches
  - [ ] Document accepted risks

---

## Phase 6.2: Testing & Quality Assurance

### Backend Unit Tests

- [ ] Create `backend/tests/test_routes/`:
  - [ ] `test_runs.py`:
    - [ ] Test list runs with filters
    - [ ] Test get run by ID
    - [ ] Test create run
    - [ ] Test cancel run
    - [ ] Test recover run
    - [ ] Test authorization enforcement
  - [ ] `test_pipelines.py`:
    - [ ] Test list pipelines
    - [ ] Test get pipeline schema
  - [ ] `test_logs.py`:
    - [ ] Test get workflow log
    - [ ] Test get task list
    - [ ] Test get task logs
  - [ ] `test_health.py`:
    - [ ] Test health endpoint
    - [ ] Test readiness endpoint
    - [ ] Test degraded mode

- [ ] Create `backend/tests/test_services/`:
  - [ ] `test_runs_service.py`:
    - [ ] Test create run
    - [ ] Test update status
    - [ ] Test status transitions
    - [ ] Test recovery run creation
  - [ ] `test_storage_service.py`:
    - [ ] Test file upload
    - [ ] Test file download
    - [ ] Test signed URL generation
    - [ ] Test file existence check
  - [ ] `test_batch_service.py`:
    - [ ] Test job submission
    - [ ] Test status retrieval
    - [ ] Test job cancellation
  - [ ] `test_log_service.py`:
    - [ ] Test workflow log parsing
    - [ ] Test task list parsing
    - [ ] Test Cloud Logging queries

- [ ] Create `backend/tests/test_tools/`:
  - [ ] `test_ngs_tools.py`:
    - [ ] Test search_ngs_runs
    - [ ] Test get_ngs_run_samples
    - [ ] Test get_ngs_run_qc
    - [ ] Test get_fastq_paths
  - [ ] `test_benchling_tools.py`:
    - [ ] Test get_entities
    - [ ] Test get_entity_relationships
    - [ ] Test list_entries
  - [ ] `test_pipeline_tools.py`:
    - [ ] Test list_pipelines
    - [ ] Test get_pipeline_schema
  - [ ] `test_file_generation.py`:
    - [ ] Test generate_samplesheet
    - [ ] Test generate_config
    - [ ] Test validate_inputs
  - [ ] `test_submission_tools.py`:
    - [ ] Test submit_run (mock HITL)
    - [ ] Test cancel_run
    - [ ] Test clear_samplesheet

### Backend Integration Tests

- [ ] Create `backend/tests/integration/`:
  - [ ] `test_agent_workflow.py`:
    - [ ] Test sample discovery flow
    - [ ] Test samplesheet generation flow
    - [ ] Test complete submission flow
  - [ ] `test_benchling_integration.py`:
    - [ ] Test real Benchling warehouse queries
    - [ ] Skip if credentials not available
  - [ ] `test_batch_integration.py`:
    - [ ] Test job submission to real Batch
    - [ ] Skip if credentials not available

### Frontend Unit Tests

- [ ] Create `frontend/__tests__/components/`:
  - [ ] `Header.test.tsx`:
    - [ ] Test navigation links
    - [ ] Test user menu
    - [ ] Test theme toggle
  - [ ] `Sidebar.test.tsx`:
    - [ ] Test navigation items
    - [ ] Test active state
  - [ ] `ChatPanel.test.tsx`:
    - [ ] Test message rendering
    - [ ] Test input submission
    - [ ] Test loading state
  - [ ] `MessageBubble.test.tsx`:
    - [ ] Test user message styling
    - [ ] Test assistant message styling
    - [ ] Test tool indicator rendering
  - [ ] `SamplesheetEditor.test.tsx`:
    - [ ] Test column rendering
    - [ ] Test cell editing
    - [ ] Test validation display
  - [ ] `ConfigEditor.test.tsx`:
    - [ ] Test syntax highlighting
    - [ ] Test content changes
  - [ ] `RunList.test.tsx`:
    - [ ] Test run rendering
    - [ ] Test sorting
    - [ ] Test filtering
  - [ ] `RunDetail.test.tsx`:
    - [ ] Test tab navigation
    - [ ] Test status display
    - [ ] Test action buttons
  - [ ] `RecoveryModal.test.tsx`:
    - [ ] Test confirmation flow
    - [ ] Test advanced options

### Frontend Integration Tests

- [ ] Create `frontend/__tests__/integration/`:
  - [ ] `workspace.test.tsx`:
    - [ ] Test chat and editor interaction
    - [ ] Test file generation display
  - [ ] `runs.test.tsx`:
    - [ ] Test run list loading
    - [ ] Test run detail navigation

### End-to-End Testing

- [ ] Create E2E test suite:
  - [ ] Test sample discovery workflow:
    - [ ] Navigate to workspace
    - [ ] Enter sample search query
    - [ ] Verify samples displayed
    - [ ] Verify samplesheet generated
  - [ ] Test run submission workflow:
    - [ ] Generate samplesheet
    - [ ] Generate config
    - [ ] Click validate
    - [ ] Approve submission
    - [ ] Verify run created
  - [ ] Test run monitoring workflow:
    - [ ] Navigate to run detail
    - [ ] Verify status updates
    - [ ] View logs
  - [ ] Test recovery workflow:
    - [ ] Open failed run
    - [ ] Click recover
    - [ ] Confirm recovery
    - [ ] Verify new run created

### Performance Testing

- [ ] Create performance benchmarks:
  - [ ] API response time tests
  - [ ] WebSocket message throughput
  - [ ] Database query performance
  - [ ] Large samplesheet handling

- [ ] Identify and address bottlenecks:
  - [ ] Add database indexes if needed
  - [ ] Optimize slow queries
  - [ ] Add caching where appropriate

### Test Coverage

- [ ] Configure coverage reporting:
  - [ ] Backend: Use pytest-cov
  - [ ] Frontend: Use Jest coverage
  - [ ] Set minimum coverage thresholds

- [ ] Generate coverage reports:
  - [ ] Add to CI pipeline
  - [ ] Track coverage over time

---

## Phase 6.3: Polish & Production Launch

### Onboarding Flow

- [ ] Create `frontend/components/onboarding/WelcomeModal.tsx`:
  - [ ] Display on first visit
  - [ ] Brief intro to platform capabilities
  - [ ] Key feature highlights
  - [ ] Link to documentation
  - [ ] "Get Started" button
  - [ ] Dismissible, remember preference

- [ ] Implement guided first run:
  - [ ] Highlight suggested prompts
  - [ ] Tooltips on key UI elements
  - [ ] Step-by-step guidance
  - [ ] Success celebration on first submission

### Empty States

- [ ] Create `frontend/components/common/EmptyState.tsx`:
  - [ ] Generic empty state component
  - [ ] Icon, title, description
  - [ ] Optional action button

- [ ] Implement empty states:
  - [ ] No runs yet → Link to workspace
  - [ ] No files generated → Chat prompt suggestions
  - [ ] No samples found → Search suggestions
  - [ ] No logs available → Status explanation

### Loading States

- [ ] Create `frontend/components/common/LoadingSkeleton.tsx`:
  - [ ] Skeleton loading patterns
  - [ ] Match actual component layouts

- [ ] Implement loading states:
  - [ ] Run list skeleton
  - [ ] Run detail skeleton
  - [ ] Chat loading indicator
  - [ ] File loading states

### Toast Notifications

- [ ] Set up toast notification system:
  - [ ] Use HeroUI toast or react-hot-toast
  - [ ] Configure global toast provider

- [ ] Implement notifications:
  - [ ] Success: Run submitted, recovery started
  - [ ] Error: Submission failed, network error
  - [ ] Info: Status updates, background actions
  - [ ] Warning: Validation warnings

### Feedback Mechanisms

- [ ] Implement success feedback:
  - [ ] Toast for quick actions
  - [ ] Modal for major completions
  - [ ] Subtle animation on first run success

- [ ] Implement error feedback:
  - [ ] Inline errors appear immediately
  - [ ] Toast for transient errors
  - [ ] Modal for blocking errors
  - [ ] Clear recovery actions

- [ ] Implement progress feedback:
  - [ ] Loading spinners for short waits (<3s)
  - [ ] Progress bars for long operations
  - [ ] Status text for multi-step processes

### Accessibility Improvements

- [ ] Conduct accessibility audit:
  - [ ] Use axe-core or similar tool
  - [ ] Test with screen reader
  - [ ] Test keyboard navigation

- [ ] Fix accessibility issues:
  - [ ] Add missing ARIA labels
  - [ ] Fix focus management
  - [ ] Add skip links
  - [ ] Improve color contrast

- [ ] Implement keyboard navigation:
  - [ ] Tab between major sections
  - [ ] Arrow keys within lists/tables
  - [ ] Enter to activate buttons/links
  - [ ] Escape to close modals
  - [ ] Ctrl+/ to focus chat input

- [ ] Ensure color independence:
  - [ ] Status never by color alone
  - [ ] Icons accompany all status indicators
  - [ ] Sufficient contrast ratios (4.5:1+)

### Monitoring & Alerting

- [ ] Set up Cloud Monitoring dashboards:
  - [ ] Request rate and latency
  - [ ] Error rate by endpoint
  - [ ] Instance count and CPU/memory
  - [ ] Run submission rate
  - [ ] Run success/failure rate

- [ ] Configure alerting policies:
  - [ ] High error rate (>5% 5xx in 5 min): Critical
  - [ ] High latency (p95 >10s in 5 min): Warning
  - [ ] High instance count (>8): Warning
  - [ ] High memory usage (>80% for 10 min): Warning

- [ ] Set up log-based metrics:
  - [ ] Count of run submissions
  - [ ] Count of run failures
  - [ ] Count of auth failures

- [ ] Configure alert notification channels:
  - [ ] Email alerts
  - [ ] Slack integration (if applicable)
  - [ ] PagerDuty for critical alerts

### Documentation

- [ ] Create user documentation:
  - [ ] Getting started guide
  - [ ] How to discover samples
  - [ ] How to submit a run
  - [ ] How to monitor runs
  - [ ] How to recover failed runs
  - [ ] FAQ and troubleshooting

- [ ] Create API documentation:
  - [ ] OpenAPI/Swagger spec
  - [ ] Endpoint descriptions
  - [ ] Request/response examples
  - [ ] Authentication guide

- [ ] Create operational runbooks:
  - [ ] Deployment procedures
  - [ ] Rollback procedures
  - [ ] Incident response
  - [ ] Common troubleshooting

- [ ] Create developer documentation:
  - [ ] Architecture overview
  - [ ] Local development setup
  - [ ] Testing guide
  - [ ] Contributing guidelines

### Production Deployment

- [ ] Prepare production configuration:
  - [ ] Update production settings
  - [ ] Verify secrets in Secret Manager
  - [ ] Verify service account permissions
  - [ ] Verify IAP configuration

- [ ] Deploy to production:
  - [ ] Run production CI/CD pipeline
  - [ ] Verify deployment successful
  - [ ] Run smoke tests
  - [ ] Verify all integrations working

- [ ] Configure DNS:
  - [ ] Set up custom domain
  - [ ] Configure SSL certificate
  - [ ] Verify HTTPS working

### Gradual Rollout

- [ ] Identify pilot users:
  - [ ] Select small group of early adopters
  - [ ] Communicate launch timeline

- [ ] Conduct pilot rollout:
  - [ ] Enable access for pilot users
  - [ ] Gather feedback actively
  - [ ] Address critical issues immediately

- [ ] Expand rollout:
  - [ ] Open to broader user group
  - [ ] Monitor usage and errors
  - [ ] Collect feedback

- [ ] Full launch:
  - [ ] Announce to all users
  - [ ] Provide training resources
  - [ ] Monitor closely post-launch

---

## Key Deliverables Checklist

- [ ] IAP integration:
  - [ ] JWT verification
  - [ ] User context extraction
  - [ ] Session management
  - [ ] Development bypass
- [ ] Authorization rules:
  - [ ] Own runs vs. others' runs
  - [ ] Admin access
- [ ] Prompt injection protection
- [ ] Audit logging:
  - [ ] Structured format
  - [ ] All critical events logged
- [ ] VPC and firewall verified
- [ ] Security review completed
- [ ] Vulnerability scanning passed
- [ ] Backend unit tests:
  - [ ] Route tests
  - [ ] Service tests
  - [ ] Tool tests
- [ ] Frontend unit tests:
  - [ ] Component tests
  - [ ] Integration tests
- [ ] End-to-end tests:
  - [ ] Sample discovery workflow
  - [ ] Run submission workflow
  - [ ] Run monitoring workflow
  - [ ] Recovery workflow
- [ ] Performance testing completed
- [ ] Test coverage meets thresholds
- [ ] Onboarding flow:
  - [ ] Welcome modal
  - [ ] Guided first run
- [ ] Empty states implemented
- [ ] Loading states implemented
- [ ] Toast notifications working
- [ ] Accessibility audit passed
- [ ] WCAG 2.1 AA compliance
- [ ] Monitoring dashboards configured
- [ ] Alerting policies set up
- [ ] Documentation complete:
  - [ ] User guide
  - [ ] API docs
  - [ ] Runbooks
  - [ ] Developer docs
- [ ] Production deployment successful
- [ ] DNS and SSL configured
- [ ] Pilot rollout completed
- [ ] Full launch completed
