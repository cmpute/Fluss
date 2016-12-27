using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.IO;
using System.Threading.Tasks;
using System.Net.Http;
using JacobC.Music.Crawlers.Astost;
using HtmlAgilityPack;
using Debugger = System.Diagnostics.Debugger;

namespace JacobC.Music.Crawlers.Test
{
    class TestStruct
    {
        public int int1 = 0;
        int int2 = 0;
        public int prop1 { get; set; } = 0;
        int prop2 { get; set; } = 0;
        public string str1 { get; set; } = "nu,ll";
    }
    class Program
    {
        static void Main(string[] args)
        {
            Test();
            //InvokeAndWait(FetchTest);
            InvokeAndWait(CrawlerTest);
        }

        static void Test()
        {
            FileStream f = File.OpenRead("test.csv");
            var ser = new CsvSerializer<TestStruct>()
            {
                UseLineNumbers = true,
                UseTextQualifier = true
            };
            ser.DeserializeHeader(f);
            var t = ser.DeserializeLine(f);
            //ser.SerializeHeader(f);
            //ser.Serialize(f, new TestStruct[] {
            //    new TestStruct { int1 = 2, prop1 = 3 },
            //    new TestStruct { str1 = "T\"TT", prop1 = 5 },
            //    new TestStruct { str1 = "new\nLine" }
            //});
            //ser.Serialize(f, new TestStruct[] {
            //    new TestStruct { int1 = 2, prop1 = 3 },
            //    new TestStruct { str1 = "T\"TT2", prop1 = 5 },
            //    new TestStruct { str1 = "new\nLine2" }
            //});
            //ser.Serialize(f, new TestStruct { str1 = "new\nLin3" });
            f.Close();
        }

        static async Task CrawlerTest()
        {
            //Debugger.Break();
            await Task.FromResult(true);
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
