using System;
using System.IO;
using System.Xml;
using System.Collections.Generic;
using System.Text.RegularExpressions;

namespace JacobC.Music.Crawlers.Astost
{
    public struct AstostAlbumInfo
    {
        ///// <summary>
        ///// 是否为应求档
        ///// </summary>
        //public bool IsRequest;
        ///// <summary>
        ///// 专辑名
        ///// </summary>
        //public string Name;
        ///// <summary>
        ///// 专辑属性
        ///// </summary>
        //public string Attribute;
        ///// <summary>
        ///// 专辑艺术家
        ///// </summary>
        //public string[] Artist;
        ///// <summary>
        ///// 发售展会（同人专辑）
        ///// </summary>
        //public string Event;
        ///// <summary>
        ///// 发售日期 [YYMMDD]
        ///// </summary>
        //public string Date;
        ///// <summary>
        ///// 相关网站
        ///// </summary>
        //public Uri[] RelateWebsite;
        /// <summary>
        /// 文件格式
        /// </summary>
        public string[] FileFormats;
        ///// <summary>
        ///// 自抓者（如果是自抓资源）
        ///// </summary>
        //public string Ripper;
        
        /// <summary>
        /// 存储网盘
        /// </summary>
        public string Cloud;
        ///// <summary>
        ///// CD数
        ///// </summary>
        //public int CDNum;
    }
    /// <summary>
    /// 专辑属性列表
    /// </summary>
    [Flags]
    public enum AstostAlbumAttribute
    {
        /// <summary>
        /// 高音质专辑
        /// </summary>
        Hires = 1,
        /// <summary>
        /// DVD音频
        /// </summary>
        DVDAudio = 2,
        /// <summary>
        /// 蓝光音频
        /// </summary>
        BluerayAudio = 4,
        /// <summary>
        /// 现场版
        /// </summary>
        Live = 8,
        /// <summary>
        /// 非实体专辑
        /// </summary>
        Digital = 16
    }
    public static class AstostTextParser
    {
        /// <summary>
        /// 保存结果的文件的名称前缀
        /// </summary>
        public static string ResultFilenameHeader = "astost_";

        /// <summary>
        /// 将一条抓取下来的链接从Html形式转换成纯文本标题
        /// </summary>
        /// <param name="content">HTML形式的行</param>
        /// <returns>纯文本标题</returns>
        //public static string HtmlLineToText(string content)
        //{
        //    //content = WebUtility.HtmlEncode("<?xml?>" + content); 用法可以记着，但是转换的太多了
        //    int temp = content.IndexOf("color=");
        //    if (temp > 0)
        //        content = content.Insert(temp + 6, "\"").Insert(content.IndexOf('>', temp) + 1, "\"");
        //    content = "<?xml version=\"1.0\" standalone=\"yes\"?>" + content.Replace("&", "&amp;"); //TODO: 本身就存在&amp;和&quot;的情况没有处理
        //    XmlDocument xd = new XmlDocument();
        //    xd.LoadXml(content.Trim());
        //    XmlNode xn = xd.ChildNodes[1];//第0个是<?xml?>
        //    while (xn.HasChildNodes)
        //        xn = xn.FirstChild;
        //    return xn.InnerText.Replace("&amp;", "&");
        //}
        /// <summary>
        /// 从抓取结果中抽取帖子名称文字
        /// </summary>
        /// <param name="resultsdir">需要抽取的页面所在路径</param>
        /// <param name="outputpath">输出文件地址，输出为txt格式</param>
        //public static void ExtractTitles(string resultsdir, string outputpath)
        //{
        //    DirectoryInfo di = new DirectoryInfo(resultsdir);
        //    List<string> fns = new List<string>();
        //    foreach (FileInfo fi in di.GetFiles())
        //    {
        //        if (fi.Name.StartsWith(ResultFilenameHeader) && (fi.Name.ToLower().EndsWith(".html") || fi.Name.ToLower().EndsWith(".htm")))
        //            fns.Add(fi.FullName);
        //    }
        //    ExtractTitles(fns.ToArray(), outputpath);
        //}
        /// <summary>
        /// 从抓取结果中抽取帖子名称文字
        /// </summary>
        /// <param name="resultsdir">需要抽取的页面</param>
        /// <param name="outputpath">输出文件地址，输出为txt格式</param>
        //public static void ExtractTitles(string[] resultpages, string outputpath)
        //{
        //    StreamWriter output = File.CreateText(outputpath);
        //    foreach (string page in resultpages)
        //    {
        //        StreamReader input = File.OpenText(page);
        //        input.ReadLine();
        //        while (!input.EndOfStream)
        //            output.WriteLine(HtmlLineToText(input.ReadLine()));
        //        input.Close();
        //        output.Flush();
        //    }
        //    output.Close();
        //}
        /// <summary>
        /// 从纯文本标题列表中提取专辑信息
        /// </summary>
        /// <param name="filepath">标题列表文件</param>
        public static List<AstostAlbumInfo> ExtractInfo(string filepath)
        {
            return null;
        }
        /// <summary>
        /// 从纯文本标题列表中提取专辑信息，并保存到文件
        /// </summary>
        /// <param name="filepath">标题列表文件</param>
        /// <param name="outpath">提取的信息保存目录</param>
        public static void ExtractInfo(string filepath, string outpath)
        {
            const int maxlines = 100000000;
            bool InBracket, noContent;//在括号内，无内容
            int braStart, braEnd; //括号位置指针
            StreamReader sr = File.OpenText(filepath);
            StreamWriter sw = File.CreateText(outpath);
            Regex brackets = new Regex(@"(?<=[\[\(【（]).*?(?=[\]\)】）])");//原来是(\[.*?\])|(\(.*?\))|（.*?）|【.*?】，但是这样需要trim处理且会有遗漏
            for (int counter = 0; counter < maxlines && !sr.EndOfStream; counter++)
            {
                //TODO：开头括号前和末尾括号后的内容要存下来
                //      |分开的内容分开存
                //      电驴资源是嵌套名称，需要单独处理（跳过也可）
                //      比如"[115/31D][千年女优.-.[平沢進][Millennium.Actress.OST].专辑.(FLAC分轨).rar][270MB]"
                //      "[JS电信长期][EAC][080827]((シングル)L&#39;Arc～en～Ciel - NEXUS 4／SHINE 精霊の守り人 OPtta+cue+jpg)[118M]"
                //
                //正则处理不了的特殊的结构："[BD][Disney-Finding.Nemo.(complete.score).PROMO](Ape+cue+log)[M]"
                string line = sr.ReadLine();
                if (line.IndexOf("】】") > -1)
                    continue;
                string linec = line;//暂存最初的字段用于debug
                List<string> Infos = new List<string>();
                bool case1 = line.IndexOf("[[") > -1;
                bool case2 = line.IndexOf("]]") > -1;
                bool case3 = Regex.Matches(line, @"\[").Count != Regex.Matches(line, @"\]").Count;
                if (case1 || case2 || case3)//出现异常时用正则处理，正则比较保守
                {
                    if (case3) //异常中的异常情况处理
                    {
                        if (case1)
                            //处理"bd [[020126] おねがい☆ティーチャー - Shooting Star／空の森で (ape+cue+jpg)147m"
                            line = line.Replace("[[", "[");//如果[[且数目不对，[[当作[进行一般处理                            
                        if (case2)
                            line = line.Replace("]]", "]");
                        //处理"[BD][EAC]TVアニメ_とある魔術の禁書目録II op2「No buts](ape+cue)"
                        //处理"[BD]借东西的阿丽埃蒂原声集.-.[The.Borrowers]Kari-gurashi.no.Arrietty.Soundtrack].专辑.[FLAC+PNG][299M]"
                        char[] linet = line.ToCharArray();
                        int delta = 0;
                        for (int i = 0; i < linet.Length; i++)
                            if (linet[i] == '[')
                                delta++;
                            else if (linet[i] == ']')
                                if (delta == 0)
                                    linet[i] = ' ';
                                else
                                    delta--;
                        line = new string(linet);
                    }
                    else
                    {
                        //处理"[baidu][[01.42.21]ZAQ - Sparkling Daydream(M4A+CUE+BK)][168MB]"
                        //处理"[自抓部分自掃][115][051102][機動戦士ガンダムSEED DESTINY COMPLETE BEST [Limited Edition]][FLAC+CUE+LOG+DVD+SCANSx2][3.74GB]"
                        MatchCollection mresult = brackets.Matches(line);
                        foreach (Match re in mresult)
                        {
                            line = line.Remove(line.IndexOf(re.Value), re.Value.Length);
                            Infos.Add(re.Value.Trim());
                        }
                        //"[*_^作为记号
                        Infos.Add(line.Trim().Trim('[', ']', '【', '】', '（', '）', '(', ')').Trim());
                        sw.WriteLine(string.Join("\n", Infos.ToArray()));
                        continue;
                    }
                }
                char end = ' ';//配对括号符，括号要一对一配对
                braStart = 0;
                braEnd = line.Length - 1;
                InBracket = false;
                noContent = true;
                //处理"[BD](自抓自扫)機動戦士ガンダムＵＣ　COMPLETE BEST（wav+cue+bk)[469MB]"
                line = line.Replace("（", "(").Replace("）", ")").Replace("｜", "|");//中文括号换成英文括号进行配对
                if (line.IndexOf('|') > -1 && Regex.Matches(line, @"\(").Count != Regex.Matches(line, @"\)").Count)
                    //处理"[NMP][EAC](マキシシングル)LEMON ANGEL PROJECT キャラクターソング 3 - Smile means love／风のように｜ape+cue+bk rr3)"
                    line = line.Replace("|", "(");
                //可以选择使用的正则式：(?m)^(?:\s*[\[(][^)\]]+[\])])+|(?:[\[(][^)\]]+[\])]\s*)+$
                for (int pointer = 0; pointer < line.Length; pointer++)
                {
                    char k = line[pointer];
                    if (InBracket)//已在括号内
                    {
                        if (k == end)
                        {
                            Infos.Add(line.Substring(braStart + 1, pointer - braStart - 1));
                            InBracket = false;
                        }
                    }
                    else//不在括号内
                    {
                        if (k == '[' || k == '【' || k == '(' || k == ' ')
                        {
                            if (k != ' ')
                            {
                                InBracket = true;
                                braStart = pointer;
                                switch (k)
                                {
                                    case '[': end = ']'; break;
                                    case '【': end = '】'; break;
                                    case '(': end = ')'; break;
                                }
                            }
                        }
                        else
                        {
                            braStart = pointer;
                            noContent = false;
                            break;
                        }
                    }
                }
                if (noContent)
                {
                    sw.WriteLine(string.Join("\t", Infos.ToArray()));
                    continue;
                }
                for (int pointer = line.Length - 1; pointer >= 0; pointer--)
                {
                    char k = line[pointer];
                    if (InBracket)
                    {
                        if (k == end)
                        {
                            Infos.Add(line.Substring(pointer + 1, braEnd - pointer - 1).Trim(')', ']'));
                            InBracket = false;
                        }
                    }
                    else
                    {
                        if (k == ']' || k == '】' || k == ')' || k == ' ')
                        {
                            if (k != ' ')
                            {
                                InBracket = true;
                                braEnd = pointer;
                                switch (k)
                                {
                                    case ']': end = '['; break;
                                    case '】': end = '【'; break;
                                    case ')': end = '('; break;
                                }
                            }
                        }
                        else
                        {
                            braEnd = pointer;
                            break;
                        }
                    }
                }
                if (braStart <= braEnd)
                    Infos.Add("[*_^" + line.Substring(braStart, braEnd - braStart + 1));//"[*_^作为记号
                //剩下的情况（如有嵌套）直接暴力分开
                else
                {
                    Infos = new List<string>();
                    foreach (string tmp in linec.Split('(', ')', '【', '】', '（', '）', '[', ']'))
                        if (tmp.Trim().Length > 0)
                            Infos.Add(tmp.Trim());
                    Console.WriteLine("Exception Title : {0}", linec);
                    Console.WriteLine(string.Join("\n", Infos.ToArray()));
                    Console.ReadLine();
                }
                sw.WriteLine(string.Join("\n", Infos.ToArray()));
            }
            sr.Dispose();
            sw.Dispose();
        }
        /// <summary>
        /// 从关键字中收集专辑数据
        /// </summary>
        /// <param name="attrTexts">专辑信息关键字</param>
        /// <param name="album">对应的专辑</param>
        public static void CollectAttribute(string[] attrTexts, ref AstostAlbumInfo album)
        {

        }
        /// <summary>
        /// 从关键字中收集专辑数据
        /// </summary>
        /// <param name="attrText">专辑信息关键字</param>
        /// <param name="album">对应的专辑</param>
        public static void CollectAttribute(string attrText, ref AstostAlbumInfo album)
        {
            if (attrText.StartsWith("[*_^"))
                Console.WriteLine("AlbumName:{0}", attrText.Substring(4));
            switch (attrText)
            {
                case "BD":
                case "MG":
                case "Baidu":
                case "BDND":
                    Console.WriteLine("Cloud:{0}", attrText);
                    break;
            }
        }
        /// <summary>
        /// 合并AstostLister抓取的结果
        /// </summary>
        /// <param name="resultsdir">需要合并的页面所在路径</param>
        /// <param name="outputpath">输出文件地址，输出为html格式</param>
        public static void CombineResults(string resultsdir, string outputpath)
        {
            DirectoryInfo di = new DirectoryInfo(resultsdir);
            List<string> fns = new List<string>();
            foreach (FileInfo fi in di.GetFiles())
            {
                if (fi.Name.StartsWith(ResultFilenameHeader))
                    fns.Add(fi.FullName);
            }
            CombineResults(fns.ToArray(), outputpath);
        }
        /// <summary>
        /// 合并AstostLister抓取的结果
        /// </summary>
        /// <param name="resultsdir">需要合并的页面</param>
        /// <param name="outputpath">输出文件地址，输出为html格式</param>
        public static void CombineResults(string[] resultpages, string outputpath)
        {

        }
    }
}
