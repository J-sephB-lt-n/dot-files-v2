using System.IO;
using DiffPlex;
using DiffPlex.DiffBuilder;
using DiffPlex.DiffBuilder.Model;

namespace PoorMansAgent.AgentTools;

internal static class FileEditor
{
    public static string EditFile(
        FileInfo file,
        string oldString,
        string newString,
        bool replaceAll
    )
    {
        if (!file.Exists)
        {
            return $"status=FAILED. File {file.ToString()} does not exist.";
        }
        else
        {
            string fileText = File.ReadAllText(file.ToString());
            string newText = fileText.Replace(oldString, newString);
            PrintDiff(fileText, newText);
            return "TODO";
        }
        ;
    }

    private static void PrintDiff(string oldText, string newText)
    {
        var diff = InlineDiffBuilder.Diff(oldText, newText);
        foreach (var line in diff.Lines)
        {
            switch (line.Type)
            {
                case ChangeType.Inserted:
                    Console.ForegroundColor = ConsoleColor.Green;
                    Console.WriteLine($"+ {line.Text}");
                    break;
                case ChangeType.Deleted:
                    Console.ForegroundColor = ConsoleColor.Red;
                    Console.WriteLine($"- {line.Text}");
                    break;
                case ChangeType.Modified:
                    Console.ForegroundColor = ConsoleColor.Yellow;
                    Console.WriteLine($"~ {line.Text}");
                    break;
                default:
                    Console.ResetColor();
                    break;
            }
        }
        Console.ResetColor();
    }
}
