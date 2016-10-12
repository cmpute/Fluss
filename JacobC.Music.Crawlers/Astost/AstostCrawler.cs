using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using System.Net;
using System.Net.Http;
using HtmlAgilityPack;

namespace JacobC.Music.Crawlers.Astost
{
    /// <summary>
    /// Astost论坛爬虫
    /// </summary>
    public class AstostCrawler : Crawler
    {
        #region .ctor And Fields
        const string Domain = "https://www.astost.com";

        uint _startid;
        ICrawlerWriter<AstostPostInfo> _writer;
        HttpClient _client;

        public AstostCrawler(ICrawlerWriter<AstostPostInfo> writer, uint startId = 0)
        {
            _startid = startId;
            _writer = writer;
        }
        #endregion

        #region Private Methods
        private void InitClient()
        {
            if(_client==null)
            {
                _client = new HttpClient();
                _client.DefaultRequestHeaders.UserAgent.ParseAdd("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36");
            }
        }

        /// <summary>
        /// 获取某一板块的指定页
        /// </summary>
        /// <param name="fid">板块编号</param>
        /// <param name="page">页码</param>
        /// <returns>页面的目录内容部分</returns>
        private async Task<HtmlNode> FetchPageBody(int fid, int page)
        {
            HtmlDocument doc = new HtmlDocument();
            using (var response = await _client.GetStreamAsync($"{Domain}/bbs/thread.php?fid={fid}&page={page}"))
                doc.Load(response);
            return doc.DocumentNode.QuerySelector("table #ajaxtable");
        }
        #endregion

        public async Task<bool> CheckLogin()
        {
            var response = await _client.GetStringAsync(Domain + "/bbs/");
            return response.IndexOf("register.php") < 0;
        }

        public override async Task StartCrawling()
        {
            InitClient();
            if (!await CheckLogin())
                throw new InvalidOperationException("请登录后再启动爬虫");

        }

    }
}
