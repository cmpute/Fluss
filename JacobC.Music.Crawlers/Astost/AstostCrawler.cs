using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using System.Net;
using System.Net.Http;
using System.IO;
using HtmlAgilityPack;

namespace JacobC.Music.Crawlers.Astost
{
    /// <summary>
    /// Astost论坛爬虫
    /// </summary>
    public class AstostCrawler : Crawler
    {
        #region .ctor And Fields
        const string Domain = "https://www.astost.com/bbs/";

        uint _startid;
        bool _savecookie;
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

        public AstostCrawler(ICrawlerWriter<AstostPostInfo> writer, uint startId = 0, bool savecookie = false)
        {
            _startid = startId;
            _writer = writer;
            _savecookie = savecookie;
        }
        ~AstostCrawler()
        {
            if (!_savecookie)
                Logout();
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

        #region Login Session

        bool? _loggedin;
        string _logouturl;

        public async Task<bool> CheckLogin()
        {
            if (!_loggedin.HasValue)
            {
                var response = await _Client.GetStringAsync(Domain);
                _loggedin = response.IndexOf("register.php") < 0;
            }
            return _loggedin.Value;
        }

        /// <summary>
        /// 获取验证码图片的文件流
        /// </summary>
        public async Task<Stream> GetVerifyCode()
        {
            int timestamp = (int)((DateTime.Now - new DateTime(1970, 1, 1).ToLocalTime()).TotalSeconds);
            var imgrequest = new HttpRequestMessage(HttpMethod.Get, Domain + "ck.php?nowtime=" + timestamp);
            imgrequest.Headers.Accept.ParseAdd("image/webp,image/*,*/*;q=0.8");
            var imgresponse = await _Client.SendAsync(imgrequest);
            return await imgresponse.Content.ReadAsStreamAsync();
        }
        /// <summary>
        /// 登录Astost
        /// </summary>
        /// <param name="username">用户名</param>
        /// <param name="password">密码</param>
        /// <param name="verifycode">验证码（可以提前通过<see cref="GetVerifyCode"/>方法获得）</param>
        /// <returns></returns>
        public async Task<LoginResult> Login(string username,string password, string verifycode)
        {
            if (await CheckLogin())
                return LoginResult.Success;
            var param = new Dictionary<string, string>
            {
                ["jumpurl"] = Domain + "index.php",
                ["step"] = "2",
                ["cktime"] = "31536000",
                ["lgt"] = "0",
                ["pwuser"] = username,
                ["pwpwd"] = password,
                ["gdcode"] = verifycode
            };
            var responese = await _Client.PostAsync(Domain + "pw_ajax.php?action=login", new FormUrlEncodedContent(param));
            string restext = await responese.Content.ReadAsStringAsync();
            string rescontent = System.Text.RegularExpressions.Regex.Match(restext, @"!\[CDATA\[[\s\S]*\]\]").Value;
            var logoutlink = ExtensionMethods.LoadHtmlRootNode(rescontent).Descendants("a").Where((node) => node.InnerText == "退出")?.First();
            if (logoutlink != null)
                _logouturl = logoutlink.GetAttributeValue("href", "");
            if (rescontent.IndexOf("<div") < 0)
            {
                _loggedin = false;
                Log("Astost Crawler Login Failed");
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
                Log("Astost Crawler Login Succeed");
                return LoginResult.Success;
            }
        }
        /// <summary>
        /// 登录Astost
        /// </summary>
        /// <param name="username">用户名</param>
        /// <param name="password">密码</param>
        /// <param name="verifycode">验证码输入的方法</param>
        /// <returns></returns>
        public async Task<LoginResult> Login(string username, string password, Func<Stream, Task<string>> verifycode) =>
            await Login(username, password, await verifycode(await GetVerifyCode()));
        public async void Logout()
        {
            if (await CheckLogin() && !string.IsNullOrEmpty(_logouturl))
            {
                var res = await _client.GetAsync(Domain + _logouturl);
                res.EnsureSuccessStatusCode();
                _loggedin = false;
                Log("Astost Crawler Logged out");
            }
        }
        #endregion

        public override async Task StartCrawling()
        {
            if (!await CheckLogin())
                throw new InvalidOperationException("请登录后再启动爬虫");

        }

    }
}
