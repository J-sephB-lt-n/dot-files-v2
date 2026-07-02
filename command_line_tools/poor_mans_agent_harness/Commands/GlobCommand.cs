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

        var command = new Command("glob", "List file paths by glob pattern.")
        {
            Arguments = { dirArg, globPatternArg },
            Options = { maxDepthOption },
        };

        command.SetAction(parseResult =>
        {
            DirectoryInfo dir = parseResult.GetValue(dirArg)!;
            string globPattern = parseResult.GetValue(globPatternArg)!;
            int maxDepth = parseResult.GetValue(maxDepthOption);
            IEnumerable<GlobFileMatch> files = PathFinder.Glob(dir, globPattern, maxDepth);
            foreach (GlobFileMatch m in files)
            {
                Console.WriteLine(m.RelativePath);
                Console.WriteLine(m);
            }
        });

        return command;
    }
}
