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

        rootCmd.Add(initCmd);

        return rootCmd.Parse(args).Invoke();
    }
}
