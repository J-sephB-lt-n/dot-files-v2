using System.CommandLine;
using System.CommandLine.Parsing;

namespace PoorMansAgentHarness;

class Program
{
    static int Main(string[] args)
    {
        var rootCmd = new RootCommand(
            """
            ---Poor Man's Agent Harness---

            Turn your chatbot into the world's worst coding agent.
            """
        );

        var initCmd = new Command(
            "init",
            "Start a new agent session (prints the LLM prompt to stdout)."
        );
        var readCmd = new Command("read", "Read a file or list files in a directory.");
        var editCmd = new Command("edit", "Exact string replacement in a file.");

        rootCmd.Add(initCmd);
        rootCmd.Add(readCmd);
        rootCmd.Add(editCmd);

        return rootCmd.Parse(args).Invoke();
    }
}
