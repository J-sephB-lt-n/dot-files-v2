using Microsoft.Extensions.FileSystemGlobbing;
using Microsoft.Extensions.FileSystemGlobbing.Abstractions;

namespace PoorMansAgent.AgentTools;

public sealed record GlobFileMatch(
    string RelativePath,
    // string FullPath,
    string RelativeDir,
    FileInfo Info
);

internal static class PathFinder
{
    public static IEnumerable<GlobFileMatch> Glob(
        DirectoryInfo dir,
        string globPattern,
        int maxDepth
    )
    {
        var matcher = new Matcher();
        matcher.AddInclude(globPattern);

        var dir_wrapper = new DirectoryInfoWrapper(dir);
        return matcher
            .Execute(dir_wrapper)
            .Files.Select(match =>
            {
                return new GlobFileMatch(
                    RelativePath: match.Path,
                    RelativeDir: Path.GetDirectoryName(match.Path) ?? string.Empty,
                    Info: new FileInfo(Path.Combine(dir.FullName, match.Path))
                );
            });
        // IEnumerable<string> files = matcher.GetResultsInFullPath(dir.FullName);
    }
}
