using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using System.Net;
using System.Net.Http;
using System.IO;
using System.Text.RegularExpressions;
using HtmlAgilityPack;

namespace JacobC.Music.Crawlers.Astost
{
    /// <summary>
    /// Astost论坛爬虫
    /// </summary>
    public class AstostCrawler : Crawler<AstostArticleInfo>
    {
        #region .ctor And Fields
        const string Domain = "https://www.astost.com/bbs/";
        const int PostPerPage = 18;

        string cookiepath = "cookie.dat";
        CookieContainer _cookiecontainer;
        HttpClient _client;
        HttpClient Client
        {
            get
            {
                if (_client == null)
                    InitClient();
                return _client;
            }
        }

        public AstostCrawler(ICrawlerWriter<AstostArticleInfo> writer)
            : base(writer)
        {
        }
        ~AstostCrawler()
        {
            if (!SaveCookie)
                Logout();
            else
                SaveCookies();
        }
        #endregion

        #region CrawlerSettings
        /// <summary>
        /// 抓取两个页面之间的间隔时间
        /// </summary>
        public int GrabInterval { get; set; } = 1000;

        /// <summary>
        /// 间隔时间是否随机化
        /// </summary>
        public bool GrabIntervalRandomize { get; set; } = true;

        /// <summary>
        /// 抓取的版块列表，传入其ID即可
        /// </summary>
        public IEnumerable<uint> GrabForumList { get; set; }

        /// <summary>
        /// 获取或设置开始抓取的帖子的ID，ID小于它的帖子将不会被抓取
        /// </summary>
        public uint StartPostID { get; set; } = 0;

        /// <summary>
        /// 获取或设置爬虫创建时是否从文件目录读取cookie，以及析构时是否保存Cookie
        /// </summary>
        public bool SaveCookie { get; set; } = false;

        /// <summary>
        /// 获取或设置爬虫的cookie存储的位置
        /// </summary>
        public string LocalCookiePath
        {
            get { return cookiepath; }
            set { cookiepath = value; }
        }
        #endregion

        #region Private Methods
        private void Log(string message) => Log(message, nameof(AstostCrawler));

        private void InitClient()
        {
            if (_client == null)
            {
                _cookiecontainer = new CookieContainer();
                if (SaveCookie) LoadCookies();
                _client = new HttpClient(new HttpClientHandler() { AutomaticDecompression = DecompressionMethods.GZip, CookieContainer = _cookiecontainer });
                _client.DefaultRequestHeaders.AcceptEncoding.ParseAdd("gzip");
                _client.DefaultRequestHeaders.AcceptLanguage.ParseAdd("zh-Hans-CN,zh-Hans;q=0.9,ja;q=0.7,de-DE;q=0.6,de;q=0.4,en-US;q=0.3,en;q=0.1");
                _client.DefaultRequestHeaders.UserAgent.ParseAdd("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36");
            }
        }

        private void LoadCookies()
        {
            Log("Loading cookies from " + cookiepath);

            if (File.Exists(cookiepath))
                using (Stream s = File.OpenRead(cookiepath))
                    _cookiecontainer.Add(ExtensionMethods.Deserialize<CookieCollection>(s));

            Log("Cookies loaded!");
        }

        private void SaveCookies()
        {
            Log("Saving cookies to " + cookiepath);

            using (Stream s = File.Create(cookiepath))
                _cookiecontainer.GetCookies(new Uri("https://www.astost.com")).Serialize(s);

            Log("Cookies Saved!");
        }

        Regex regtid = new Regex("(?<=tid=)[0-9]+",RegexOptions.Compiled);
        private AstostArticleInfo ParseLine(HtmlNode tr)
        {
            var result = new AstostArticleInfo();
            var linknode = tr.SelectSingleNode("./td/h3/a");
            result.Title = WebUtility.HtmlDecode(linknode.InnerText);
            result.ThreadID = uint.Parse(regtid.Match(linknode.GetAttributeValue("href", "=0")).Value);
            var user = tr.SelectSingleNode("./th/a[@class='bl']");
            result.UserName = user.InnerText;
            var linkaddr = user.GetAttributeValue("href", "=0");
            result.UserID = uint.Parse(linkaddr.Substring(linkaddr.LastIndexOf('=') + 1));
            result.PostDate = user.ParentNode.LastChild.InnerText;
            return result;
        }
        #endregion

        #region Login Session

        bool? _loggedin;
        string _logouturl;

        public async Task<bool> CheckLogin()
        {
            if (!_loggedin.HasValue)
            {
                var response = await Client.GetStringAsync(Domain);
                _loggedin = response.IndexOf("register.php") < 0;
            }
            return _loggedin.Value;
        }

        /// <summary>
        /// 获取验证码图片的文件流
        /// </summary>
        public async Task<Stream> GetVerifyCode()
        {
            Log("Fetching verify code Image");

            int timestamp = (int)((DateTime.Now - new DateTime(1970, 1, 1).ToLocalTime()).TotalSeconds);
            var imgrequest = new HttpRequestMessage(HttpMethod.Get, Domain + "ck.php?nowtime=" + timestamp);
            imgrequest.Headers.Accept.ParseAdd("image/webp,image/*,*/*;q=0.8");
            var imgresponse = await Client.SendAsync(imgrequest);
            return await imgresponse.Content.ReadAsStreamAsync();
        }
        /// <summary>
        /// 登录Astost
        /// </summary>
        /// <param name="username">用户名</param>
        /// <param name="password">密码</param>
        /// <param name="verifycode">验证码（可以提前通过<see cref="GetVerifyCode"/>方法获得）</param>
        /// <returns></returns>
        public async Task<LoginResult> Login(string username, string password, string verifycode)
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
            Log("Attempt to log in...");

            var responese = await Client.PostAsync(Domain + "pw_ajax.php?action=login", new FormUrlEncodedContent(param));
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
                Log("Astost crawler login succeed!");
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

        /// <summary>
        /// 抓取论坛的板块列表
        /// </summary>
        /// <returns>板块信息</returns>
        public async Task<IEnumerable<AstostForumInfo>> FetchForumList()
        {
            var response = await Client.GetAsync(Domain);
            var doc = new HtmlDocument();
            doc.LoadHtml(await response.Content.ReadAsStringAsync());
            return doc.DocumentNode.QuerySelectorAll("tr.tr3.f_one").Select((node) =>
            {
                var info = new AstostForumInfo();
                var link = node.SelectSingleNode(".//h3/a");
                info.Name = link.InnerText;
                var linkaddr = link.GetAttributeValue("href", "thread.php?fid=1");
                info.ID = uint.Parse(linkaddr.Substring(linkaddr.IndexOf('=') + 1));
                var counts = node.SelectNodes(".//span[@class='f10']");
                info.ArticleCount = int.Parse(counts[0].InnerText);
                info.PostCount = int.Parse(counts[1].InnerText);
                return info;
            });
        }

        public override async Task StartCrawling()
        {
            if (GrabForumList == null)
                return;
            if (!await CheckLogin())
                throw new InvalidOperationException("请登录后再启动Astost爬虫");
            int page = 2; //从2开始循环
            HtmlDocument doc = new HtmlDocument();
            bool pinflag = true, breakflag = false;
            Random intvr = new Random();
            foreach (int id in GrabForumList)
            {
                //处理第一页
                doc.LoadHtml(await Client.GetStringAsync(Domain + $"thread.php?fid={id}"));
                var table = doc.DocumentNode.QuerySelector("table#ajaxtable");
                foreach (var row in table.SelectNodes("./tbody/tr").Skip(3))
                {
                    var cla = row.GetAttributeValue("class", string.Empty);
                    if (string.IsNullOrEmpty(cla)) continue;
                    if (cla == "tr2")
                    {
                        pinflag = false;
                        continue;
                    }
                    var info = ParseLine(row);
                    if (!pinflag && info.ThreadID < StartPostID)
                    {
                        breakflag = true;
                        break;
                    }
                    if (breakflag) return;
                    info.Pinned = pinflag;
                    Writer.WriteData(info);
                }
                while (true)
                {
                    if (GrabIntervalRandomize)
                        Thread.Sleep(intvr.Next(GrabInterval));
                    else
                        Thread.Sleep(GrabInterval);
                    doc.LoadHtml(await Client.GetStringAsync(Domain + $"thread.php?fid={id}&page={page}"));
                    table = doc.DocumentNode.QuerySelector("table#ajaxtable");
                    var rows = table.SelectNodes("./tbody/tr[@align='center']");
                    breakflag = false;
                    foreach (var row in rows)
                    {
                        var info = ParseLine(row);
                        if (info.ThreadID < StartPostID)
                        {
                            breakflag = true;
                            break;
                        }
                        Writer.WriteData(info);
                    }
                    if (breakflag || rows.Count < PostPerPage) break;
                    page++;
                }
                Thread.Sleep(1000);
            }
        }
    }
}
