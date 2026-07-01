using Microsoft.Extensions.FileSystemGlobbing;

namespace PoorMansAgent.AgentTools;

internal static class PathFinder
{
    public static IEnumerable<string> Glob(DirectoryInfo dir, string globPattern, int maxDepth)
    {
        var matcher = new Matcher();
        matcher.AddInclude(globPattern);
        IEnumerable<string> files = matcher.GetResultsInFullPath(dir.FullName);
        return files;
    }
}
