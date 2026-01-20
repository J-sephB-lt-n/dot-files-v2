# Create folder to hold current task context

First, ask me for the name and description of the task (project feature) which we are going to start working on, then once I've given you this information, do the following:

1. Create the folder current_task/ in the project root directory. If it already exists, empty it (i.e. delete all of the existing files in it).

2. Create an empty file current_task/agent_notes.md.

3. Create the file current_task/README.md with the following content:

```
# {{ task name here }}

The current task (project feature) being worked on is {{ task description here }}

Current task status is: 'REQUIREMENTS_GATHERING'

This folder (current_task/) contains context and documentation on the current task (project feature) being worked on.

The file current_task/agent_notes.md contains notes left by developers who have worked on this task (project feature) before you.
```
