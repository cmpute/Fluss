using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using JacobZ.Fluss.Audio;
using JacobZ.Fluss.Utils;
using SharpCompress.Archives;

namespace JacobZ.Fluss.Operation
{
    // Note: Add checksum verification
    public class RecodeAudio : IArchiveEntryOperation
    {
        private static readonly string TempPath = Path.Combine(Path.GetTempPath(), "fluss", "audio\\");

        public delegate void FindRequiredCodec(AudioType ext);
        public static FindRequiredCodec CodecFinder { get; set; }

        public enum AudioType
        {
            Wavpack, // .wv
            TTA, // .tta
        }

        public struct Meta
        {
            public AudioType Type { get; set; }
        }
        Meta _props;
        public object Properties { get => _props; set => _props = (Meta)value; }

        public void Execute(IArchiveEntry[] entryIndices, params string[] outputPath)
        {
            StreamHelper.EnsureFilePath(TempPath);
            StreamHelper.EnsureFilePath(outputPath);
            IPcmCodec decoder = null, encoder = null;
            string input = Path.Combine(TempPath, Path.GetFileName(entryIndices[0].Key));
            string input2 = null;

            // Select decoder
            string fext = Path.GetExtension(entryIndices[0].Key).ToLower();
            switch (fext)
            {
                case ".wv":
                    decoder = new WavPack();
                    CodecFinder(AudioType.Wavpack);

                    // Decompress wvc file
                    string finame = Path.GetFileNameWithoutExtension(entryIndices[0].Key) + ".wvc";
                    input2 = Path.Combine(TempPath, finame);
                    var wvcfiles = entryIndices[0].Archive.Entries.Where(entry => Path.GetFileName(entry.Key) == finame).ToArray();
                    if (wvcfiles.Length > 0)
                    {
                        using (var fin = wvcfiles[0].OpenEntryStream())
                        using (var fout = File.OpenWrite(input2))
                            fin.CopyTo(fout);
                    }
                    break;
                case ".tta":
                    decoder = new TTA();
                    CodecFinder(AudioType.TTA);
                    break;
            }

            // Decompress audio file
            using (var fin = entryIndices[0].OpenEntryStream())
            using (var fout = File.OpenWrite(input))
                fin.CopyTo(fout);

            // Select encoder
            switch (_props.Type)
            {
                case AudioType.Wavpack:
                    encoder = new WavPack();
                    CodecFinder(AudioType.Wavpack);
                    break;
                case AudioType.TTA:
                    decoder = new TTA();
                    CodecFinder(AudioType.TTA);
                    break;
            }

            // Recode
            var ts = decoder.Decode(input, PcmEncodingType.RAW);
            encoder.Encode(outputPath[0], ts, PcmEncodingType.RAW);

            // Clear temp files
            File.Delete(input);
            if (input2 != null) File.Delete(input2);
        }

        public string[] Pass(params IArchiveEntry[] archiveEntries)
        {
            if (archiveEntries.Length > 1) return null;
            var fname = archiveEntries[0].Key;
            var fext = Path.GetExtension(fname).ToLower();
            var oname = Path.GetFileName(fname);

            // Check input
            switch (fext)
            {
                default: return null;
                case ".wv":
                case ".tta":
                    break;
            }

            // Generate output
            switch (_props.Type)
            {
                case AudioType.Wavpack:
                    return new string[] { oname + ".wv", oname + ".wvc" };
            }
            return null;
        }
    }
}
