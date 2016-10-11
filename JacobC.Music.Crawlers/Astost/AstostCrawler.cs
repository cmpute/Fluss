using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using System.Net;

namespace JacobC.Music.Crawlers.Astost
{
    /// <summary>
    /// Astost论坛爬虫
    /// </summary>
    public class AstostCrawler : Crawler
    {
        int _startid;
        public AstostCrawler(int startId = 0)
        {
            _startid = startId;
        }


    }
}
