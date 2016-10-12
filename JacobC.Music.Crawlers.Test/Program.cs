using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Net.Http;
using JacobC.Music.Crawlers.Astost;
using HtmlAgilityPack;

namespace JacobC.Music.Crawlers.Test
{
    class Program
    {
        static void Main(string[] args)
        {
            FetchTest();
            //CrawlerTest();
        }

        static void CrawlerTest()
        {
            AstostCrawler c = new AstostCrawler(null);
        }

        static void FetchTest()
        {
            HtmlDocument doc = new HtmlDocument();
            using (var response = InvokeAndWait(async () => await new HttpClient().GetStreamAsync($"http://www.qq.com/")))
                doc.Load(response);
            var d = doc.DocumentNode;
            var t = d.QuerySelector("div #newsContent01");
            doc.DocumentNode.SelectSingleNode(".//table[id='ajaxtable']");
        }

        public static T InvokeAndWait<T>(Func<Task<T>> asyncMethod)
        {
            Task<T> t = Task.Run(() => asyncMethod())
                .ContinueWith(task =>
                {
                    task.Wait();
                    return task.Result;
                });
            t.Wait();
            return t.Result;
        }
    }
}
