using System;
using System.Collections.Generic;
using System.IO;
using System.Text;

namespace JacobZ.Fluss.Audio
{
    public class Wave : IPcmCodec
    {
        // TODO: Convert various WAV format into RIFF to do splitting and checksuming
        public Stream Decode(string inputFile)
        {
            return File.OpenRead(inputFile);
        }

        public void Encode(string outputFile, Stream input)
        {
            using (var fout = File.OpenWrite(outputFile))
                input.CopyTo(fout);
        }
    }
}
