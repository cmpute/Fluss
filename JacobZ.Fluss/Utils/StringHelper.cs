using System;
using System.Collections.Generic;
using System.Text;

namespace JacobZ.Fluss.Utils
{
    static class StringHelper
    {
        public static List<string> SplitQuoteSpace(this string content)
        {
            List<string> list = new List<string>();
            StringBuilder cur = new StringBuilder();
            bool quote = false;
            foreach (char c in content.Trim())
            {
                if (c == ' ' && !quote)
                {
                    list.Add(cur.ToString());
                    cur.Clear();
                }
                else if (c == '"')
                    quote = !quote;
                else cur.Append(c);
            }
            if (cur.Length > 0) list.Add(cur.ToString());
            return list;
        }

        public static string JoinQuoteSpace(this IEnumerable<string> strs)
        {
            StringBuilder sb = new StringBuilder();
            var iter = strs.GetEnumerator();
            while (iter.MoveNext())
            {
                if (iter.Current.Contains(" "))
                    sb.Append("\"" + iter.Current + "\"");
                else sb.Append(iter.Current); sb.Append(' ');
            }
            sb.Remove(sb.Length - 1, 1);
            return sb.ToString();
        }
    }
}
