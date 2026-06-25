# Poor Man's Agent Harness

```bash
dotnet publish \
  --configuration Release \
  --runtime linux-x64 \
  --self-contained false \
  -p:PublishSingleFile=true
```

Built file is written to: `bin/Release/net9.0/linux-x64/publish/poor_mans_agent_harness.pdb`

Make it globally available by sym-linking to the built executable:

```bash
ln -s \
  ~/command_line_tools/poor_mans_agent_harness/bin/Release/net9.0/linux-x64/publish/poor_mans_agent_harness \
  ~/.local/bin/pma
```

## Learning Resources

- <https://learn.microsoft.com/en-us/dotnet/standard/commandline/get-started-tutorial>
