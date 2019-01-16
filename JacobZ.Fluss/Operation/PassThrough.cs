using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using SharpCompress.Archives;
using JacobZ.Fluss.Utils;

namespace JacobZ.Fluss.Operation
{
    class PassThrough : IArchiveEntryOperation
    {
        public void Execute(IArchiveEntry[] entryIndices, params string[] outputPath)
        {
            StreamHelper.EnsureFilePath(outputPath);
            using (var fin = entryIndices[0].OpenEntryStream())
            using (var fout = File.OpenWrite(outputPath[0]))
                fin.CopyTo(fout);
        }

        public string[] Pass(params IArchiveEntry[] archiveEntries)
        {
            var entry = archiveEntries[0].Key;
            return new string[] { Path.GetFileNameWithoutExtension(entry) + ".copy" + Path.GetExtension(entry) };
        }
    }
}
