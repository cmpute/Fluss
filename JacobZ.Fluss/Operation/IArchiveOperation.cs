using System;
using System.Collections.Generic;
using System.Text;
using SharpCompress.Archives;

namespace JacobZ.Fluss.Operation
{
    interface IArchiveOperation
    {
        bool CheckCompatibilty(IArchiveEntry entry);

        void Execute(IArchiveEntry entry, string outputPath);
    }
}
