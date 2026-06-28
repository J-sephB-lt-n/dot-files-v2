using System.CommandLine;

namespace PoorMansAgent.Commands;

internal static class ReadCommand
{
    public static Command Build()
    {
        var inputPathArg = new Argument<FileInfo>("inputPath")
        {
            Description = "File or directory to read.",
            Arity = ArgumentArity.ExactlyOne,
        };
        var offsetOption = new Option<int>("--offset")
        {
            Description = "TODO",
            DefaultValueFactory = _ => 0,
        };
        var limitOption = new Option<int>("--limit")
        {
            Description = "Maximum number of lines to show",
            DefaultValueFactory = _ => 200,
        };
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
        });

        return command;
    }
}
