using Microsoft.Extensions.FileSystemGlobbing;
using Microsoft.Extensions.FileSystemGlobbing.Abstractions;

namespace PoorMansAgent.AgentTools;

internal static class PathFinder
{
    private sealed record GlobFileMatch(
        string RelativePath,
        // string FullPath,
        string RelativeDir,
        FileInfo Info
    );

    public static IEnumerable<string> Glob(DirectoryInfo dir, string globPattern, int maxDepth)
    {
        IEnumerable<GlobFileMatch> all_matches = GetAllMatches(dir, globPattern);
        // filtering steps to go here
        IEnumerable<string> filepaths = all_matches.Select(x => x.RelativePath);

        return filepaths;
    }

    /// Fetch ALL filepaths matching the glob pattern ``globPattern``
    private static IEnumerable<GlobFileMatch> GetAllMatches(DirectoryInfo dir, string globPattern)
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
    }
}
