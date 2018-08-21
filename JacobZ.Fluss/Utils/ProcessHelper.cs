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
            exec.StartInfo.RedirectStandardError = true;
            exec.StartInfo.FileName = executable;

            return exec;
        }

        public static Process Generate(string executable, params string[] arguments)
        {
            Process exec = Generate(executable);
            exec.StartInfo.Arguments = string.Join(" ", arguments);
            return exec;
        }

        public static void EnsureExit(this Process process)
        {
            while (!process.HasExited) ;
            if (process.ExitCode != 0)
                throw new ExecutionException(process.StandardError.ReadToEnd())
                { Output = process.StandardOutput.ReadToEnd() };
        }
    }

    public class ExecutionException : ApplicationException
    {
        public string Output { get; set; }

        public ExecutionException() : base() { }
        public ExecutionException(string error) : base(error) { }
        public ExecutionException(string error, Exception inner) : base(error, inner) { }
    }
}
