using System;
using System.Collections.Generic;
using System.Text;
using System.Linq;
using System.IO;
using SharpCompress.Archives;

namespace JacobZ.Fluss.Operation
{
    public class FixCuesheet : IArchiveEntryOperation
    {
        public void Execute(IArchiveEntry[] entries, params string[] outputPath)
        {
            var cueentry = entries.First(et => et.Key.EndsWith(".cue"));
            var encoding = FixEncoding.DetectEncoding(cueentry);
            var stream = cueentry.OpenEntryStream();
            var sr = new StreamReader(stream, encoding);

            List<string> content = new List<string>();
            List<string> entryNames = entries.Select(et => Path.GetFileName(et.Key)).ToList();
            while (!sr.EndOfStream)
            {
                var line = sr.ReadLine();
                if(!line.StartsWith("FILE "))
                {
                    content.Add(line);
                    continue;
                }

                var wavename = line.Substring(6, line.IndexOf('"', 6));
                var cuename = Path.GetFileNameWithoutExtension(cueentry.Key);
                var cuepath = Path.GetDirectoryName(cueentry.Key);

                foreach (var ext in Audio.WaveFormat.WaveExtensions)
                {
                    if (entryNames.Contains(wavename + ext))
                    {
                        content.Add($"FILE \"{wavename + ext}\" WAVE");
                        break;
                    }
                    else if(entryNames.Contains(cuename + ext))
                    {
                        content.Add($"FILE \"{cuename + ext}\" WAVE");
                        break;
                    }
                }
                throw new Exception("Cannot find correspond wave file for the cuesheet!");
            }

            var sw = new StreamWriter(File.OpenWrite(outputPath[0]), FixEncoding.UTF8_BOM); // Add BOM by default for foobar
            sw.Write(string.Join(Environment.NewLine, content));
            sr.Close(); sw.Close();
        }

        public string[] Pass(params IArchiveEntry[] entries)
        {
            var cueentry = entries.FirstOrDefault(et => et.Key.EndsWith(".cue"));
            if(cueentry != null) return new string[] { cueentry.Key };
            else return null;
        }
    }
}
