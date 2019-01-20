﻿using System;
using System.IO;
using System.Collections.Generic;
using System.Linq;
using JacobZ.Fluss.Metadata;
using SharpCompress.Archives;

namespace JacobZ.Fluss
{
    public class MusicArchive
    {
        private string _root;
        private List<IArchiveEntry> _entries;
        private Album _meta;

        public MusicArchive(IArchive archive, string rootPath)
        {
            _root = rootPath;
            _entries = archive.Entries.Where(entry => !entry.IsDirectory).ToList();
            _entries.Sort((e1, e2) => e1.Key.CompareTo(e2.Key));
        }
        public IList<IArchiveEntry> Entries => _entries;
        public string Root => _root;
        public IEnumerable<IArchiveEntry> SelectEntries(params int[] indices)
            => indices.Select(idx => _entries[idx]);
    }
}