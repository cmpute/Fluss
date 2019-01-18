using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using SharpCompress.Archives;
using JacobZ.Fluss.Utils;

namespace JacobZ.Fluss.Operation
{
    public class PassThrough : IArchiveEntryOperation
    {
        public struct Meta { }
        Meta _props;
        public object Properties { get => _props; set => _props = (Meta)value; }

        public void Execute(IArchiveEntry[] entryIndices, params string[] outputPath)
        {
            StreamHelper.EnsureFilePath(outputPath);
            using (var fin = entryIndices[0].OpenEntryStream())
            using (var fout = File.OpenWrite(outputPath[0]))
                fin.CopyTo(fout);
        }

        public string[] Pass(params IArchiveEntry[] archiveEntries)
        {
            if (archiveEntries.Length > 1) return null;
            var entry = archiveEntries[0].Key;
            return new string[] { Path.GetFileNameWithoutExtension(entry) + ".copy" + Path.GetExtension(entry) };
        }
    }
}
