# Define Requirements

I am defining requirements for a new piece of code to be added to this codebase.

Do the following (in exactly this order):

1. Gather context

- Ask my permission to read `README.md` (if it exists)
- Ask my permission to read the files in `docs/**/*` (if they exist)
- Ask my permission to see the layout of the whole codebase (``)
- Ask my permission to read the files in `.current_agent_context/**/*` (if this folder exists)
- If you deem them necessary, ask my permission to delegate context gathering tasks to codebase researcher subagents (see [Guide to using Codebase Research Subagents](#guide-to-using-codebase-research-subagents))

2. fill in the template from the context yourself
3. we discuss each section (with your recommendations you discovered/wrote)
4. you ask me where to write it to

## Requirements Template Sections

This template enforces structure that helps avoid common requirement deficits:

✅ **Completeness** — covers drivers, constraints, functional and non-functional requirements
✅ **Clarity** — separate glossary and data dictionary reduces ambiguity
✅ **Testability** — it encourages a “fit criterion” for each requirement so you can measure whether it’s satisfied (not just stated)
✅ **Traceability** — each requirement can link back to business goals and stakeholders

### 1) **Project Needs (Project Drivers)**

These explain _why_ you’re doing the work.

1. **The Purpose of the Project**
   - Business problem / opportunity being addressed
   - Why this solution matters

2. **Stakeholders**
   - Client(s), customers, users, any party with interest

3. **Relevant Facts and Assumptions**
   - Conditions assumed true for this project
   - Environmental or domain facts that influence requirements

### 2) **Project Requirements**

This is the core section where you write requirements _from high level to granular_.

#### 2a) **Project Constraints**

Limits within which requirements must exist:

- Mandated constraints
- Naming conventions & terminology
- Technology constraints
- Budget/time boundaries
- External system interfaces (if relevant)

#### 2b) **Functional Requirements**

These describe _what the system must do_:

1. **Scope of the Work** – business area or problem boundary
2. **Business Data Model / Data Dictionary** – key entities & data definitions
3. **Scope of the Product** – what is in and out of scope
4. **List of Atomic Functional Requirements** – detailed requirements typically written using a structured “requirement shell” (unique ID, description, rationale, fit criterion, etc.)

#### 2c) **Non-Functional Requirements**

These describe _how the system must be_ (qualities, constraints):

- Look & Feel requirements
- Usability and humanity requirements
- Performance requirements
- Operational and environmental requirements
- Maintainability & support requirements
- Security requirements
- Cultural requirements
- Legal/compliance requirements

### 3) **Project Issues**

Document _uncertainties, risks, and implications_.

1. **Open Issues** – unresolved questions
2. **Off-the-Shelf Solutions** – evaluated options
3. **New Problems** – newly discovered problem areas
4. **Tasks** – tasks necessary to achieve the requirements
5. **Migration / Cut-over Activities** – transition actions
6. **Risks** – key project risks and mitigations
7. **Costs** – estimated costs tied to requirements
8. **User Documentation and Training** – documentation/training required
9. **Waiting Room** – ideas deferred but noted
10. **Ideas for Solutions** – suggested approaches without commitment

### 4) **Naming Conventions and Definitions**

Critical for clarity and precision:

- **Glossary** – terms & acronyms explained
- **Data Dictionary** – clear definitions of data items used in requirements

## Guide to using Codebase Research Subagents

Delegate a research/exploration task to a codebase researcher subagent if any of the following apply:

- Context cost is high i.e. the question requires reading many docs / long logs / multiple web pages that would bloat your own context window (you are a Large Language Model).
- Deep factual lookup e.g. you are looking for stable facts, up-to-date API details, benchmark numbers, or library behaviour and you need a concise, verified summary as output.
- Exploratory research e.g. evaluating multiple options, tradeoffs, or gathering citations and links (design choices, benchmarking results, algorithm selection).
- Complex synthesis e.g. you require a short, information-dense deliverable (TL;DR + 3 recommended options + one best option + commands/code snippets).

You may launch several parallel subagents - launch 1 subagent per distinct task.

Give me the list of subagents you want to launch and ask my permission before launching them.
