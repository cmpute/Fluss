using System;
using System.Collections.Generic;

namespace JacobZ.Fluss.Archiver
{
    public interface IArchiver
    {
        /// <summary>
        /// 获取压缩文件内容列表
        /// </summary>
        /// <param name="archivePath">压缩文件路径</param>
        /// <returns>文件列表</returns>
        IEnumerable<string> GetContentList(string archivePath);

        /// <summary>
        /// 解压压缩文件
        /// </summary>
        /// <param name="archivePath">压缩文件目录</param>
        /// <param name="outputPath">输出位置</param>
        void Decompress(string archivePath, string outputPath);

        /// <summary>
        /// 解压压缩包中的部分文件
        /// </summary>
        /// <param name="archivePath">压缩文件目录</param>
        /// <param name="outputPath">输出位置</param>
        /// <param name="files">所解压文件在压缩包中的路径</param>
        void Decompress(string archivePath, string outputPath, params string[] files);

        /// <summary>
        /// 建立压缩文件
        /// </summary>
        /// <param name="archivePath">压缩文件目录</param>
        /// <param name="settings">压缩设置</param>
        void Compress(string archivePath, CompressSettings settings);
    }
}
