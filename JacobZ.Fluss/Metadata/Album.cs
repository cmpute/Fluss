using System;
using System.Collections.Generic;
using System.Text;

namespace JacobZ.Fluss.Metadata
{
    public class Album
    {
        // "TITLE" in cue, "ALBUM" in tag
        public string Title { get; set; }
        public string Publisher { get; set; }
        public string Vendor { get; set; }
        // "PERFORMER" in cue, "ALBUM ARTIST" in tag
        public string Artist { get; set; }
        public Dictionary<ItemType, string> Association { get; set; }
        public List<AlbumFolder> Folders { get; set; }
        public string Event { get; set; }
        // "REM DATE" in cue, "YEAR" in tag
        public string Year { get; set; }
        // "REM GENRE" in cue, "GENRE" in tag
        public string Genre { get; set; }
    }
}
