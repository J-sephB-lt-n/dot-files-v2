using System.CommandLine;
using PoorMansAgent.AgentTools;

namespace PoorMansAgent.Commands;

internal static class GlobCommand
{
    public static Command Build()
    {
        var dirArg = new Argument<DirectoryInfo>("dir")
        {
            Description = "The directory to search in",
            Arity = ArgumentArity.ExactlyOne,
        };
        var globPatternArg = new Argument<string>("globPattern")
        {
            Description = "Glob pattern.",
            Arity = ArgumentArity.ExactlyOne,
        };
        var maxDepthOption = new Option<int>("--max-depth")
        {
            Description = "Maximum folder depth to traverse.",
            DefaultValueFactory = _ => 3,
        };
        var idOption = new Option<string>("--id")
        {
            Description = "Unique command identifier",
            Required = true,
        };

        var command = new Command("glob", "List file paths by glob pattern.")
        {
            Arguments = { dirArg, globPatternArg },
            Options = { maxDepthOption, idOption },
        };

        command.SetAction(parseResult =>
        {
            DirectoryInfo dir = parseResult.GetValue(dirArg)!;
            string globPattern = parseResult.GetValue(globPatternArg)!;
            int maxDepth = parseResult.GetValue(maxDepthOption);
            IEnumerable<string> filePaths = PathFinder.Glob(dir, globPattern, maxDepth);
            string commandId = parseResult.GetValue(idOption)!;
            string result = WrapWithResultTags(filePaths, commandId, globPattern);
            Console.WriteLine(result);
        });

        return command;
    }

    public static string WrapWithResultTags(
        IEnumerable<string> filePaths,
        string commandId,
        string globPattern
    )
    {
        string lines = string.Join(Environment.NewLine, filePaths);
        return $"""
            <glob-result id="{commandId}" pattern="{globPattern}">
            {lines}
            </glob-result>
            """;
    }
}
