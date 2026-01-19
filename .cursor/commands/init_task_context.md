# Create folder to hold current task context

First, ask me for the name and description of the task/feature which we are going to start working on, then once I've given you this information, do the following:

1. Create the folder current_feature/ in the project root directory. If it already exists, empty it (i.e. delete all of the existing files in it).

2. Create an empty file current_feature/agent_notes.md.

3. Create the file current_feature/README.md with the following content:

```
# {{ task/feature name here }}

The current feature being worked on is {{ task/feature description here }}

Current feature status is: 'REQUIREMENTS_GATHERING'

This folder (current_feature/) contains context and documentation on the current feature being worked on.

The file current_feature/agent_notes.md contains notes left by developers who have worked on this feature before you.
```
