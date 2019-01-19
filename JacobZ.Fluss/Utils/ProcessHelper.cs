using System;
using System.IO;
using System.Threading.Tasks;
using System.Diagnostics;

namespace JacobZ.Fluss.Utils
{
    static class ProcessHelper
    {
        public static Process Generate(string executable, params string[] arguments)
        {
            Process exec = new Process();

            // default settings
            exec.StartInfo.UseShellExecute = false;
            exec.StartInfo.CreateNoWindow = true;
            exec.StartInfo.RedirectStandardInput = true;
            exec.StartInfo.RedirectStandardOutput = true;
            exec.StartInfo.RedirectStandardError = false; // TODO: Add stderr log
            exec.StartInfo.FileName = executable;
            exec.StartInfo.Arguments = arguments.JoinQuoteSpace();

            return exec;
        }

        public static Stream RunWithOutput(string executable, Stream stderr = null, params string[] arguments)
        {
            Process exec = Generate(executable, arguments);
            exec.StartInfo.RedirectStandardError = stderr != null;

            exec.Start();
            exec.StandardInput.Close();

            if (stderr != null)
                Task.Run(() => exec.StandardError.BaseStream.CopyTo(stderr));
            return new ProcessStream(exec, ProcessPipeType.Stdout);
        }

        public static void RunWithInput(string executable, Stream input, Stream stderr = null, params string[] arguments)
        {
            Process exec = Generate(executable, arguments);
            exec.StartInfo.RedirectStandardError = stderr != null;

            exec.Start();
            input.CopyTo(exec.StandardInput.BaseStream, 2 << 24);
            exec.StandardInput.Close();

            if (stderr != null)
                Task.Run(() => exec.StandardError.BaseStream.CopyTo(stderr));
            exec.EnsureExit();
        }

        public static void EnsureExit(this Process process)
        {
            process.WaitForExit();
            if (process.ExitCode != 0)
                throw new ExecutionException("Process ended with non-zero return value")
                { ExitCode = process.ExitCode };
        }
    }

    public class ExecutionException : ApplicationException
    {
        public int ExitCode { get; set; }

        public ExecutionException() : base() { }
        public ExecutionException(string error) : base(error) { }
        public ExecutionException(string error, Exception inner) : base(error, inner) { }
    }
}
