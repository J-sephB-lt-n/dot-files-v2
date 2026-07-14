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
            int oldStringCounts = CountOccurencesOfSubstring(oldString, fileText);
            if (oldStringCounts == 0)
                return $"status=FAILED. String '{oldString}' does not appear in file {file.ToString()}.";
            if (oldStringCounts > 1 && !replaceAll)
            {
                return $"status=FAILED. string to replace appears {oldStringCounts} times "
                    + $"in file {file.ToString()} and flag --replace-all is missing.";
            }
            string newText = fileText.Replace(oldString, newString);
            PrintDiff(fileText, newText);
            Console.WriteLine("Approve this change [y/n]");
            Console.WriteLine("(anything other than 'y' aborts)");
            string? userInput = Console.ReadLine();
            if (userInput == "y")
            {
                File.WriteAllText(file.ToString(), newText);
                return $"status=SUCCESS: Replaced {oldStringCounts} occurrences of string in "
                    + $"file {file.ToString()}";
            }
            else
            {
                return $"status=FAILED: user rejected proposed string replacement "
                    + $"in file {file.ToString()}";
            }
        }
        ;
    }

    private static int CountOccurencesOfSubstring(string substring, string source)
    {
        int count = 0;
        int index = 0;
        while (true)
        {
            index = source.IndexOf(substring, index, StringComparison.Ordinal);
            if (index == -1)
            {
                break;
            }
            count++;
            index += substring.Length;
        }
        return count;
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
