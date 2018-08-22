using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using JacobZ.Fluss.Archiver;
using JacobZ.Fluss.AudioCodec;

namespace JacobZ.Fluss.Win.Utils
{
    static class ProgramFinder
    {
        public static string FindArchiver<Archiver>()
            where Archiver : IArchiver
        {
            var archiver = typeof(Archiver);
            if (archiver == typeof(RAR))
                return Frar();
            else return null;
        }

        public static string FindAudioEncoder<Codec>()
            where Codec : IAudioCodec
        {
            var codec = typeof(Codec);
            if (codec == typeof(TTA))
                return Ftta();
            else if (codec == typeof(WavPack))
                return Fwavpack();
            else return null;
        }

        public static string FindAudioDecoder<Codec>()
            where Codec : IAudioCodec
        {
            var codec = typeof(Codec);
            if (codec == typeof(TTA))
                return Ftta();
            else if (codec == typeof(WavPack))
                return Fwvunpack();
            else return null;
        }

        private static string Fwavpack()
        {
            throw new NotImplementedException();
        }

        private static string Fwvunpack()
        {
            throw new NotImplementedException();
        }

        private static string Ftta()
        {
            throw new NotImplementedException();
        }

        private static string Frar()
        {
            throw new NotImplementedException();
        }
    }
}
