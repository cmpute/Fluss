using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace JacobC.Music.Crawlers
{
    /// <summary>
    /// 爬虫数据的存写器
    /// </summary>
    /// <typeparam name="TData">爬虫数据的类型</typeparam>
    public interface ICrawlerWriter<TData>
    {
        /// <summary>
        /// 记录一条爬下来的数据
        /// </summary>
        /// <param name="data">数据内容</param>
        void WriteData(TData data);
        /// <summary>
        /// 记录多条爬下来的数据
        /// </summary>
        void WriteData(IEnumerable<TData> data);
    }
}
