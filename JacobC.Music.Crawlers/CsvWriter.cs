using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace JacobC.Music.Crawlers
{
    /// <summary>
    /// CSV存写器
    /// </summary>
    /// <typeparam name="TData">爬虫数据的类型</typeparam>
    public class CsvWriter<TData> : ICrawlerWriter<TData>, IDisposable where TData:new()
    {
        const string defaultPath = "crawlerResult.csv";

        CsvSerializer<TData> _serializer;
        FileStream _file;

        public CsvWriter() : this(defaultPath) { }

        /// <summary>
        /// 创建一个写入指定文件的CSV存写器
        /// </summary>
        /// <param name="path">写入的CSV文件的路径</param>
        /// <param name="writeHeaders">是否写入列表头</param>
        public CsvWriter(string path, bool writeHeaders = false)
        {
            _serializer = new CsvSerializer<TData>();
            _file = File.OpenWrite(path);//File.Create(path);
            if (writeHeaders) _serializer.SerializeHeader(_file);
        }

        /// <inheritdoc/>
        public void WriteData(TData data)
        {
            _serializer.Serialize(_file, data);
        }

        /// <inheritdoc/>
        public void WriteData(IEnumerable<TData> data)
        {
            _serializer.Serialize(_file, data);
        }

        #region IDisposable Support
        private bool disposedValue = false; // 要检测冗余调用

        protected void Dispose(bool disposing)
        {
            if (!disposedValue)
            {
                if (disposing)
                {
                    // 释放托管状态(托管对象)。
                }

                // 释放未托管的资源(未托管的对象)并在以下内容中替代终结器。
                _file.Dispose();
                // 将大型字段设置为 null。

                disposedValue = true;
            }
        }
        
        ~CsvWriter()
        {
            // 请勿更改此代码。将清理代码放入以上 Dispose(bool disposing) 中。
            Dispose(false);
        }

        // 添加此代码以正确实现可处置模式。
        public void Dispose()
        {
            // 请勿更改此代码。将清理代码放入以上 Dispose(bool disposing) 中。
            Dispose(true);
            // 如果在以上内容中替代了终结器，则取消注释以下行。
            GC.SuppressFinalize(this);
        }
        #endregion
    }
}
