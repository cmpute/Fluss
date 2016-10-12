using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using HtmlAgilityPack;

namespace JacobC.Music.Crawlers
{
    internal static class ExtensionMethods
    {
        /// <summary>
        /// 加载Html内容并返回根节点
        /// </summary>
        public static HtmlNode LoadHtmlRootNode(string content)
        {
            var doc = new HtmlDocument();
            doc.LoadHtml(content);
            return doc.DocumentNode;
        }
    }
}
