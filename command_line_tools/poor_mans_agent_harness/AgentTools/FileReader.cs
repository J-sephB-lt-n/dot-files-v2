using System.Text;

namespace PoorMansAgent.AgentTools;

internal static class FileReader
{
    public static string ReadFile(FileInfo file, int offset, int limit)
    {
        if (!file.Exists)
        {
            return $"File {file.ToString()} does not exist.";
        }
        else
        {
            var sb = new StringBuilder();
            foreach (
                var (line, idx) in File.ReadLines(file.FullName)
                    .Skip(offset)
                    .Take(limit)
                    .Select((line, i) => (line, i))
            )
            {
                sb.AppendLine($"{offset + idx + 1, 5}: {line}");
            }

            return sb.ToString();
        }
        ;
    }
}
