using System;
using System.Collections.Generic;
using System.Text;

namespace JacobZ.Fluss.Metadata
{
    public class AlbumFolder
    {
        // folder name
        public string Name { get; set; }
        // "DISC" in tag (e.g. "1/2"), or "DISCNUMBER/DISCTOTAL"
        public byte DiscNumber { get; set; }
        // "REM DISCID" in cue, "DISCID" in tag
        public string DiscID { get; set; }
        // "CATALOG" in cue, "CATALOG" in tag
        public string Catalog { get; set; }
        // 品番
        public string PartNumber { get; set; }
        public string Edition { get; set; }
        public string Tool { get; set; }
        public string Source { get; set; }
        public string Ripper { get; set; }
        // "REM COMMENT" in cue, "COMMENT" in tag
        public string Comment { get; set; }
        public Dictionary<Database, string> Databases { get; set; }
    }
}
