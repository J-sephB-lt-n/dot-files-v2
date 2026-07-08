using System.CommandLine;
using PoorMansAgent.AgentTools;

namespace PoorMansAgent.Commands;

internal static class BashCommand
{
    public static Command Build()
    {
        var bashCommandOption = new Option<string>("--command")
        {
            Description =
                "Single bash command to run directly - akin to 'bash -c'. Cannot be used if --stdin is used.",
        };
        var stdInOption = new Option<string>("--stdin")
        {
            Description =
                "Bash command(s) to run from standard input. Cannot be used if --command is used.",
        };
        var motivationOption = new Option<string>("--motivation")
        {
            Description = "Description of what bash command does and why we are running it.",
            Required = true,
        };
        var idOption = new Option<string>("--id")
        {
            Description = "Unique command identifier.",
            Required = true,
        };

        var command = new Command("bash", "Execute bash command(s)")
        {
            Options = { bashCommandOption, stdInOption, motivationOption, idOption },
        };

        command.Validators.Add(commandResult =>
        {
            bool hasBashCommand = commandResult.GetValue(bashCommandOption) is not null;
            bool hasStdIn = commandResult.GetValue(stdInOption) is not null;
            if (hasBashCommand == hasStdIn)
            {
                commandResult.AddError("Exactly one of --command or --stdin must be supplied.");
            }
        });

        command.SetAction(parseResult =>
        {
            Console.WriteLine("TODO");
        });

        return command;
    }
}
