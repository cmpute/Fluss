using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using JacobZ.Fluss.Audio;
using JacobZ.Fluss.Utils;
using SharpCompress.Archives;
using TagLib;

namespace JacobZ.Fluss.Operation
{
    public class EmbedMetadata : IArchiveEntryOperation
    {
        public struct Meta { }
        Meta _props;
        public object Properties { get => _props; set => _props = (Meta)value; }

        public void Execute(IArchiveEntry[] archiveEntries, params string[] outputPath)
        {
            // Interpret input
            IArchiveEntry audio = null, cuesheet = null, cover = null;
            foreach (var entry in archiveEntries)
            {
                var fext = Path.GetExtension(entry.Key).ToLower();
                if (fext == ".cue") cuesheet = entry;
                else if (ImageCodecFactory.ParseCodec(fext) != ImageCodecType.Unknown) cover = entry;
                else if (AudioCodecFactory.ParseCodec(fext) != AudioCodecType.Unknown) audio = entry;
            }

            // Copy if it's not in same position
            if (!(audio is DirectoryArchiveEntry) || (audio as DirectoryArchiveEntry).Root.FullName +
                (audio as DirectoryArchiveEntry).Key != outputPath[0])
            {
                using (var fin = audio.OpenEntryStream())
                using (var fout = System.IO.File.OpenWrite(outputPath[0]))
                    fin.CopyTo(fout);
            }

            // Embed
            var tag = TagLib.File.Create(outputPath[0]);
            var apetag = tag.GetTag(TagTypes.Ape, true) as TagLib.Ape.Tag;

            string strcue = null;
            using (var fcue = cuesheet.OpenEntryStream())
            using (var sr = new StreamReader(fcue))
                strcue = sr.ReadToEnd();
            apetag.AddValue("CUESHEET", strcue);

            Picture cpic = null;
            using (var fcover = cover.OpenEntryStream())
            using (var sr = new BinaryReader(fcover))
                cpic = new Picture(new ByteVector(sr.ReadBytes((int)fcover.Length)));
            cpic.Type = PictureType.FrontCover;
            cpic.MimeType = "image/jpeg";
            apetag.Pictures = new IPicture[] { cpic };

            tag.Save();
        }

        public string[] Pass(params IArchiveEntry[] archiveEntries)
        {
            if (archiveEntries.Length < 2) return null;

            IArchiveEntry audio = null, cuesheet = null, cover = null;
            foreach (var entry in archiveEntries)
            {
                var fext = Path.GetExtension(entry.Key).ToLower();
                if (fext == ".cue") cuesheet = entry;
                else if (ImageCodecFactory.ParseCodec(fext) != ImageCodecType.Unknown) cover = entry;
                else if (AudioCodecFactory.ParseCodec(fext) != AudioCodecType.Unknown) audio = entry;
                else return null; // Unknown input
            }

            if (audio == null) return null; // Audio input is needed
            return new string[] { Path.GetFileName(audio.Key) }; // Use the same filename
        }
    }
}
