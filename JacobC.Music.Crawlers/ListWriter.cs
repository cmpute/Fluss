using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace JacobC.Music.Crawlers
{
    /// <summary>
    /// 一个最简单的爬虫存写器的List实现
    /// </summary>
    /// <typeparam name="T">爬虫数据类型</typeparam>
    public class ListWriter<T> : ICrawlerWriter<T>
    {
        public List<T> Result { get; protected set; } = new List<T>();

        /// <inheritdoc/>
        public void WriteData(IEnumerable<T> data) => Result.AddRange(data);

        /// <inheritdoc/>
        public void WriteData(T data) => Result.Add(data);
    }
}
