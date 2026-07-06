namespace PoorMansAgent.AgentTools;

internal static class FileEditor
{
    public static string EditFile(
        FileInfo file,
        string oldString,
        string newString,
        bool replaceAll
    )
    {
        if (!file.Exists)
        {
            return $"status=FAILED. File {file.ToString()} does not exist.";
        }
        else
        {
            return "TODO";
        }
    }
}
