using System;
using System.Diagnostics;

namespace PoorMansAgent.AgentTools;

public enum BashRunStatus
{
    Executed,
    UserRejected,
}

public sealed record BashResult(BashRunStatus Status, int ExitCode, string StdOut, string StdErr);

internal static class BashRunner
{
    // public static string RunBash(string? bashCommand, string? stdIn, string motivation)
    public static BashResult RunBash(string bashCommand, string motivation)
    {
        bool useColor = !Console.IsErrorRedirected;
        string green = useColor ? "\x1b[32m" : "";
        string yellow = useColor ? "\x1b[33m" : "";
        string resetColor = useColor ? "\x1b[0m" : "";
        Console.Error.WriteLine("Proposed bash command(s):");
        Console.Error.WriteLine($"{yellow}{bashCommand}{resetColor}");
        Console.Error.WriteLine($"{green}MOTIVATION: {motivation}{resetColor}");
        Console.Error.WriteLine(
            "Approve this command? [y/n] (anything other than 'y' is interpreted as no.)"
        );
        string? userInput = ReadApprovalFromTerminal();
        if (string.Equals(userInput, "y", StringComparison.OrdinalIgnoreCase))
        {
            var result = RunBashAsync(bashCommand).GetAwaiter().GetResult();
            return result;
        }
        return new BashResult(
            BashRunStatus.UserRejected,
            -1,
            string.Empty,
            "User rejected the proposed bash command(s)."
        );
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

    private static async Task<BashResult> RunBashAsync(string bashCommand)
    {
        var psi = new ProcessStartInfo
        {
            FileName = "bash",
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
            CreateNoWindow = true,
        };

        psi.ArgumentList.Add("-c");
        psi.ArgumentList.Add(bashCommand);

        using var process = new Process { StartInfo = psi };

        process.Start();

        Task<string> stdOutTask = process.StandardOutput.ReadToEndAsync();
        Task<string> StdErrTask = process.StandardError.ReadToEndAsync();

        await process.WaitForExitAsync();

        return new BashResult(
            BashRunStatus.Executed,
            process.ExitCode,
            await stdOutTask,
            await StdErrTask
        );
    }
}
