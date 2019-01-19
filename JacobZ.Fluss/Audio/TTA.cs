using System;
using System.Diagnostics;
using System.IO;

namespace JacobZ.Fluss.Audio
{
    using JacobZ.Fluss.Utils;

    public class TTA : IPcmCodec
    {
        public static string TTAPath { get; set; }

        public Stream Decode(string inputFile)
        {
            return ProcessHelper.RunWithOutput(TTAPath, null, "-d", inputFile, "-");
        }

        public void Encode(string outputFile, Stream input)
        {
            ProcessHelper.RunWithInput(TTAPath, input, null, "-e", "-", outputFile);
        }
    }
}
