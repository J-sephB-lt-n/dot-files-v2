using System;
using System.Diagnostics;

namespace PoorMansAgent.AgentTools;

public sealed record BashResult(int ExitCode, string StdOut, string StdErr);

internal static class BashRunner
{
    // public static string RunBash(string? bashCommand, string? stdIn, string motivation)
    public static void RunBash(string bashCommand, string motivation)
    {
        Console.WriteLine("Proposed bash command(s):");
        Console.ForegroundColor = ConsoleColor.Green;
        Console.WriteLine(motivation);
        Console.ForegroundColor = ConsoleColor.Yellow;
        Console.WriteLine(bashCommand);
        Console.ResetColor();
        // return RunBashAsync(bashCommand, stdIn)
        //   .GetAwaiter()
        //   .GetResult()
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

        return new BashResult(process.ExitCode, await stdOutTask, await StdErrTask);
    }
}
