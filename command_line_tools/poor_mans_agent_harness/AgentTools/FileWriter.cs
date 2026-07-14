using System.IO;
using DiffPlex;
using DiffPlex.DiffBuilder;
using DiffPlex.DiffBuilder.Model;

namespace PoorMansAgent.AgentTools;

internal static class FileWriter
{
    public static string WriteFile(FileInfo file, string fileContent)
    {
        if (file.Exists)
        {
            return $"status=FAILED. File {file.ToString()} already exists.";
        }
        else
        {
            bool useColor = !Console.IsErrorRedirected;
            string green = useColor ? "\x1b[32m" : "";
            string resetColor = useColor ? "\x1b[0m" : "";
            Console.Error.WriteLine($"Proposed contents for new file {file.ToString()}:");
            Console.Error.WriteLine($"{green}{fileContent}{resetColor}");
            Console.Error.WriteLine(
                "Approve this command? [y/n] (anything other than 'y' is interpreted as no.)"
            );
            string? userInput = ReadApprovalFromTerminal();
            if (userInput == "y")
            {
                File.WriteAllText(file.ToString(), fileContent);
                return $"status=SUCCESS: successfully wrote new file {file.ToString()}";
            }
            else
            {
                return $"status=FAILED: user rejected proposed new file {file.ToString()}";
            }
        }
        ;
    }

    private static string? ReadApprovalFromTerminal()
    {
        if (OperatingSystem.IsLinux() || OperatingSystem.IsMacOS())
        {
            try
            {
                using var tty = File.OpenText("/dev/tty");
                return tty.ReadLine();
            }
            catch
            {
                return null;
            }
        }

        return Console.ReadLine();
    }
}
