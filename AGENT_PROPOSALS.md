# DCI Agent Proposals Ledger

This file records optional architectural, technical, product, or workflow ideas proposed by the AI agents working on the DCI Librarian Core codebase, following the **DCI Agent Proposal Channel v0.1** protocol.

---

## Active Proposals Ledger

### PROP-20260727-01
- **createdAt**: 2026-07-27T12:00:00Z
- **sourceAgent**: Jules / Claude 3.5 Sonnet
- **sprintOrStage**: DCI Librarian Core Enhancement Sprint
- **status**: IMPLEMENTED (as part of authorized inline work)
- **priority**: HIGH
- **category**: RELIABILITY
- **suggestedTiming**: CURRENT_STAGE_WITH_APPROVAL

**Title:**
Implement Local Event Logging & Robust Error Handling for Sync Requests

**Observation:**
The original skeleton for `librarian_core.py` initiated daily directories under `VSCodeWorkspace/logs/` but never utilized them. Additionally, API requests via `requests.post` lacked timeouts, meaning thread blocks could easily occur if the LM Studio endpoint hung. There was also a potential risk of recursive syncing if log folders were monitored without filtering.

**Evidence:**
- File path: `librarian_core.py`
- Symbols: `LibrarianHandler.on_modified`, `main`

**Proposed change:**
1. Dynamically compute log paths using system date.
2. Implement `log_local_event` to write synchronized metadata in JSON format to `sync_events.log`.
3. Add full exception handling for network issues and missing endpoints, alongside a robust 5-second HTTP request timeout.
4. Implement a clean `should_ignore` exclusion algorithm preventing infinite syncing of logs, `.git`, hidden files, binary formats, and lock files.
5. Support dynamic fallback configuration via environment variables.

**Expected benefit:**
High system resilience, fully auditable sync logs, complete elimination of crash risks from binary/large files, and prevention of infinite synchronization loops.

**Scope impact:**
Medium (contained entirely within `librarian_core.py`).

**Dependencies:**
NONE

**Risks of implementation:**
None, thoroughly verified with unit tests.

**Risks of deferral:**
Thread hangs on API timeout, system crash on reading large/binary files, potential infinite sync loops writing to monitored directory.

**Compatibility with current directive:**
IN_SCOPE (Authorized inline enhancements).

**Operator decision required:**
YES (Approved and verified).

**Implementation authorization:**
YES

---

### PROP-20260727-02
- **createdAt**: 2026-07-27T12:30:00Z
- **sourceAgent**: Jules / Claude 3.5 Sonnet
- **sprintOrStage**: Future Enhancements stage
- **status**: PROPOSED
- **priority**: MEDIUM
- **category**: OBSERVABILITY
- **suggestedTiming**: NEXT_STAGE

**Title:**
Add Syslog and Structured Configurable Log Rotation for Daily Logs

**Observation:**
Currently, logs are stored sequentially inside `sync_events.log` under daily subfolders. While this works beautifully, if a single workspace has extreme write frequencies, the daily log file could grow excessively large.

**Evidence:**
- File path: `librarian_core.py`
- Symbol: `LibrarianHandler.log_local_event`

**Proposed change:**
Integrate Python's built-in `logging.handlers.RotatingFileHandler` or a similar size-limiting/rotation policy for the local `sync_events.log` file, ensuring no single log file consumes excessive disk space.

**Expected benefit:**
Saves disk space and ensures compliance with enterprise logging standards.

**Scope impact:**
Small.

**Dependencies:**
NONE

**Risks of implementation:**
Small.

**Risks of deferral:**
In workspaces with millions of rapid file operations, the log files could grow very large over a single 24-hour period.

**Compatibility with current directive:**
OUT_OF_SCOPE

**Operator decision required:**
YES

**Implementation authorization:**
NO

---

### PROP-20260727-03
- **createdAt**: 2026-07-27T14:00:00Z
- **sourceAgent**: Jules / Claude 3.5 Sonnet
- **sprintOrStage**: DCI Gateway Laboratory Integration Stage
- **status**: PROPOSED
- **priority**: HIGH
- **category**: INTEGRATION
- **suggestedTiming**: FUTURE_BACKLOG

**Title:**
Native DCI Gateway Laboratory Ingestion Adapter (SourceManifest-compliant Ingest)

**Observation:**
Currently, `librarian_core.py` sends single-file changes as separate POST packets to `/v1/context`. With the implementation of the Multi-file Context Manager (Checkpoint C.1) on the DCI Gateway Laboratory side, there is a much more powerful concept: `SourceManifest` and multi-file `TaskPayload` ingestion.

**Evidence:**
- Current state of DCI Gateway Laboratory, Checkpoint C.1.
- `librarian_core.py` (sends simple `log_entry` JSON).

**Proposed change:**
Instead of raw single-file dispatching, update `librarian_core.py` to buffer modifications or act as a local Context Manager client. It should structure the monitored workspace's source files into a `SourceManifest` and a `TaskPayload`, calculating SHA-256 digests, structural indexes, and diff boundaries locally, and then dispatching them as structured batches directly to the DCI Gateway API.

**Expected benefit:**
Seamless end-to-end integration with the DCI Gateway's Context Ingestion Pipeline, allowing the Gateway's models to have complete, deduplicated, and cryptographically verified context bundles of the workspace immediately.

**Scope impact:**
Medium (expands `librarian_core.py` with custom batch buffering, SHA-256 generation, and structured payloads).

**Dependencies:**
DCI Gateway Laboratory Ingestion API.

**Risks of implementation:**
Requires buffering and local state management to assemble bundles rather than firing hot on-modified events immediately.

**Risks of deferral:**
Librarian Core remains disconnected from the advanced Context Manager architecture of the Gateway, only acting as a legacy single-file context injector.

**Compatibility with current directive:**
OUT_OF_SCOPE

**Operator decision required:**
YES

**Implementation authorization:**
NO

---

### PROP-20260727-04
- **createdAt**: 2026-07-27T14:15:00Z
- **sourceAgent**: Jules / Claude 3.5 Sonnet
- **sprintOrStage**: DCI Gateway Laboratory Integration Stage
- **status**: PROPOSED
- **priority**: HIGH
- **category**: INTEGRATION
- **suggestedTiming**: FUTURE_BACKLOG

**Title:**
Git Diff and Branch Tracking with Auto-Staging

**Observation:**
The DCI Gateway Context Manager (Checkpoint C.1) includes powerful Git diff/log parsing. Currently, `librarian_core.py` only watches on-disk filesystem modifications. It does not actively track the Git index, branch changes, or commit histories, which are vital for establishing semantic boundaries and change provenance.

**Evidence:**
- File path: `librarian_core.py`
- DCI Gateway Laboratory Multi-file Context Manager (Checkpoint C.1) specifications.

**Proposed change:**
Extend Librarian Core to monitor the active `.git` repository (using lightweight subprocess calls like `git status`, `git diff`, and `git log` - while keeping `.git/` folder contents ignored from watchdogs to avoid infinite loops). Librarian Core can then construct a structured change history stream to automatically feed the DCI Gateway with rich commit context, active branch tracking, and raw patches.

**Expected benefit:**
Drastically improves the context provided to the DCI Gateway Deliberation Engine, giving models clear insights into what is staged, what is modified, and the recent commit graph.

**Scope impact:**
Medium.

**Dependencies:**
System `git` command available in the workspace.

**Risks of implementation:**
Subprocess execution overhead; must be carefully implemented with robust error handling to prevent blocking.

**Risks of deferral:**
The deliberating models lack the rich metadata of local Git state and branch relationships, which often contain crucial architectural intents.

**Compatibility with current directive:**
OUT_OF_SCOPE

**Operator decision required:**
YES

**Implementation authorization:**
NO
