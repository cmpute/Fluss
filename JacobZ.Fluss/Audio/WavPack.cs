using System;
using System.Diagnostics;
using System.IO;

namespace JacobZ.Fluss.Audio
{
    using JacobZ.Fluss.Utils;

    public class WavPack : IPcmCodec
    {
        string _wvpack, _wvunpack;

        public WavPack(string wavpackPath, string wvunpackPath)
        {
            _wvpack = wavpackPath;
            _wvunpack = wvunpackPath;
        }
        public WavPack(string wavpackPath)
        {
            _wvpack = wavpackPath;
            _wvunpack = Path.Combine(Path.GetDirectoryName(wavpackPath), "wvunpack" + Path.GetExtension(wavpackPath));
        }

        public Stream Decode(string inputFile, PcmEncodingType type)
        {
            Process exec = ProcessHelper.Generate(_wvunpack, inputFile, "-");
            exec.StandardInput.Close();
            exec.Start();
            return new ProcessStream(exec, ProcessPipeType.Stdout);
        }

        public void Encode(string outputFile, Stream input, PcmEncodingType type)
        {
            Process exec = ProcessHelper.Generate(_wvpack, "-b192", "-c", "-", outputFile);
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
