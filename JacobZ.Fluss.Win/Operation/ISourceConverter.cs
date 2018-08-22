using System;
using System.Threading.Tasks;

namespace JacobZ.Fluss.Win.Operation
{
    interface ISourceConverter
    {
        bool CheckUsable(string targetFile);
        string[] GetExpectedOutputs(string targetFile);
        Task Apply(string targetFile, string outputfile, IProgress<double> progress);
    }
}
