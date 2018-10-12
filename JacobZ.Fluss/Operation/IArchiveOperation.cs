using System;
using System.Collections.Generic;
using System.Text;
using SharpCompress.Archives;

namespace JacobZ.Fluss.Operation
{
    interface IArchiveEntryOperation
    {
        bool CheckCompatibilty(IArchiveEntry entry);

        void Execute(string outputPath, params IArchiveEntry[] entry);
    }
    
    interface IArchiveOperation
    {
        bool CheckCompatibility(IArchive archive);

        void Execute(string outputPath, IArchive archive);
    }
}
