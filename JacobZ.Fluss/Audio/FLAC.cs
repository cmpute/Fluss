using System;
using System.Diagnostics;
using System.IO;

namespace JacobZ.Fluss.Audio
{
    using JacobZ.Fluss.Utils;

    public class FLAC : IPcmCodec
    {
        public static string FLACPath { get; set; }
        
        public Stream Decode(string inputFile)
        {
            return ProcessHelper.RunWithOutput(FLACPath, null, "-b", "-c", inputFile);
        }

        public void Encode(string outputFile, Stream input)
        {
            ProcessHelper.RunWithInput(FLACPath, input, null, "-", "-o", outputFile);
        }
    }
}
