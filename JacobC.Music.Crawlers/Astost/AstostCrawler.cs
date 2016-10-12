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

        bool? _loggedin;
        uint _startid;
        ICrawlerWriter<AstostPostInfo> _writer;
        HttpClient _client;
        HttpClient _Client
        {
            get
            {
                if (_client == null)
                    InitClient();
                return _client;
            }
        }

        public AstostCrawler(ICrawlerWriter<AstostPostInfo> writer, uint startId = 0)
        {
            _startid = startId;
            _writer = writer;
        }
        #endregion

        #region Properties
        /// <summary>
        /// 抓取两个页面之间的间隔时间
        /// </summary>
        public int GrabInterval { get; set; } = 1000;

        /// <summary>
        /// 间隔时间是否随机化
        /// </summary>
        public bool GrabIntervalRandomize { get; set; } = true;
        #endregion

        #region Private Methods
        private void InitClient()
        {
            if(_client==null)
            {
                _client = new HttpClient(new HttpClientHandler() { AutomaticDecompression = DecompressionMethods.GZip });
                _client.DefaultRequestHeaders.AcceptEncoding.ParseAdd("gzip");
                _client.DefaultRequestHeaders.AcceptLanguage.ParseAdd("zh-Hans-CN,zh-Hans;q=0.9,ja;q=0.7,de-DE;q=0.6,de;q=0.4,en-US;q=0.3,en;q=0.1");
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
            using (var response = await _Client.GetStreamAsync($"{Domain}/bbs/thread.php?fid={fid}&page={page}"))
                doc.Load(response);
            return doc.DocumentNode.QuerySelector("table #ajaxtable");
        }
        #endregion

        public async Task<bool> CheckLogin()
        {
            if (!_loggedin.HasValue)
            {
                var response = await _Client.GetStringAsync(Domain + "/bbs/");
                _loggedin = response.IndexOf("register.php") < 0;
            }
            return _loggedin.Value;
        }

        /// <summary>
        /// 登录Astost
        /// </summary>
        /// <param name="username">用户名</param>
        /// <param name="password">密码</param>
        /// <param name="verifycode">验证码输入的方法</param>
        /// <returns></returns>
        public async Task<LoginResult> Login(string username, string password, Func<System.IO.Stream, Task<string>> verifycode)
        {
            if (await CheckLogin())
                return LoginResult.Success;
            int timestamp = (int)((DateTime.Now - new DateTime(1970, 1, 1).ToLocalTime()).TotalSeconds);
            var imgrequest = new HttpRequestMessage(HttpMethod.Get, "https://www.astost.com/bbs/ck.php?nowtime=" + timestamp);
            imgrequest.Headers.Accept.ParseAdd("image/webp,image/*,*/*;q=0.8");
            var imgresponse = await _client.SendAsync(imgrequest);
            var image = await imgresponse.Content.ReadAsStreamAsync();
            var param = new Dictionary<string, string>{
                ["jumpurl"] = "https://www.astost.com/bbs/index.php",
                ["step"] = "2",
                ["cktime"] = "31536000",
                ["lgt"] = "0",
                ["pwuser"] = username,
                ["pwpwd"] = password,
                ["gdcode"] = await verifycode(image)
            };
            var responese = await _client.PostAsync("https://www.astost.com/bbs/pw_ajax.php?action=login", new FormUrlEncodedContent(param));
            string restext = await responese.Content.ReadAsStringAsync();
            string rescontent = System.Text.RegularExpressions.Regex.Match(restext, @"!\[CDATA\[.*\]\]").Value;
            if (rescontent.IndexOf("<div") < 0)
            {
                _loggedin = false;
                if (rescontent.IndexOf("密码") >= 0)
                    return LoginResult.WrongPassword;
                else if (rescontent.IndexOf("验证码") >= 0)
                    return LoginResult.WrongVerifyCode;
                else
                    return LoginResult.WrongPassword;
            }
            else
            {
                _loggedin = true;
                return LoginResult.Success;
            }
        }


        public override async Task StartCrawling()
        {
            if (!await CheckLogin())
                throw new InvalidOperationException("请登录后再启动爬虫");

        }

    }
}
