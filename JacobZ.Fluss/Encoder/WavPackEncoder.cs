using System;
using System.Diagnostics;
using System.IO;

namespace JacobZ.Fluss.Encoder
{
    using JacobZ.Fluss.Utils;

    public class WavPackEncoder : IAudioEncoder
    {
        string _wvpack, _wvunpack;

        public WavPackEncoder(string wavpackPath, string wvunpackPath)
        {
            _wvpack = wavpackPath;
            _wvunpack = wvunpackPath;
        }

        public WavPackEncoder(string wavpackPath)
        {
            _wvpack = wavpackPath;
            _wvunpack = Path.Combine(Path.GetDirectoryName(wavpackPath), "wvunpack" + Path.GetExtension(wavpackPath));
        }

        public void Decode(Stream output, string inputFile)
        {
            Process exec = ProcessHelper.Generate(_wvunpack, inputFile, "-");
            exec.Start();
            exec.StandardOutput.BaseStream.CopyTo(output);
            exec.EnsureExit();
        }

        public void Encode(Stream input, string outputFile)
        {
            Process exec = ProcessHelper.Generate(_wvpack, "-c", "-", outputFile);
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
