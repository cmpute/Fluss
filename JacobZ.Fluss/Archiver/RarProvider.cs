using System;
using System.Collections.Generic;

namespace JacobZ.Fluss.Archiver
{
    public class RarProvider : IArchiver
    {
        private string _rar;

        /// <summary>
        /// 新建Rar压缩对象
        /// </summary>
        /// <param name="rarPath">WinRAR安装目录</param>
        public RarProvider(string rarPath)
        {
            _rar = rarPath;
        }

        public void Compress(string archivePath, CompressSettings settings)
        {
            throw new NotImplementedException();
        }

        public void Decompress(string archivePath, string outputPath)
        {
            throw new NotImplementedException();
        }

        public IEnumerable<string> GetContentList(string archivePath)
        {
            throw new NotImplementedException();
        }
    }
}
