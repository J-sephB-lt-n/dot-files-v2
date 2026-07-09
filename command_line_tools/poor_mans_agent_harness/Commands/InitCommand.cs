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

                You can also give me bash commands to run for you, which you can do 2 
                different ways:
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
                bash for listing and reading files - use `pma glob` and `pma read` for that.

                Please make it very clear what the commands are which you would like me to 
                run. Feel free to tell me to run multiple commands (--id will help you 
                    differentiate the outputs of the different commands).
                In particular, please batch file reads if you know you are going to read 
                multiple files e.g.
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
