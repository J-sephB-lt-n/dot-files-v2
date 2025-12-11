# Launch a Subagent

Launch a subagent in the terminal using this command:

```bash
mkdir -p ./tmp_subagent_output &&
cursor-agent -p '<describe the task for the subagent here>' --model claude-4.5-opus-high
```

Instruct the agent to write it's final findings in an information-dense markdown file in ./tmp_subagent_output/ (maximum useful information in as few lines as possible).
