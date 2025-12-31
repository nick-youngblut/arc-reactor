# Sprint 6: Security, Testing, Polish & Launch

## Overview

This sprint implements security hardening, comprehensive testing, performance optimization, UX polish, and prepares the application for production launch.

## References

- [08-security-spec.md](../spec/08-security-spec.md) - Security requirements
- [09-deployment-spec.md](../spec/09-deployment-spec.md) - Production deployment
- [10-ux-spec.md](../spec/10-ux-spec.md) - UX polish

---

## Phase 6.1: Security Hardening

> **Spec References:**
> - [08-security-spec.md#authentication](../spec/08-security-spec.md) - Authentication requirements
> - [08-security-spec.md#authorization](../spec/08-security-spec.md) - Authorization rules
> - [07-integration-spec.md#gcp-iap-integration](../spec/07-integration-spec.md) - IAP implementation

### IAP Integration

> **Spec References:**
> - [07-integration-spec.md#jwt-verification](../spec/07-integration-spec.md) - JWT verification process
> - [08-security-spec.md#jwt-token-handling](../spec/08-security-spec.md) - Token validation rules

- [ ] Update `backend/utils/auth.py` — *See [07-integration-spec.md#jwt-verification](../spec/07-integration-spec.md)*:
  - [ ] Implement complete JWT verification:
    - [ ] Fetch Google's public keys
    - [ ] Verify JWT signature
    - [ ] Check `iss` claim is `https://cloud.google.com/iap`
    - [ ] Verify `aud` matches expected audience
    - [ ] Check `exp` is in the future
    - [ ] Confirm `hd` (hosted domain) is `arcinstitute.org` — *See [08-security-spec.md#jwt-token-handling](../spec/08-security-spec.md)*
  - [ ] Cache public keys with expiration
  - [ ] Handle key rotation gracefully

- [ ] Implement user context extraction — *See [07-integration-spec.md#user-context](../spec/07-integration-spec.md)*:
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
  - [ ] Log bypass usage for awareness — *See [08-security-spec.md#audit-logging](../spec/08-security-spec.md)*
  - [ ] Document security implications

### Authorization Rules

> **Spec References:**
> - [08-security-spec.md#role-based-access-control](../spec/08-security-spec.md) - RBAC roles
> - [08-security-spec.md#resource-level-access](../spec/08-security-spec.md) - Resource permissions
> - [03-backend-spec.md#authorization](../spec/03-backend-spec.md) - API access rules

- [ ] Create `backend/utils/authorization.py` — *See [08-security-spec.md#authorization](../spec/08-security-spec.md)*:
  - [ ] Implement `authorize_run_access()` — *See [08-security-spec.md#resource-level-access](../spec/08-security-spec.md)*:
    - [ ] Owner: Full access to run
    - [ ] Admin: Full access to all runs
    - [ ] Other: Read status only, no files/logs
  - [ ] Implement `is_admin()` check:
    - [ ] Check group membership or config
    - [ ] Cache admin status per session

- [ ] Apply authorization to run endpoints — *See [03-backend-spec.md#authorization](../spec/03-backend-spec.md)*:
  - [ ] `GET /api/runs/{id}`: Owner or status-only
  - [ ] `GET /api/runs/{id}/files`: Owner or admin only
  - [ ] `GET /api/runs/{id}/logs`: Owner or admin only
  - [ ] `DELETE /api/runs/{id}`: Owner or admin only
  - [ ] `POST /api/runs/{id}/recover`: Owner or admin only

- [ ] Apply authorization to file downloads:
  - [ ] Verify run ownership before generating signed URLs
  - [ ] Log access attempts for audit — *See [08-security-spec.md#audit-logging](../spec/08-security-spec.md)*

### Prompt Injection Protection

> **Spec References:**
> - [08-security-spec.md#prompt-injection-protection](../spec/08-security-spec.md) - Sanitization rules
> - [05-agentic-features-spec.md#security](../spec/05-agentic-features-spec.md) - AI security

- [ ] Create `backend/utils/sanitization.py` — *See [08-security-spec.md#prompt-injection-protection](../spec/08-security-spec.md)*:
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
  - [ ] Sanitize tool parameters before execution — *See [08-security-spec.md#tool-execution-safety](../spec/08-security-spec.md)*
  - [ ] Log sanitized content for security review

### Audit Logging

> **Spec References:**
> - [08-security-spec.md#audit-logging](../spec/08-security-spec.md) - Complete audit requirements
> - [08-security-spec.md#log-format](../spec/08-security-spec.md) - Structured log format

- [ ] Create `backend/utils/audit.py` — *See [08-security-spec.md#audit-logging](../spec/08-security-spec.md)*:
  - [ ] Define `AuditEvent` model — *See [08-security-spec.md#log-format](../spec/08-security-spec.md)*:
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

- [ ] Define auditable events — *See [08-security-spec.md#auditable-events](../spec/08-security-spec.md)*:
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

> **Spec References:**
> - [08-security-spec.md#network-security](../spec/08-security-spec.md) - VPC configuration
> - [08-security-spec.md#firewall-rules](../spec/08-security-spec.md) - Firewall rules
> - [08-security-spec.md#egress-controls](../spec/08-security-spec.md) - Egress destinations

- [ ] Verify VPC configuration — *See [08-security-spec.md#network-security](../spec/08-security-spec.md)*:
  - [ ] Cloud Run uses VPC connector
  - [ ] All egress through Cloud NAT
  - [ ] Private Google Access enabled

- [ ] Verify firewall rules — *See [08-security-spec.md#firewall-rules](../spec/08-security-spec.md)*:
  - [ ] Allow IAP ranges to Cloud Run
  - [ ] Allow internal VPC traffic
  - [ ] Default deny all other ingress

- [ ] Verify egress controls — *See [08-security-spec.md#egress-controls](../spec/08-security-spec.md)*:
  - [ ] Allow `*.googleapis.com`
  - [ ] Allow `generativelanguage.googleapis.com`
  - [ ] Allow `aiplatform.googleapis.com`
  - [ ] Allow Benchling warehouse host
  - [ ] Allow `github.com` for pipeline downloads
  - [ ] Allow container registries

### Security Review

> **Spec References:**
> - [08-security-spec.md#application-security](../spec/08-security-spec.md) - Security checklist

- [ ] Conduct code security review — *See [08-security-spec.md#application-security](../spec/08-security-spec.md)*:
  - [ ] Check for SQL injection vulnerabilities — *See [08-security-spec.md#sql-injection-prevention](../spec/08-security-spec.md)*
  - [ ] Check for XSS vulnerabilities — *See [08-security-spec.md#xss-prevention](../spec/08-security-spec.md)*
  - [ ] Check for CSRF vulnerabilities — *See [08-security-spec.md#csrf-prevention](../spec/08-security-spec.md)*
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

> **Spec References:**
> - [03-backend-spec.md#testing](../spec/03-backend-spec.md) - Backend testing approach
> - [04-frontend-spec.md#testing](../spec/04-frontend-spec.md) - Frontend testing approach

### Backend Unit Tests

- [ ] Create `backend/tests/test_routes/`:
  - [ ] `test_runs.py` — *See [03-backend-spec.md#run-management-endpoints](../spec/03-backend-spec.md)*:
    - [ ] Test list runs with filters
    - [ ] Test get run by ID
    - [ ] Test create run
    - [ ] Test cancel run
    - [ ] Test recover run
    - [ ] Test authorization enforcement
  - [ ] `test_pipelines.py` — *See [03-backend-spec.md#pipeline-endpoints](../spec/03-backend-spec.md)*:
    - [ ] Test list pipelines
    - [ ] Test get pipeline schema
  - [ ] `test_logs.py` — *See [03-backend-spec.md#log-endpoints](../spec/03-backend-spec.md)*:
    - [ ] Test get workflow log
    - [ ] Test get task list
    - [ ] Test get task logs
  - [ ] `test_health.py` — *See [03-backend-spec.md#health-endpoints](../spec/03-backend-spec.md)*:
    - [ ] Test health endpoint
    - [ ] Test readiness endpoint
    - [ ] Test degraded mode

- [ ] Create `backend/tests/test_services/`:
  - [ ] `test_runs_service.py` — *See [03-backend-spec.md#runstoreservice](../spec/03-backend-spec.md)*:
    - [ ] Test create run
    - [ ] Test update status
    - [ ] Test status transitions
    - [ ] Test recovery run creation
  - [ ] `test_storage_service.py` — *See [03-backend-spec.md#storageservice](../spec/03-backend-spec.md)*:
    - [ ] Test file upload
    - [ ] Test file download
    - [ ] Test signed URL generation
    - [ ] Test file existence check
  - [ ] `test_batch_service.py` — *See [03-backend-spec.md#batchservice](../spec/03-backend-spec.md)*:
    - [ ] Test job submission
    - [ ] Test status retrieval
    - [ ] Test job cancellation
  - [ ] `test_log_service.py` — *See [03-backend-spec.md#logservice](../spec/03-backend-spec.md)*:
    - [ ] Test workflow log parsing
    - [ ] Test task list parsing
    - [ ] Test Cloud Logging queries

- [ ] Create `backend/tests/test_tools/`:
  - [ ] `test_ngs_tools.py` — *See [05-agentic-features-spec.md#ngs-data-discovery-tools](../spec/05-agentic-features-spec.md)*:
    - [ ] Test search_ngs_runs
    - [ ] Test get_ngs_run_samples
    - [ ] Test get_ngs_run_qc
    - [ ] Test get_fastq_paths
  - [ ] `test_benchling_tools.py` — *See [05-agentic-features-spec.md#benchling-discovery-tools](../spec/05-agentic-features-spec.md)*:
    - [ ] Test get_entities
    - [ ] Test get_entity_relationships
    - [ ] Test list_entries
  - [ ] `test_pipeline_tools.py` — *See [05-agentic-features-spec.md#pipeline-info-tools](../spec/05-agentic-features-spec.md)*:
    - [ ] Test list_pipelines
    - [ ] Test get_pipeline_schema
  - [ ] `test_file_generation.py` — *See [05-agentic-features-spec.md#file-generation-tools](../spec/05-agentic-features-spec.md)*:
    - [ ] Test generate_samplesheet
    - [ ] Test generate_config
    - [ ] Test validate_inputs
  - [ ] `test_submission_tools.py` — *See [05-agentic-features-spec.md#validation-submission-tools](../spec/05-agentic-features-spec.md)*:
    - [ ] Test submit_run (mock HITL)
    - [ ] Test cancel_run
    - [ ] Test clear_samplesheet

### Backend Integration Tests

- [ ] Create `backend/tests/integration/`:
  - [ ] `test_agent_workflow.py`:
    - [ ] Test sample discovery flow — *See [10-ux-spec.md#first-time-run](../spec/10-ux-spec.md)*
    - [ ] Test samplesheet generation flow
    - [ ] Test complete submission flow
  - [ ] `test_benchling_integration.py`:
    - [ ] Test real Benchling warehouse queries
    - [ ] Skip if credentials not available
  - [ ] `test_batch_integration.py`:
    - [ ] Test job submission to real Batch
    - [ ] Skip if credentials not available

### Frontend Unit Tests

> **Spec References:**
> - [04-frontend-spec.md#testing](../spec/04-frontend-spec.md) - Jest configuration

- [ ] Create `frontend/__tests__/components/`:
  - [ ] `Header.test.tsx`:
    - [ ] Test navigation links
    - [ ] Test user menu
    - [ ] Test theme toggle
  - [ ] `Sidebar.test.tsx`:
    - [ ] Test navigation items
    - [ ] Test active state
  - [ ] `ChatPanel.test.tsx` — *See [04-frontend-spec.md#chatpanel](../spec/04-frontend-spec.md)*:
    - [ ] Test message rendering
    - [ ] Test input submission
    - [ ] Test loading state
  - [ ] `MessageBubble.test.tsx`:
    - [ ] Test user message styling
    - [ ] Test assistant message styling
    - [ ] Test tool indicator rendering
  - [ ] `SamplesheetEditor.test.tsx` — *See [04-frontend-spec.md#samplesheeteditor](../spec/04-frontend-spec.md)*:
    - [ ] Test column rendering
    - [ ] Test cell editing
    - [ ] Test validation display
  - [ ] `ConfigEditor.test.tsx` — *See [04-frontend-spec.md#configeditor](../spec/04-frontend-spec.md)*:
    - [ ] Test syntax highlighting
    - [ ] Test content changes
  - [ ] `RunList.test.tsx` — *See [04-frontend-spec.md#runlist](../spec/04-frontend-spec.md)*:
    - [ ] Test run rendering
    - [ ] Test sorting
    - [ ] Test filtering
  - [ ] `RunDetail.test.tsx` — *See [04-frontend-spec.md#rundetail](../spec/04-frontend-spec.md)*:
    - [ ] Test tab navigation
    - [ ] Test status display
    - [ ] Test action buttons
  - [ ] `RecoveryModal.test.tsx` — *See [12-recovery-spec.md#frontend-workflow](../spec/12-recovery-spec.md)*:
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

> **Spec References:**
> - [10-ux-spec.md#core-user-flows](../spec/10-ux-spec.md) - User flow testing

- [ ] Create E2E test suite — *See [10-ux-spec.md#core-user-flows](../spec/10-ux-spec.md)*:
  - [ ] Test sample discovery workflow — *See [10-ux-spec.md#first-time-run](../spec/10-ux-spec.md)*:
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
  - [ ] Test recovery workflow — *See [10-ux-spec.md#troubleshooting-failed-run](../spec/10-ux-spec.md)*:
    - [ ] Open failed run
    - [ ] Click recover
    - [ ] Confirm recovery
    - [ ] Verify new run created

### Performance Testing

> **Spec References:**
> - [10-ux-spec.md#performance-expectations](../spec/10-ux-spec.md) - Latency targets

- [ ] Create performance benchmarks — *See [10-ux-spec.md#performance-expectations](../spec/10-ux-spec.md)*:
  - [ ] API response time tests
  - [ ] WebSocket message throughput
  - [ ] Database query performance
  - [ ] Large samplesheet handling

- [ ] Identify and address bottlenecks:
  - [ ] Add database indexes if needed
  - [ ] Optimize slow queries
  - [ ] Add caching where appropriate — *See [07-integration-spec.md#caching-strategy](../spec/07-integration-spec.md)*

### Test Coverage

- [ ] Configure coverage reporting:
  - [ ] Backend: Use pytest-cov
  - [ ] Frontend: Use Jest coverage
  - [ ] Set minimum coverage thresholds

- [ ] Generate coverage reports:
  - [ ] Add to CI pipeline — *See [09-deployment-spec.md#github-actions-workflow](../spec/09-deployment-spec.md)*
  - [ ] Track coverage over time

---

## Phase 6.3: Polish & Production Launch

> **Spec References:**
> - [10-ux-spec.md#onboarding](../spec/10-ux-spec.md) - Onboarding experience
> - [10-ux-spec.md#empty-states](../spec/10-ux-spec.md) - Empty state design
> - [10-ux-spec.md#loading-states](../spec/10-ux-spec.md) - Loading state design
> - [09-deployment-spec.md#production-deployment](../spec/09-deployment-spec.md) - Deployment process

### Onboarding Flow

> **Spec References:**
> - [10-ux-spec.md#onboarding](../spec/10-ux-spec.md) - Complete onboarding spec

- [ ] Create `frontend/components/onboarding/WelcomeModal.tsx` — *See [10-ux-spec.md#onboarding](../spec/10-ux-spec.md)*:
  - [ ] Display on first visit
  - [ ] Brief intro to platform capabilities
  - [ ] Key feature highlights
  - [ ] Link to documentation
  - [ ] "Get Started" button
  - [ ] Dismissible, remember preference

- [ ] Implement guided first run — *See [10-ux-spec.md#guided-first-run](../spec/10-ux-spec.md)*:
  - [ ] Highlight suggested prompts
  - [ ] Tooltips on key UI elements
  - [ ] Step-by-step guidance
  - [ ] Success celebration on first submission

### Empty States

> **Spec References:**
> - [10-ux-spec.md#empty-states](../spec/10-ux-spec.md) - Empty state design

- [ ] Create `frontend/components/common/EmptyState.tsx` — *See [10-ux-spec.md#empty-states](../spec/10-ux-spec.md)*:
  - [ ] Generic empty state component
  - [ ] Icon, title, description
  - [ ] Optional action button

- [ ] Implement empty states:
  - [ ] No runs yet → Link to workspace
  - [ ] No files generated → Chat prompt suggestions
  - [ ] No samples found → Search suggestions
  - [ ] No logs available → Status explanation

### Loading States

> **Spec References:**
> - [10-ux-spec.md#loading-states](../spec/10-ux-spec.md) - Loading state design

- [ ] Create `frontend/components/common/LoadingSkeleton.tsx` — *See [10-ux-spec.md#loading-states](../spec/10-ux-spec.md)*:
  - [ ] Skeleton loading patterns
  - [ ] Match actual component layouts

- [ ] Implement loading states:
  - [ ] Run list skeleton
  - [ ] Run detail skeleton
  - [ ] Chat loading indicator
  - [ ] File loading states

### Toast Notifications

> **Spec References:**
> - [10-ux-spec.md#feedback-mechanisms](../spec/10-ux-spec.md) - Feedback patterns

- [ ] Set up toast notification system — *See [10-ux-spec.md#feedback-mechanisms](../spec/10-ux-spec.md)*:
  - [ ] Use HeroUI toast or react-hot-toast
  - [ ] Configure global toast provider

- [ ] Implement notifications:
  - [ ] Success: Run submitted, recovery started
  - [ ] Error: Submission failed, network error
  - [ ] Info: Status updates, background actions
  - [ ] Warning: Validation warnings

### Feedback Mechanisms

> **Spec References:**
> - [10-ux-spec.md#feedback-mechanisms](../spec/10-ux-spec.md) - Complete feedback spec

- [ ] Implement success feedback — *See [10-ux-spec.md#success-feedback](../spec/10-ux-spec.md)*:
  - [ ] Toast for quick actions
  - [ ] Modal for major completions
  - [ ] Subtle animation on first run success

- [ ] Implement error feedback — *See [10-ux-spec.md#error-feedback](../spec/10-ux-spec.md)*:
  - [ ] Inline errors appear immediately
  - [ ] Toast for transient errors
  - [ ] Modal for blocking errors
  - [ ] Clear recovery actions

- [ ] Implement progress feedback — *See [10-ux-spec.md#progress-feedback](../spec/10-ux-spec.md)*:
  - [ ] Loading spinners for short waits (<3s)
  - [ ] Progress bars for long operations
  - [ ] Status text for multi-step processes

### Accessibility Improvements

> **Spec References:**
> - [10-ux-spec.md#accessibility](../spec/10-ux-spec.md) - Accessibility requirements
> - [04-frontend-spec.md#accessibility](../spec/04-frontend-spec.md) - WCAG compliance

- [ ] Conduct accessibility audit — *See [10-ux-spec.md#accessibility](../spec/10-ux-spec.md)*:
  - [ ] Use axe-core or similar tool
  - [ ] Test with screen reader
  - [ ] Test keyboard navigation

- [ ] Fix accessibility issues:
  - [ ] Add missing ARIA labels
  - [ ] Fix focus management
  - [ ] Add skip links
  - [ ] Improve color contrast

- [ ] Implement keyboard navigation — *See [10-ux-spec.md#keyboard-navigation](../spec/10-ux-spec.md)*:
  - [ ] Tab between major sections
  - [ ] Arrow keys within lists/tables
  - [ ] Enter to activate buttons/links
  - [ ] Escape to close modals
  - [ ] Ctrl+/ to focus chat input

- [ ] Ensure color independence — *See [10-ux-spec.md#color-independence](../spec/10-ux-spec.md)*:
  - [ ] Status never by color alone
  - [ ] Icons accompany all status indicators
  - [ ] Sufficient contrast ratios (4.5:1+)

### Monitoring & Alerting

> **Spec References:**
> - [09-deployment-spec.md#monitoring-alerting](../spec/09-deployment-spec.md) - Monitoring setup
> - [09-deployment-spec.md#alerting-policies](../spec/09-deployment-spec.md) - Alert configuration

- [ ] Set up Cloud Monitoring dashboards — *See [09-deployment-spec.md#monitoring-alerting](../spec/09-deployment-spec.md)*:
  - [ ] Request rate and latency
  - [ ] Error rate by endpoint
  - [ ] Instance count and CPU/memory
  - [ ] Run submission rate
  - [ ] Run success/failure rate

- [ ] Configure alerting policies — *See [09-deployment-spec.md#alerting-policies](../spec/09-deployment-spec.md)*:
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
  - [ ] Getting started guide — *See [10-ux-spec.md#onboarding](../spec/10-ux-spec.md)*
  - [ ] How to discover samples
  - [ ] How to submit a run
  - [ ] How to monitor runs
  - [ ] How to recover failed runs — *See [12-recovery-spec.md](../spec/12-recovery-spec.md)*
  - [ ] FAQ and troubleshooting

- [ ] Create API documentation:
  - [ ] OpenAPI/Swagger spec — *See [03-backend-spec.md#api-endpoints](../spec/03-backend-spec.md)*
  - [ ] Endpoint descriptions
  - [ ] Request/response examples
  - [ ] Authentication guide

- [ ] Create operational runbooks — *See [09-deployment-spec.md#deployment-procedures](../spec/09-deployment-spec.md)*:
  - [ ] Deployment procedures
  - [ ] Rollback procedures — *See [09-deployment-spec.md#rollback-procedure](../spec/09-deployment-spec.md)*
  - [ ] Incident response — *See [08-security-spec.md#incident-response](../spec/08-security-spec.md)*
  - [ ] Common troubleshooting

- [ ] Create developer documentation:
  - [ ] Architecture overview — *See [02-architecture-overview.md](../spec/02-architecture-overview.md)*
  - [ ] Local development setup
  - [ ] Testing guide
  - [ ] Contributing guidelines

### Production Deployment

> **Spec References:**
> - [09-deployment-spec.md#production-deployment](../spec/09-deployment-spec.md) - Deployment process
> - [09-deployment-spec.md#environment-configuration](../spec/09-deployment-spec.md) - Environment setup

- [ ] Prepare production configuration — *See [09-deployment-spec.md#environment-configuration](../spec/09-deployment-spec.md)*:
  - [ ] Update production settings
  - [ ] Verify secrets in Secret Manager
  - [ ] Verify service account permissions
  - [ ] Verify IAP configuration

- [ ] Deploy to production — *See [09-deployment-spec.md#standard-deployment](../spec/09-deployment-spec.md)*:
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
  - [ ] Select small group of early adopters — *See [10-ux-spec.md#user-personas](../spec/10-ux-spec.md)*
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
