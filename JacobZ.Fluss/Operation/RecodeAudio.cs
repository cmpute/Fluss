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

        public struct Meta
        {
            public AudioCodecType Type { get; set; }
        }
        Meta _props = new Meta() { Type = AudioCodecType.Wavpack };
        public object Properties { get => _props; set => _props = (Meta)value; }

        public void Execute(IArchiveEntry[] entryIndices, params string[] outputPath)
        {
            StreamHelper.EnsureFilePath(TempPath);
            StreamHelper.EnsureFilePath(outputPath);
            IPcmCodec decoder = null, encoder = null;
            string input = Path.Combine(TempPath, Path.GetFileName(entryIndices[0].Key));
            string input2 = null;

            // Select codec
            string fext = Path.GetExtension(entryIndices[0].Key).ToLower();
            AudioCodecType tdec = AudioCodecFactory.ParseCodec(fext);
            decoder = AudioCodecFactory.GetCodec(tdec);
            encoder = AudioCodecFactory.GetCodec(_props.Type);

            // Decompress audio file
            using (var fin = entryIndices[0].OpenEntryStream())
            using (var fout = File.OpenWrite(input))
                fin.CopyTo(fout);
            if (tdec == AudioCodecType.Wavpack)
            {
                string finame = Path.GetFileNameWithoutExtension(entryIndices[0].Key) + ".wvc";
                input2 = Path.Combine(TempPath, finame);
                var wvcfiles = entryIndices[0].Archive.Entries.Where(entry => Path.GetFileName(entry.Key) == finame).ToArray();
                if (wvcfiles.Length > 0)
                {
                    using (var fin = wvcfiles[0].OpenEntryStream())
                    using (var fout = File.OpenWrite(input2))
                        fin.CopyTo(fout);
                }
            }

            // Recode
            var ts = decoder.Decode(input, PcmEncodingType.RAW);
            encoder.Encode(outputPath[0], ts, PcmEncodingType.RAW);

            // Clear temp files
            File.Delete(input);
            if (input2 != null) File.Delete(input2); // delete input wvc file
            if (_props.Type == AudioCodecType.Wavpack && outputPath.Length > 1) // move output wvc file
            {
                string fwv, fwvc;
                if(Path.GetExtension(outputPath[0]) == ".wv")
                {
                    fwv = outputPath[0];
                    fwvc = outputPath[1];
                }
                else
                {
                    fwvc = outputPath[0];
                    fwv = outputPath[1];
                }
                if (Path.GetDirectoryName(fwvc) != Path.GetDirectoryName(fwv))
                    File.Move(fwv + "c", fwvc);
            }
        }

        public string[] Pass(params IArchiveEntry[] archiveEntries)
        {
            if (archiveEntries.Length > 1) return null;
            var fname = archiveEntries[0].Key;
            var fext = Path.GetExtension(fname).ToLower();
            var oname = Path.GetFileNameWithoutExtension(fname);

            // Check input
            var tdec = AudioCodecFactory.ParseCodec(fext);
            if (tdec == AudioCodecType.Unknown) return null;

            // Generate output
            switch (_props.Type)
            {
                case AudioCodecType.Wavpack:
                    return new string[] { oname + ".wv", oname + ".wvc" };
            }
            return null;
        }
    }
}
