using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using JacobZ.Fluss.Audio;
using JacobZ.Fluss.Utils;
using SharpCompress.Archives;

namespace JacobZ.Fluss.Operation
{
    public class EmbedCuesheet : IArchiveEntryOperation
    {
        public struct Meta { }
        Meta _props;
        public object Properties { get => _props; set => _props = (Meta)value; }

        public void Execute(IArchiveEntry[] archiveEntries, params string[] outputPath)
        {
            // Interpret input
            IArchiveEntry audio = null, cuesheet = null;
            foreach (var entry in archiveEntries)
            {
                var fext = Path.GetExtension(entry.Key).ToLower();
                if (fext == ".cue") cuesheet = entry;
                else if (CodecFactory.ParseCodec(fext) != CodecType.Unknown) audio = entry;
            }

            // Copy if it's not in same position
            if (!(audio is DirectoryArchiveEntry) || (audio as DirectoryArchiveEntry).Root.FullName + 
                (audio as DirectoryArchiveEntry).Key != outputPath[0])
            {
                using (var fin = audio.OpenEntryStream())
                using (var fout = File.OpenWrite(outputPath[0]))
                    fin.CopyTo(fout);
            }

            // Embed
            string strcue = null;
            using (var fcue = cuesheet.OpenEntryStream())
            using (var sr = new StreamReader(fcue))
                strcue = sr.ReadToEnd();

            var tag = TagLib.File.Create(outputPath[0]);
            (tag.GetTag(TagLib.TagTypes.Ape, true) as TagLib.Ape.Tag).AddValue("CUESHEET", strcue);
            tag.Save();
        }

        public string[] Pass(params IArchiveEntry[] archiveEntries)
        {
            if (archiveEntries.Length < 2) return null;

            IArchiveEntry audio = null, cuesheet = null;
            foreach (var entry in archiveEntries)
            {
                var fext = Path.GetExtension(entry.Key).ToLower();
                if (fext == ".cue") cuesheet = entry;
                else if (CodecFactory.ParseCodec(fext) != CodecType.Unknown) audio = entry;
                else return null;
            }

            if (audio == null || cuesheet == null) return null;
            return new string[] { Path.GetFileName(audio.Key) }; // Use the same filename
        }
    }
}
