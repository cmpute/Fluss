using System;
using System.Diagnostics;
using System.IO;

namespace JacobZ.Fluss.Audio
{
    using JacobZ.Fluss.Utils;

    public class TTA : IPcmCodec
    {
        string _tta;

        public TTA(string ttaPath) { _tta = ttaPath; }

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
