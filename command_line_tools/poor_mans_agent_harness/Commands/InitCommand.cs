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

                Here is the root layout of my codebase:
                $ pma glob . '**/**' --max-depth 1 --id project-root-files
                {globResult}
                """
            );
        });

        return command;
    }
}
