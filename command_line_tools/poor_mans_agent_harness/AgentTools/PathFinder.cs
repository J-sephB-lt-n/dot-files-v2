using System.Collections.Generic;
using Microsoft.Extensions.FileSystemGlobbing;
using Microsoft.Extensions.FileSystemGlobbing.Abstractions;

namespace PoorMansAgent.AgentTools;

internal static class PathFinder
{
    private sealed record GlobFileMatch(
        string RelativePath,
        IReadOnlyList<string> RelativePathSegments,
        // string FullPath,
        string RelativeDir
    // FileInfo Info
    );

    public static IEnumerable<string> Glob(DirectoryInfo dir, string globPattern, int maxDepth)
    {
        int maxFiles = 50; // might make this a function arg later
        var matches = GetAllMatches(dir, globPattern).ToList();
        var filePaths = new List<string>();
        for (int depth = 1; depth <= maxDepth; depth++)
        {
            var remaining = new List<GlobFileMatch>();
            var dirFileCounts = matches
                // count (recursively) files per folder at this depth
                .Where(m => m.RelativePathSegments.Count > depth)
                .CountBy(m => String.Join("/", m.RelativePathSegments.Take(depth)))
                .ToDictionary();
            foreach (
                var (bigDir, fileCount) in dirFileCounts.Where(x =>
                    x.Value > maxFiles || depth == maxDepth
                )
            )
            {
                filePaths.Add($"{bigDir}/... ({fileCount} files)");
            }
            foreach (var match in matches)
            {
                if (match.RelativePathSegments.Count == depth)
                {
                    filePaths.Add(match.RelativePath);
                }
                else if (
                    dirFileCounts.GetValueOrDefault(
                        String.Join("/", match.RelativePathSegments.Take(depth))
                    ) > maxFiles
                    || depth == maxDepth
                ) { }
                else
                {
                    remaining.Add(match);
                }
            }
            matches = remaining;
        }

        return filePaths;
    }

    private static string[] SplitFilePath(string filepath)
    {
        ArgumentNullException.ThrowIfNullOrEmpty(filepath);
        return filepath.Replace("\\", "/").Split("/", StringSplitOptions.RemoveEmptyEntries);
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
                    RelativePathSegments: SplitFilePath(match.Path),
                    RelativeDir: Path.GetDirectoryName(match.Path) ?? string.Empty
                // Info: new FileInfo(Path.Combine(dir.FullName, match.Path))
                );
            });
    }
}
