using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace JacobC.Music.Crawlers
{
    /// <summary>
    /// 用来记录日志的代理方法
    /// </summary>
    /// <param name="message">日志消息，不含换行符</param>
    public delegate void LogDelegate(string message);
    public abstract class Crawler<TPost>
    {
        /// <summary>
        /// 获取或者设置爬虫爬取内容的存写器
        /// </summary>
        public ICrawlerWriter<TPost> Writer { get; set; }
        public Crawler(ICrawlerWriter<TPost> writer)
        {
            Writer = writer;
        }

        /// <summary>
        /// 爬虫日志的记录服务
        /// </summary>
        public event LogDelegate LogService;
        protected virtual void Log(string message, string caller)
        {
#if DEBUG
            LogService?.Invoke($"[{caller}]{message}");
#endif
        }

        /// <summary>
        /// 开始抓取
        /// </summary>
        public abstract Task StartCrawling();
    }
}
