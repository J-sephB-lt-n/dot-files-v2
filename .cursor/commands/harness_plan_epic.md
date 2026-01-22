# Epic Decomposition Planning

First, for each of the following, check whether the file exists, then ask permission to read it, then (if given the go ahead) read the full file contents:

1. README.md
2. docs/PRD.md
3. docs/architecture_design.md
4. docs/adr/\*.md (all)
5. docs/current_epic/epic_requirements.md

We are now going to decompose the epic defined in /docs/current_epic/eipc_requirements.md into user stories (individual self-contained units of developer work). You may explore the codebase a little on your own to get any further context you may need to perform this task.

In discussion with me (e.g. we might need to debate what is an appropriate user story size), define a sequence of user stories whose completion means the completion of the epic.
User stories have the following standard format:

```json
[
  {
    "id": "unique identifier of user story in this epic",
    "title": "short descriptive title of user story",
    "description": "As a [role], I want [capability], so that [benefit]",
    "acceptance_criteria": ["one sentence description of criterion", ...], // up to 5
    "status": "NOT_STARTED",
  },
  ...
]
```

Once we have finalised these user stories, write them to a valid JSON file at `docs/current_epic/user_stories.json`
