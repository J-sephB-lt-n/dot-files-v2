using System.CommandLine;
using PoorMansAgent.AgentTools;

namespace PoorMansAgent.Commands;

internal static class WriteFileCommand
{
    public static Command Build()
    {
        var newFilePathArg = new Argument<FileInfo>("newFilePath")
        {
            Description = "Desired filepath of new file.",
            Arity = ArgumentArity.ExactlyOne,
        };
        var idOption = new Option<string>("--id")
        {
            Description = "Unique session identifier",
            Required = true,
        };

        var command = new Command("write", "Write a new file.")
        {
            Arguments = { newFilePathArg },
            Options = { idOption },
        };

        command.SetAction(async parseResult =>
        {
            FileInfo newFilePath = parseResult.GetValue(newFilePathArg)!;
            string commandId = parseResult.GetValue(idOption)!;
            string fileContent = await Console.In.ReadToEndAsync();
            string result = FileWriter.WriteFile(newFilePath, fileContent);
            Console.WriteLine(
                $"<write-file-result file=\"{newFilePath.ToString()}\" id=\"{commandId}\">"
            );
            Console.WriteLine(result);
            Console.WriteLine("</write-file-result>\n");
        });

        return command;
    }
}
