# Codebase Scaffolding

Your task is to set up the current codebase for a new variant of agile development.

First, do the following:

1. Explore the existing project structure (folders and files) without viewing any file contents.
2. Read the following project documentation (whichever exist) to get project context:

- README.md
- /docs/PRD.md
- /docs/architecture_design.md
- If there is other documentation that looks useful for project context, give me the filepaths and I'll tell you whether you should read it or not.

Then, please perform the following steps in order:
(Make a list first and then tick it off as you complete each step. For EVERY step, ask my permission first before acting)

1. If the project does not have a README.md at the project root then create one (ask my permission first).
2. Set up an Architecture Decision Record (ADR) system (ask my permission first):
   i. Create the /docs/adr/ folder (if it doesn't exist)
   ii. Add a note into the project root README.md linking to /docs/adr/ and explaining what it is for.
   iii. Describe in the project root README.md describing how to add an ADR (ADRs must be sequentially numbered markdown files in /docs/adr/{{ adr_num }}-{{ adr_name }}.md in a consistent schema with entries "title", "status", "context", "decision", "consequences", "alternatives considered", "decision drivers", "references")
3. If this is a greenfield codebase, scaffold (create) the project folders and files according to the goals and requirements in the project documentation you read earlier (ask my permission first). Keep the actual files empty for now (you can add module docstrings and similar high-level documentation).
4. Check whether each of the following sections exist in the README.md, adding them if they don't (ask my permission first):
   i. Very brief overview of the project - like an elevator pitch.
   ii. Instructions on how to run the project.
   iii. An overview of the project architecture, including the core project architecture goals, a filetree view of the project architecture (with in-line comments) and (if relevant) some guidance on how to do common tasks (based on the project architecture goals or on patterns already in the codebase).
5. If you have made any technical decisions, add records of these to /docs/adr/ (ask my permission first).
6. Make a git commit of your changes with an organised commit message (ask my permission first).

After completing all of these steps, give me a list of everything which was done (and not done).
