using System;
using System.Collections.Generic;
using System.IO;
using System.Text;

namespace JacobZ.Fluss.Utils
{
    /// <remarks> http://wiki.hydrogenaud.io/index.php?title=Cue_sheet </remarks>
    public class Cuesheet
    {
        public Dictionary<string, string> Remarks { get; private set; } = new Dictionary<string, string>();
        public string Catalog { get; set; }
        public string CDTextFile { get; set; }
        public string Performer { get; set; }
        public string Songwriter { get; set; }
        public string Title { get; set; }
        public List<CuesheetFileReference> Files { get; set; } = new List<CuesheetFileReference>();

        public void Deserialize(string content)
        {
            StringReader sr = new StringReader(content);
            CuesheetFileReference cur_file = null;
            List<CuesheetTrack> cur_tracks = null;
            CuesheetTrack cur_tr = null;
            List<CuesheetTrackIndex> cur_indices = null;

            while (true)
            {
                var line = sr.ReadLine();
                if (line == null) { break; }
                var terms = line.SplitQuoteSpace();
                switch (terms[0])
                {
                    case "CATALOG": { Catalog = terms[1]; break; }
                    case "REM": { Remarks.Add(terms[1], terms[2]); break; }
                    case "CDTEXTFILE": { CDTextFile = terms[1]; break; }
                    case "FLAGS": { cur_tr.Flags = terms[1]; break; }
                    case "ISRC": { cur_tr.ISRC = terms[1]; break; }
                    case "PREGAP": { cur_tr.PreGap = terms[1]; break; }
                    case "POSTGAP": { cur_tr.PostGap = terms[1]; break; }
                    case "TITLE":
                        if (cur_tr == null) Title = terms[1];
                        else cur_tr.Title = terms[1];
                        break; 
                    case "PERFORMER":
                        if (cur_tr == null) Performer = terms[1];
                        else cur_tr.Performer = terms[1];
                        break; 
                    case "SONGWRITER":
                        if (cur_tr == null) Songwriter = terms[1];
                        else cur_tr.Songwriter = terms[1];
                        break;
                    case "FILE": 
                        cur_tracks = new List<CuesheetTrack>();
                        cur_file = new CuesheetFileReference(terms[1], terms[2], cur_tracks);
                        Files.Add(cur_file);
                        break;
                    case "TRACK":
                        cur_indices = new List<CuesheetTrackIndex>();
                        cur_tr = new CuesheetTrack(terms[1], terms[2], cur_indices);
                        cur_tracks.Add(cur_tr);
                        break;
                    case "INDEX":
                        cur_indices.Add(new CuesheetTrackIndex(terms[1], terms[2]));
                        break;
                }
            }
        }

        public string Serialize()
        {
            var builder = new StringBuilder();

            foreach (var item in Remarks)
                if(item.Key == "COMMENT")
                    builder.AppendLine($"REM {item.Key} \"{item.Value}\"");
                else builder.AppendLine($"REM {item.Key} {item.Value}");
            if (Catalog != null) builder.AppendLine($"CATALOG {Catalog}");
            if (CDTextFile != null) builder.AppendLine($"CDTEXTFILE {CDTextFile}");
            if (Title != null) builder.AppendLine($"TITLE \"{Title}\"");
            if (Performer != null) builder.AppendLine($"PERFORMER \"{Performer}\"");
            if (Songwriter != null) builder.AppendLine($"SONGWRITER \"{Songwriter}\"");

            foreach (var file in Files)
            {
                builder.AppendLine($"FILE \"{file.Path}\" {file.Format}");
                foreach (var track in file.Tracks)
                {
                    builder.AppendLine($"  TRACK {track.Number:00} {track.Type}");
                    if (track.Title != null) { builder.AppendLine($"    TITLE \"{track.Title}\""); }
                    if (track.Performer != null) { builder.AppendLine($"    PERFORMER \"{track.Performer}\""); }
                    if (track.Songwriter != null) { builder.AppendLine($"    SONGWRITER \"{track.Songwriter}\""); }
                    foreach (var index in track.Indices)
                        builder.AppendLine($"    INDEX {index.Number:00} {index.Minute:00}:{index.Second:00}:{index.Frame:00}");
                }
            }

            return builder.ToString();
        }
    }
    public class CuesheetFileReference
    {
        public CuesheetFileReference(string path, string format, List<CuesheetTrack> tracks)
        {
            Path = path; Format = format; Tracks = tracks;
        }
        public string Path { get; set; }
        public string Format { get; set; }
        public List<CuesheetTrack> Tracks { get; private set; }
    }
    public class CuesheetTrack
    {
        public CuesheetTrack(string num, string type, List<CuesheetTrackIndex> indices)
        {
            Number = byte.Parse(num);
            Type = type;
            Indices = indices;
        }
        public byte Number { get; set; }
        public string Type { get; set; }
        public string Performer { get; set; }
        public string ISRC { get; set; }
        public string Flags { get; set; }
        public string Songwriter { get; set; }
        public string Title { get; set; }
        public string PreGap { get; set; }
        public string PostGap { get; set; }
        public List<CuesheetTrackIndex> Indices { get; set; }
    }

    public class CuesheetTrackIndex
    {
        public CuesheetTrackIndex(string num, string timing)
        {
            Number = byte.Parse(num);
            var ts = timing.Split(':');
            Minute = byte.Parse(ts[0]);
            Second = byte.Parse(ts[1]);
            Frame = byte.Parse(ts[2]);
        }
        public byte Number { get; set; }
        public byte Minute { get; set; }
        public byte Second { get; set; }
        public byte Frame { get; set; }
    }
}
