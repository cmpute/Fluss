using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using SharpCompress.Archives;
using SharpCompress.Common;
using SharpCompress.Readers;

namespace JacobZ.Fluss.Utils
{
    public class DirectoryArchive : IArchive
    {
        public DirectoryInfo _dir;
        public DirectoryArchive(string directory)
        {
            _dir = new DirectoryInfo(directory);
        }

        public IEnumerable<IArchiveEntry> Entries => Directory.EnumerateFiles(_dir.FullName)
            .Select(file => new DirectoryArchiveEntry(file, _dir));

        public IEnumerable<IVolume> Volumes => null;
        public ArchiveType Type => throw new InvalidOperationException();
        public bool IsSolid => false;
        public bool IsComplete => true;
        public long TotalSize => Entries.Sum(entry => entry.Size);
        public long TotalUncompressSize => Entries.Sum(entry => entry.Size);

        public event EventHandler<ArchiveExtractionEventArgs<IArchiveEntry>> EntryExtractionBegin;
        public event EventHandler<ArchiveExtractionEventArgs<IArchiveEntry>> EntryExtractionEnd;
        public event EventHandler<CompressedBytesReadEventArgs> CompressedBytesRead;
        public event EventHandler<FilePartExtractionBeginEventArgs> FilePartExtractionBegin;

        public void Dispose() { }
        public IReader ExtractAllEntries() { return null; }
    }

    public class DirectoryArchiveEntry : IArchiveEntry
    {
        internal FileInfo File { get; set; }
        internal DirectoryInfo Root { get; set; }

        // Construct dummy
        public DirectoryArchiveEntry(string file)
        {
            File = new FileInfo(file);
            Root = null;
        }

        public DirectoryArchiveEntry(string file, DirectoryInfo root)
        {
            File = new FileInfo(file);
            Root = root;
        }

        #region IEntry
        public DateTime? ArchivedTime => null;
        public int? Attrib => (int)File.Attributes;
        public long CompressedSize => File.Length;
        public CompressionType CompressionType => CompressionType.None;
        public long Crc => throw new NotImplementedException();
        public DateTime? CreatedTime => File.CreationTime;
        public bool IsDirectory => false;
        public bool IsEncrypted => false;
        public bool IsSplitAfter => false;
        public DateTime? LastAccessedTime => File.LastAccessTime;
        public DateTime? LastModifiedTime => null;
        public long Size => File.Length;
        public string Key => Root == null ? File.Name : File.FullName.Substring(Root.FullName.Length);
        #endregion

        #region IArchiveEntry
        public bool IsComplete => true;
        public IArchive Archive => Root == null ? null : new DirectoryArchive(Root.FullName);
        public Stream OpenEntryStream() => File.Open(FileMode.Open);
        #endregion
    }
}
