using System;
using System.Diagnostics;
using System.IO;

namespace JacobZ.Fluss.Audio
{
    using JacobZ.Fluss.Utils;

    public class FLAC : IPcmCodec
    {
        string _flac;

        public FLAC(string flacPath)
        {
            _flac = flacPath;
        }
        
        public Stream Decode(string inputFile, PcmEncodingType type)
        {
            Process exec = ProcessHelper.Generate(_flac, "-b", "-c", inputFile);
            exec.StandardInput.Close();
            exec.Start();
            return new ProcessStream(exec, ProcessPipeType.Stdout);
        }

        public void Encode(string outputFile, Stream input, PcmEncodingType type)
        {
            Process exec = ProcessHelper.Generate(_flac, "-", "-o", outputFile);
            exec.Start();
            input.CopyTo(exec.StandardInput.BaseStream);
            exec.StandardInput.Close();
            exec.EnsureExit();
        }
    }
}
