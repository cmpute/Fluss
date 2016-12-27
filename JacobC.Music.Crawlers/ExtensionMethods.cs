using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net;
using System.Threading.Tasks;
using HtmlAgilityPack;
using Serializer = System.Runtime.Serialization.Formatters.Binary.BinaryFormatter;

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

        /// <summary>
        /// 通过<see cref="Serializer"/>序列化器进行对象序列化
        /// </summary>
        /// <param name="stream">需要写入的流</param>
        public static void Serialize<T>(this T target, Stream stream)
            => new Serializer().Serialize(stream, target);
        public static T Deserialize<T>(Stream stream) where T : class
            => new Serializer().Deserialize(stream) as T;
    }
}
