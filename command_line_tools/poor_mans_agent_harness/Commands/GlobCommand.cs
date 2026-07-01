using System.CommandLine;
using PoorMansAgent.AgentTools;

namespace PoorMansAgent.Commands;

internal static class GlobCommand
{
    public static Command Build()
    {
        var pathArg = new Argument<DirectoryInfo>("path")
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

        var command = new Command("glob", "List file paths by glob pattern.")
        {
            Arguments = { pathArg, globPatternArg },
            Options = { maxDepthOption },
        };

        command.SetAction(parseResult =>
        {
            Console.WriteLine("working so far");
        });

        return command;
    }
}
