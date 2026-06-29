namespace PoorMansAgent.ReadTool;

public class ReadService
{
    public string Read(FileSystemInfo fsi)
    {
        if (!fsi.Exists)
        {
            return "does not exist";
        }
        else if (fsi is FileInfo file)
        {
            return ReadFile(file);
        }
        else if (fsi is DirectoryInfo dir)
        {
            return ListDir(dir);
        }
        else
        {
            throw new InvalidOperationException($"Unknown FileSystemInfo {fsi.GetType().Name}");
        }
    }

    private string ReadFile(FileInfo file)
    {
        return "is a file";
    }

    private string ListDir(DirectoryInfo dir)
    {
        return "is a dir";
    }
}
