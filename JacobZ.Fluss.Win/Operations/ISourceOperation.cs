using System;
using System.Threading.Tasks;

namespace JacobZ.Fluss.Win.Operations
{
    interface ISourceOperation
    {
        /// <summary>
        /// 判断该操作是否适用于指定文件
        /// </summary>
        /// <param name="sourceFile">源文件路径</param>
        /// <returns>代表是否合适的布尔值</returns>
        bool CheckUsable(string sourceFile);

        /// <summary>
        /// 提取可能的输出文件名
        /// </summary>
        /// <param name="sourceFile">源文件路径</param>
        /// <returns>输出文件名，可能有多个文件</returns>
        string[] GetExpectedOutputs(string sourceFile);

        /// <summary>
        /// 应用该操作
        /// </summary>
        /// <param name="sourceFile">源文件路径</param>
        /// <param name="outputFile">输出文件路径</param>
        /// <param name="progress">提供进度回调</param>
        /// <returns>用于异步操作的<see cref="Task"/>对象</returns>
        Task Apply(string sourceFile, string outputFile, IProgress<double> progress);
    }
}
