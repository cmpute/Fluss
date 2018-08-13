using System;
using System.Collections.Generic;
using System.Diagnostics;

namespace JacobZ.Fluss.Archiver
{
    using JacobZ.Fluss.Utils;

    public class ExternRarProvider : IArchiver
    {
        private string _rar;

        /// <summary>
        /// 新建RAR压缩提供对象
        /// </summary>
        /// <param name="rarPath">WinRAR安装目录</param>
        public ExternRarProvider(string rarPath)
        {
            _rar = rarPath;
            VersionCheck();
        }

        protected void VersionCheck()
        {
            Process exec = ProcessHelper.Generate(_rar);
            exec.Start();

            var output = exec.StandardOutput;
            while (output.Read() != 'R') ;
            while (output.Read() != ' ') ;
            
            if (output.Read() < '5')
                throw new InvalidProgramException("Please use WinRAR 5!");
        }

        public void Compress(string archivePath, CompressSettings settings)
        {
            throw new NotImplementedException();
        }

        public void Decompress(string archivePath, string outputPath)
        {
            Process exec = ProcessHelper.Generate(_rar);
            exec.StartInfo.Arguments = "x " + archivePath + " " + outputPath;
            exec.Start();
            exec.EnsureExit();
        }

        public void Decompress(string archivePath, string outputPath, params string[] files)
        {
            Process exec = ProcessHelper.Generate(_rar);
            exec.StartInfo.Arguments = "x " + archivePath + " " + string.Join(" ", files) + " " + outputPath;
            exec.Start();
            exec.EnsureExit();
        }

        public IEnumerable<string> GetContentList(string archivePath)
        {
            Process exec = ProcessHelper.Generate(_rar);
            exec.StartInfo.Arguments = "lb " + archivePath;
            exec.Start();
            exec.EnsureExit();

            var output = exec.StandardOutput;
            while (!output.EndOfStream)
            {
                string filename = output.ReadLine();

                // FIXME: Use rar to judge path property
                if (System.IO.Path.GetExtension(filename).Length > 0)
                    yield return filename;
            }
        }
    }
}
