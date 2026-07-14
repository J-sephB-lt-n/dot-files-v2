using System.CommandLine;
using PoorMansAgent.AgentTools;

namespace PoorMansAgent.Commands;

internal static class EditFileCommand
{
    public static Command Build()
    {
        var filePathArg = new Argument<FileInfo>("filePath")
        {
            Description = "File to edit.",
            Arity = ArgumentArity.ExactlyOne,
        };
        var oldStringOption = new Option<string>("--old-string")
        {
            Description = "String to replace.",
            Required = true,
        };
        var newStringOption = new Option<string>("--new-string")
        {
            Description = "Replacement text",
            Required = true,
        };
        var idOption = new Option<string>("--id")
        {
            Description = "Unique command identifier",
            Required = true,
        };
        var replaceAllOption = new Option<bool>("--replace-all")
        {
            Description = "If true, all occurrences of <old-text> are replaced.",
            DefaultValueFactory = _ => false,
        };

        var command = new Command(
            "edit",
            "Replace text <old-string> with text <new-string> in file. If multiple instances of <old-string> are present in the file and --replace-all is not set, then the edit fails."
        )
        {
            Arguments = { filePathArg },
            Options = { oldStringOption, newStringOption, idOption, replaceAllOption },
        };

        command.SetAction(parseResult =>
        {
            FileInfo filePath = parseResult.GetValue(filePathArg)!;
            string oldString = parseResult.GetValue(oldStringOption)!;
            string newString = parseResult.GetValue(newStringOption)!;
            string commandId = parseResult.GetValue(idOption)!;
            bool replaceAll = parseResult.GetValue(replaceAllOption)!;

            string result = FileEditor.EditFile(filePath, oldString, newString, replaceAll);
            Console.WriteLine(
                $"<edit-file-result file=\"{filePath.ToString()}\" replace-all={replaceAll} "
                    + $"id=\"{commandId}\">"
            );
            Console.WriteLine(result);
            Console.WriteLine("</edit-file-result>\n");
        });

        return command;
    }
}
