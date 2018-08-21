using System;
using System.Diagnostics;
using System.IO;

namespace JacobZ.Fluss.Encoder
{
    using JacobZ.Fluss.Utils;

    public class TTAEncoder : IAudioEncoder
    {
        string _tta;

        public TTAEncoder(string ttaPath) { _tta = ttaPath; }

        public void Decode(Stream output, string inputFile)
        {
            Process exec = ProcessHelper.Generate(_tta, "-d", inputFile, "-");
            exec.Start();
            exec.StandardOutput.BaseStream.CopyTo(output);
            exec.EnsureExit();
        }

        public void Encode(Stream input, string outputFile)
        {
            Process exec = ProcessHelper.Generate(_tta, "-e", "-", outputFile);
            exec.Start();
            input.CopyTo(exec.StandardInput.BaseStream);
            exec.StandardInput.Close();
            exec.EnsureExit();
        }

        public void ReadTags(string input)
        {
            throw new NotImplementedException();
        }

        public void WriteTags(string output)
        {
            throw new NotImplementedException();
        }
    }
}
