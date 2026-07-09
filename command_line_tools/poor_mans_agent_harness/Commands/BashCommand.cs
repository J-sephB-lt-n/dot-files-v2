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
        var hasStdInFlagOption = new Option<bool>("--stdin")
        {
            Description =
                "Allows to provide bash command(s) from standard input (e.g. a heredoc). Cannot be used if --command is used.",
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
            Options = { bashCommandOption, hasStdInFlagOption, motivationOption, idOption },
        };

        command.Validators.Add(commandResult =>
        {
            bool hasBashCommand = commandResult.GetValue(bashCommandOption) is not null;
            bool hasStdIn = commandResult.GetValue(hasStdInFlagOption);
            if (hasBashCommand == hasStdIn)
            {
                commandResult.AddError("Exactly one of --command or --stdin must be supplied.");
            }
        });

        command.SetAction(async parseResult =>
        {
            string? bashCommand = parseResult.GetValue(bashCommandOption);
            bool hasStdIn = parseResult.GetValue(hasStdInFlagOption);
            if (hasStdIn)
            {
                bashCommand = await Console.In.ReadToEndAsync();
            }
            string motivation = parseResult.GetValue(motivationOption)!;
            string commandId = parseResult.GetValue(idOption)!;
            BashRunner.RunBash(bashCommand!, motivation);
        });

        return command;
    }
}
