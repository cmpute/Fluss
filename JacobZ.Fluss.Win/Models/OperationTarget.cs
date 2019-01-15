using System;
using System.Collections.Generic;
using SharpCompress.Archives;

namespace JacobZ.Fluss.Win.Models
{
    sealed class OperationTarget
    {
        public MusicArchive Archive { get; set; }
        public int EntryIndex { get; set; }
        public bool IsSource { get; set; }

        public IArchiveEntry Entry => Archive.Entries[EntryIndex];
        public string FilePath => Entry.Key;
    }
}
