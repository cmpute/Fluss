using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using SharpCompress.Archives;
using Ude;

namespace JacobZ.Fluss.Operation
{
    public class FixEncoding : IArchiveEntryOperation
    {
        internal static readonly Encoding UTF8_BOM = new UTF8Encoding(true);

        public static Encoding DetectEncoding(IArchiveEntry entry)
        {
            var stream = entry.OpenEntryStream();

            // Select None-ASCII encodings
            List<byte> candidates = new List<byte>();
            int value = stream.ReadByte();
            while (value >= 0)
            {
                if (value == 0 || value > 127) // skip normall ASCII chars
                {
                    // read two bytes
                    candidates.Add((byte)value);
                    candidates.Add((byte)stream.ReadByte());
                }
                value = stream.ReadByte();
            }
            stream.Close(); // stream.Seek(0, SeekOrigin.Begin);

            // Get encodings
            Encoding encoding = Encoding.ASCII;
            if (candidates.Count > 0)
            {
                var detector = new CharsetDetector();
                detector.Feed(candidates.ToArray(), 0, candidates.Count);
                detector.DataEnd();
                switch (detector.Charset)
                {
                    case Charsets.SHIFT_JIS:
                        encoding = Encoding.GetEncoding(932);
                        break;
                    case Charsets.BIG5:
                        encoding = Encoding.GetEncoding(950);
                        break;
                    case Charsets.HZ_GB_2312:
                        encoding = Encoding.GetEncoding(936);
                        break;
                    case Charsets.GB18030:
                        encoding = Encoding.GetEncoding(54936);
                        break;
                    case Charsets.UTF8:
                        encoding = Encoding.UTF8;
                        break;
                };
            }
            return encoding;
        }

        public void Execute(IArchiveEntry[] entries, params string[] outputPath)
        {
            var entry = entries[0];
            var encoding = DetectEncoding(entry);
            var stream = entry.OpenEntryStream();
            var sr = new StreamReader(stream, encoding);
            var sw = new StreamWriter(File.OpenWrite(outputPath[0]), UTF8_BOM); // Add BOM by default for foobar
            sw.Write(sr.ReadToEnd());
            sr.Close(); sw.Close();
        }

        readonly string[] SupportText = new string[] { ".log", ".txt", ".cue" };
        public string[] Pass(params IArchiveEntry[] entries)
        {
            if (entries.Count() > 0) return null;
            var entry = entries[0];
            var ext = Path.GetExtension(entry.Key);
            if (SupportText.Contains(ext)) return new string[] { entry.Key };
            else return null;
        }
    }
}
