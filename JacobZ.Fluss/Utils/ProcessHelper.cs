using System;
using System.Diagnostics;

namespace JacobZ.Fluss.Utils
{
    public static class ProcessHelper
    {
        public static Process Generate(string executable)
        {
            Process exec = new Process();
            exec.StartInfo.UseShellExecute = false;
            exec.StartInfo.RedirectStandardInput = true;
            exec.StartInfo.RedirectStandardOutput = true;
            exec.StartInfo.FileName = executable;

            return exec;
        }

        public static void EnsureExit(this Process process)
        {
            while (!process.HasExited) ;
            if (process.ExitCode != 0)
                throw new ExecutionException(process.StandardOutput.ReadToEnd());
        }
    }

    public class ExecutionException : ApplicationException
    {
        public ExecutionException() : base() { }
        public ExecutionException(string message) : base(message) { }
        public ExecutionException(string message, Exception inner) : base(message, inner) { }
    }
}
