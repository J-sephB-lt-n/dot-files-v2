using System.CommandLine;
using PoorMansAgent.AgentTools;

namespace PoorMansAgent.Commands;

internal static class InitCommand
{
    public static Command Build()
    {
        var command = new Command("init", "Start a new agent session in the current folder.");

        command.SetAction(parserResult =>
        {
            var current_dir = new DirectoryInfo(".");
            IEnumerable<string> filePaths = PathFinder.Glob(current_dir, "**/**", 1);
            string globResult = GlobCommand.WrapWithResultTags(
                filePaths,
                "project-root-files",
                "**/**"
            );
            Console.WriteLine(
                $"""
                I have some work for you to do in my codebase.

                You can read files in my codebase using:
                ```bash
                pma read path/to/file --offset 0 --limit 200 --id <unique-text>
                ```
                where --offset is the number of lines at the beginning to skip (default 0),
                --limit is the number of lines to show (default 200, maximum 999) and --id 
                is a unique identifier (I'll include it when I give the command result 
                back to you).
                File numbers are shown at the start of each line as "<num>: " (these line 
                  numbers are not part of the actual file content).

                You can list files using:
                ```bash
                pma glob <dir> '<glob-pattern>' --max-depth 3 --id <unique-text>
                ```
                where --max-depth controls how deep to traverse (default 3) and --id is a 
                unique identifier I will include when I give you the command result.

                You can write a new file using:
                ```bash
                pma write <filepath> << 'EOF'
                file
                content
                here
                EOF
                ```
                For new folders, use `mkdir` via `pma bash`

                To edit an existing file use:
                ```bash
                pma edit <filepath> --old-string 'existing-string' --new-string 'string-to-replace-with' --id <unique-text>
                ```
                This replaces --old-string with --new-string
                If there are multiple occurences of --old-string then your edit will be 
                rejected unless you additionally include flag --replace-all

                You can give me bash commands to run for you, which you can do via 
                --command or via --stdin:
                ```bash
                # Option 1: call like `bash -c` (single simple command)
                pma bash --id <unique-text> --motivation 'explanation of what you propose to run, what it will do and why' --command 'grep -r --include="*.js" --exclude-dir=node_modules "handleSubmit" src/'
                # Option 2: pass bash command(s) from stdin (longer command or multiple commands):
                pma bash --id <unique-text> --motivation 'explanation of what you propose to run, what it will do and why' --stdin <<'EOF'
                find . -name "*.js" -maxdepth 3
                find . -type f -name "Dockerfile"
                find . -type d -name "node_modules"
                EOF
                ```
                explain to me what the command will do and why you are running it. Don't use 
                bash for listing, reading, writing or editing files - use `pma glob`, 
                `pma read`, `pma write` and `pma edit` for those.

                Please make it very clear what the commands are which you would like me to 
                run. Feel free to tell me to run multiple commands (--id will help you 
                    differentiate the outputs of the different commands).
                In particular, for pma commands which you don't need to run sequentially, please 
                batch them for me e.g.
                ```
                pma read file1 --id read-file1 && pma read file2 --id read-file2 && pma read file3 --id read-file-3
                ```

                Here is the root layout of my codebase:
                $ pma glob . '**/**' --max-depth 1 --id project-root-files
                {globResult}

                I will now describe your task.
                """
            );
        });

        return command;
    }
}
