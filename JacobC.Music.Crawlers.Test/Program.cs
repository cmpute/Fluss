using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Net.Http;
using JacobC.Music.Crawlers.Astost;
using HtmlAgilityPack;
using Debugger = System.Diagnostics.Debugger;

namespace JacobC.Music.Crawlers.Test
{
    class Program
    {
        static void Main(string[] args)
        {
            //InvokeAndWait(FetchTest);
            InvokeAndWait(CrawlerTest);
        }

        static async Task CrawlerTest()
        {
            AstostCrawler c = new AstostCrawler(null);
            var t = await c.CheckLogin();
            Debugger.Break();
        }

        static async Task FetchTest()
        {
            HtmlDocument doc = new HtmlDocument();
            using (var response = await new HttpClient().GetStreamAsync($"http://www.qq.com/"))
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
        public static void InvokeAndWait(Func<Task> asyncMethod)
        {
            Task.Run(() => asyncMethod())
                .ContinueWith(task => task.Wait())
                .Wait();
        }
    }
}
