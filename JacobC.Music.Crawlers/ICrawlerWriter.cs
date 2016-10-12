using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace JacobC.Music.Crawlers
{
    public interface ICrawlerWriter<DataType>
    {
        /// <summary>
        /// 记录一条爬下来的数据
        /// </summary>
        /// <param name="data">数据内容</param>
        void WriteData(DataType data);
    }
}
