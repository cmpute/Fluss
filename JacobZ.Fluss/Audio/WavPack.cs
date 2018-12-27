using System;
using System.Diagnostics;
using System.IO;

namespace JacobZ.Fluss.Audio
{
    using JacobZ.Fluss.Utils;

    public class WavPack : IPcmCodec
    {
        public static string WavPackPath { get; set; }

        public Stream Decode(string inputFile, PcmEncodingType type)
        {
            var wvunpack = Path.Combine(Path.GetDirectoryName(WavPackPath), "wvunpack" + Path.GetExtension(WavPackPath));
            Process exec = ProcessHelper.Generate(wvunpack, inputFile, "-");
            exec.StandardInput.Close();
            exec.Start();
            return new ProcessStream(exec, ProcessPipeType.Stdout);
        }

        public void Encode(string outputFile, Stream input, PcmEncodingType type)
        {
            Process exec = ProcessHelper.Generate(WavPackPath, "-b192", "-c", "-", outputFile);
            exec.Start();
            input.CopyTo(exec.StandardInput.BaseStream);
            exec.StandardInput.Close();
            exec.EnsureExit();
        }
    }
}
