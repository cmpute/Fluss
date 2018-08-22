using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using JacobZ.Fluss.AudioCodec;

namespace JacobZ.Fluss.Win.Operation
{
    class AudioConverter : ISourceConverter
    {
        private const string EXT_Wave = ".wav";
        private const string EXT_FreeLossless = ".flac";
        private const string EXT_TrueAudio = ".tta";
        private const string EXT_WavPack = ".wv";

        public static readonly string[] SupportedFormats = { EXT_Wave, EXT_FreeLossless, EXT_TrueAudio, EXT_WavPack};

        string _tformat;

        public AudioConverter(string targetFormat)
        {
            if (!SupportedFormats.Contains(targetFormat))
                throw new NotSupportedException();
            _tformat = targetFormat;
        }

        public IAudioCodec GetCodecFromExt(string extension)
        {
            switch (extension)
            {
                default:
                case EXT_Wave:
                    return null;
                case EXT_TrueAudio:
                    return new TTA(Utils.ProgramFinder.FindAudioEncoder<TTA>());
            }
        }

        public async Task Apply(string targetFile, string outputfile, IProgress<double> progress)
        {
            var decoder = GetCodecFromExt(Path.GetExtension(targetFile));
            var encoder = GetCodecFromExt(_tformat);

            await Task.Run(() =>
            {
                MemoryStream ms = new System.IO.MemoryStream();
                decoder.Decode(ms, targetFile);
                ms.Seek(0, System.IO.SeekOrigin.Begin);
                encoder.Encode(ms, outputfile);
            });
        }

        public bool CheckUsable(string targetFile)
        {
            return SupportedFormats.Contains(targetFile);
        }

        public string[] GetExpectedOutputs(string targetFile)
        {
            string name = Path.GetFileNameWithoutExtension(targetFile);

            if (_tformat == ".wv")
                return new string[] { name + ".wv", name + ".wvc" };
            else return new string[] { name + _tformat };    
        }
    }
}
