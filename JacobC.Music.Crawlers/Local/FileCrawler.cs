using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace JacobC.Music.Crawlers.Local
{
    /// <summary>
    /// 从现有文件分析专辑信息的爬虫
    /// </summary>
    public class FileCrawler : Crawler<AlbumInfo>
    {
        public FileCrawler(ICrawlerWriter<AlbumInfo> writer) : base(writer) { }
        public override Task StartCrawling()
        {
            throw new NotImplementedException();
        }
    }
}
