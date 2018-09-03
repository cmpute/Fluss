using System;
using System.IO;
using System.Threading.Tasks;

namespace JacobZ.Fluss.Win.Operations
{
    class CopyOperation : ISourceOperation
    {
        public async Task Apply(string sourceFile, string outputfile, IProgress<double> progress)
        {
            using (var istream = new FileStream(sourceFile, FileMode.Open, FileAccess.Read, FileShare.Read,
                4096, FileOptions.Asynchronous | FileOptions.SequentialScan))
            using (var ostream = new FileStream(outputfile, FileMode.CreateNew, FileAccess.Write, FileShare.None,
                4096, FileOptions.Asynchronous | FileOptions.SequentialScan))
                await istream.CopyToAsync(ostream);
        }

        public bool CheckUsable(string sourceFile)
        {
            return true;
        }

        public string Name => "复制文件";

        public string[] GetExpectedOutputs(string sourceFile)
        {
            return new string[] { Path.GetFileName(sourceFile) };
        }
    }
}
