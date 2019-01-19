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
            return ProcessHelper.RunWithOutput(wvunpack, null, inputFile, "-");
        }

        public void Encode(string outputFile, Stream input, PcmEncodingType type)
        {
            ProcessHelper.RunWithInput(WavPackPath, input, null, "-b192", "-c", "-", outputFile);
        }
    }
}
