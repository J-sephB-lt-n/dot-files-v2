using System.CommandLine;
using PoorMansAgent.Commands;

namespace PoorMansAgent;

class Program
{
    static int Main(string[] args)
    {
        var rootCmd = new RootCommand(
            """
            --- Poor Man's Agent Harness (pma) ---
            Turn your chatbot into almost a coding agent 
            """
        );

        // rootCmd.Add(initCmd);
        rootCmd.Add(ReadCommand.Build());
        // rootCmd.Add(editCmd);

        return rootCmd.Parse(args).Invoke();
    }
}
