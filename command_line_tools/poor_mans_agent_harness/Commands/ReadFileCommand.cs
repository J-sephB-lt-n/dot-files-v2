using System.CommandLine;
using PoorMansAgent.AgentTools;

namespace PoorMansAgent.Commands;

internal static class ReadFileCommand
{
    public static Command Build()
    {
        var inputPathArg = new Argument<FileInfo>("inputPath")
        {
            Description = "File to read.",
            Arity = ArgumentArity.ExactlyOne,
        };
        var offsetOption = new Option<int>("--offset")
        {
            Description = "Number of initial lines to skip.",
            DefaultValueFactory = _ => 0,
        };
        var limitOption = new Option<int>("--limit")
        {
            Description = "Maximum number of lines to show [1, 999]",
            DefaultValueFactory = _ => 200,
        };
        limitOption.Validators.Add(result =>
        {
            var value = result.GetValueOrDefault<int>();
            if (value is < 1 or > 999)
            {
                result.AddError("--limit must be between 1 and 999.");
            }
        });
        var idOption = new Option<string>("--id")
        {
            Description = "Unique session identifier",
            Required = true,
        };

        var command = new Command("read", "Read a portion of the content in a single file.")
        {
            Arguments = { inputPathArg },
            Options = { offsetOption, limitOption, idOption },
        };

        command.SetAction(parseResult =>
        {
            FileInfo inputPath = parseResult.GetValue(inputPathArg)!;
            int offset = parseResult.GetValue(offsetOption);
            int limit = parseResult.GetValue(limitOption);
            string sessionId = parseResult.GetValue(idOption)!;

            Console.WriteLine(
                $"""
                 inputPath: {inputPath.FullName}
                 offset:    {offset}
                 limit:     {limit}
                 sessionId: {sessionId}
                """
            );

            Console.WriteLine(FileReader.ReadFile(file: inputPath, offset, limit));
        });

        return command;
    }
}
