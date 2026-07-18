### 5. `agent_instructions.md`

```markdown
# Antigravity Agent Runtime Instructions (`agent_instructions.md`)

> **🚨 SYSTEM ROUTING DIRECTIVE FOR THE COGNITIVE AGENT:**
> You are the primary engineering agent for this workspace. You are tasked with writing clean, robust, multi-tenant B2B source code. You operate strictly under a Human-in-the-Loop (HITL) architecture and must adhere to the modular specifications defined below.

---

## 1. Pre-Task Initialization Context Sequence

Before executing any generation task, writing a single line of code, modifying endpoints, or debugging a component stack, you **MUST** read and cross-reference the workspace context files located in the root directory.

               COGNITIVE CONTEXT RETRIEVAL
┌────────────────────────────────────────────────────────────────┐
│ 1. Read 'project.md'       --> Verify MVP goals & value moat   │
├────────────────────────────────────────────────────────────────┤
│ 2. Read 'design.md'        --> Match structural schema layouts │
├────────────────────────────────────────────────────────────────┤
│ 3. Read 'system_arch.md'   --> Verify runtime isolation limits │
├────────────────────────────────────────────────────────────────┤
│ 4. Read 'api_contracts.md' --> Anchor types & payload contracts│
├────────────────────────────────────────────────────────────────┤
│ 5. Read 'dependency_guard.md' -> Ensure zero version changes   │
└────────────────────────────────────────────────────────────────┘


*   **Contract Lock:** If a task requires structural modifications to data payloads or new state variables, you must explicitly prompt the user to alter `api_contracts.md` **FIRST** before generating application files.
*   **Package Freeze:** You are absolutely banned from running `npm install`, `pip install`, or triggering package adjustments without explicit user verification in the chat interface.

---

## 2. Enforced Modular Coding Style Constraints

To protect the model's token limits and prevent massive, unmaintainable single-file blocks that cause syntax crashes, you must enforce a strict decoupled system design patterns model.

### A. The "Single Responsibility Principle" for Files
*   **Monolithic Files are Banned:** No individual source file shall exceed **200 lines of code**. If a service grows past this boundary, you must break its logic down into sub-modules.
*   **FastAPI Separation:** Separate your routes (`/routes/`), data validations (`/models/`), database interactions (`/services/`), and tool layouts (`/mcp_mocks/`) into clearly defined files. Do not mix database writes or vector manipulations directly inside route handler parameters.
*   **Next.js Components Isolation:** Keep custom layout editor features isolated into atomic React components inside the `/components/` folder. The primary entry page file (`page.tsx`) should function merely as a high-level wrapper shell.

### B. Functional Pureness & Context Isolation
*   **Explicit State Handlers:** All data transformations (e.g., converting live tool payloads into a structured text tree) must be built as pure, testable utility functions that accept inputs and return predictable outputs.
*   **Multi-Tenancy Guard:** When generating operations that access ChromaDB or MongoDB Atlas collections, you must explicitly type the query filters to accept a session tracking variable (`client_id`). **Never write an unsecured query function.**

---

## 3. Step-by-Step Code Generation Protocol

When instructed by the user to build out a new system block or route workflow, you must execute the implementation using this explicit sequence:

```text
                     CODE GENERATION PIPELINE
┌─────────────────────────────────────────────────────────────────┐
│ Step 1: Framework Layout Check                                  │
│ Describe the target code files and their directory paths first. │
├─────────────────────────────────────────────────────────────────┤
│ Step 2: Interface Validation                                    │
│ Match implementation targets against the active schemas in      │
│ api_contracts.md to verify structure before writing logic.      │
├─────────────────────────────────────────────────────────────────┘
4. Error Trapping and Handoff Directives
Strict Exception Handling: Every network boundary operation, database query, or JSON parsing loop must be wrapped inside structured exception handling blocks (try/except in Python, try/catch in TypeScript). Log descriptive contextual errors and always return clean error payload contracts to the interface client.

Validation Failure Management: If a generated model output deviates from a pre-defined schema, reject the process immediately, isolate the problem field, and return an informative message back up the stack.

Conflict Reporting: If a user requirement introduces a logical contradiction between the application configuration scripts or runtime constraints, stop generation loops instantly and lay out the exact architectural conflicts for the human supervisor to review.