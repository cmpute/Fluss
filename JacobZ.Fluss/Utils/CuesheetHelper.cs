using System;
using System.Collections.Generic;
using System.Text;

namespace JacobZ.Fluss.Utils
{
    /// <remarks> http://wiki.hydrogenaud.io/index.php?title=Cue_sheet </remarks>
    class Cuesheet
    {
        public string Catalog { get; set; }
        public string CDTextFile { get; set; }
        public string File { get; set; }
        public string Remarks { get; set; }
        public string Performer { get; set; }
        public string Title { get; set; }
        public CuesheetTrack[] Tracks { get; set; }

        public void Deserialize(string content)
        {
            throw new NotImplementedException();
        }

        public string Serialize()
        {
            throw new NotImplementedException();
        }
    }

    class CuesheetTrack
    {
        public string Performer { get; set; }
        public string ISRC { get; set; }
        public string Flags { get; set; }
        public string Songwriter { get; set; }
        public string Title { get; set; }
        public string PreGap { get; set; }
        public string PostGap { get; set; }
    }
}
