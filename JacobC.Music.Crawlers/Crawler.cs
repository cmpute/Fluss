using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace JacobC.Music.Crawlers
{
    /// <summary>
    /// 用来记录日志的代理方法
    /// </summary>
    /// <param name="message"></param>
    public delegate void LogDelegate(string message);
    public abstract class Crawler
    {
        /// <summary>
        /// 爬虫日志的记录服务
        /// </summary>
        public event LogDelegate LogService;
        protected virtual void Log(string message)
        {
            LogService?.Invoke(message);
        }
        /// <summary>
        /// 开始抓取
        /// </summary>
        public abstract Task StartCrawling();
    }
}
