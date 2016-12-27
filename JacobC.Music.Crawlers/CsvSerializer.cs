using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text;
using System.Threading.Tasks;

namespace JacobC.Music.Crawlers
{
    /// <summary>
    /// 序列化和反序列化对象列表到CSV中
	/// </summary>
    /// <remarks>
    /// TODO： 增加自定义表头的Attribute
    /// </remarks>
	public class CsvSerializer<T> where T : new()
    {
        #region Fields

        const char Separator = ',';

        List<PropertyInfo> _properties;
        int _row = 1;
        StreamReader _reader;
        string[] columns;

        #endregion Fields

        #region Properties
        /// <summary>
        /// 反序列化时是否忽略空行
        /// </summary>
        public bool IgnoreEmptyLines { get; set; } = true;
        /// <summary>
        /// 忽略除string外的引用类型
        /// </summary>
        public bool IgnoreReferenceTypesExceptString { get; set; } = true;

        /// <summary>
        /// <see cref="Escape"/>为true时，换行符的替换字符
        /// </summary>
        public string NewlineReplacement { get; set; } = "\t";
        /// <summary>
        /// <see cref="Escape"/>为true时，间隔符的替换字符
        /// </summary>
        public string Replacement { get; set; } = "\t";
        /// <summary>
        /// 是否替换换行符和分隔符(逗号)
        /// </summary>
        public bool Escape { get; set; } = false;

        /// <summary>
        /// 是否存入行号
        /// </summary>
        public bool UseLineNumbers { get; set; } = false;
        /// <summary>
        /// 当<see cref="UseLineNumbers"/>为true时，行号的标题
        /// </summary>
        public string RowNumberColumnTitle { get; set; } = "NO.";

        /// <summary>
        /// 是否对文本强制使用引号包含
        /// </summary>
        public bool UseTextQualifier { get; set; } = false;

        #endregion Properties

        /// <summary>
        /// CSV格式序列化器，从类型参数T的属性中初始化
        /// </summary>
        public CsvSerializer()
        {
            var type = typeof(T);

            var properties = type.GetProperties(BindingFlags.Public | BindingFlags.Instance
                | BindingFlags.GetProperty | BindingFlags.SetProperty);

            var q = properties.AsQueryable();

            if (IgnoreReferenceTypesExceptString)
                q = q.Where(a => a.PropertyType.IsValueType || a.PropertyType.Name == "String");

            var r = from a in q
                    where a.GetCustomAttribute<NonSerializedAttribute>() == null 
                        && a.GetCustomAttribute<CsvIgnoreAttribute>() == null
                    orderby a.Name
                    select a;

            _properties = r.ToList();
        }

        #region Deserialize
        /// <summary>
        /// 从流中读取CSV格式的一行数据
        /// </summary>
        /// <param name="stream">读取流</param>
        public string[] ParseLine(Stream stream)
        {
            List<string> result = new List<string>(columns?.Length ?? 0);
            if (_reader == null || !_reader.BaseStream.Equals(stream))
                _reader = new StreamReader(stream);
            ParseLine(stream, result);
            return result.ToArray();
        }

        /// <summary>
        /// 从流中读取CSV格式的一行数据
        /// </summary>
        /// <param name="stream">读取流</param>
        /// <param name="_reader">用来读取的StreamReader对象</param>
        internal void ParseLine(Stream stream, List<string> result)
        {
            //List<string> result = new List<string>(columns?.Length ?? 0);
            StringBuilder buffer = new StringBuilder();
            bool inquote = false, doublequote = false;
            do
            {
                string line = _reader.ReadLine();
                if (string.IsNullOrWhiteSpace(line))
                {
                    if (IgnoreEmptyLines)
                        continue;
                    else
                        throw new InvalidCsvFormatException($"Empty line!");
                }
                if (Escape)
                {
                    line = line.Replace(NewlineReplacement, Environment.NewLine)
                        .Replace(Replacement, ",");
                }
                foreach (var c in line)
                {
                    if (c == '\"')
                    {
                        if (doublequote)
                        {
                            buffer.Append('\"');
                            doublequote = false;
                        }
                        else
                            doublequote = true;
                    }
                    else
                    {
                        if (doublequote)
                        {
                            inquote = !inquote;
                            doublequote = false;
                        }
                        if (!inquote && c == Separator)
                        {
                            result.Add(buffer.ToString());
                            buffer.Clear();
                        }
                        else
                            buffer.Append(c);
                    }
                }
                if (doublequote)
                {
                    inquote = !inquote;
                    doublequote = false;
                }
                if (inquote) buffer.Append(Environment.NewLine);
                else break;
            }
            while (true);
            result.Add(buffer.ToString());
        }

        /// <summary>
        /// 从流中读取CSV标题行
        /// </summary>
        /// <param name="stream">读取的流</param>
        /// <exception cref="InvalidCsvFormatException"/>
        public void DeserializeHeader(Stream stream)
        {
            columns = ParseLine(stream);
            if (UseLineNumbers && !columns[0].Equals(RowNumberColumnTitle))
                throw new InvalidCsvFormatException("自动识别的行号必须位于第一列");
        }

        /// <summary>
        /// 从流中读取CSV格式对象
        /// </summary>
        /// <exception cref="InvalidCsvFormatException"/>
        public List<T> Deserialize(Stream stream)
        {
            if (_reader == null || !_reader.BaseStream.Equals(stream))
                _reader = new StreamReader(stream);

            var line = new List<string>(columns?.Length ?? 0);
            var data = new List<T>();

            while (!_reader.EndOfStream)
            {
                line.Clear();
                ParseLine(stream, line);
                data.Add(DeserializeLine(line));
            }
            return data;
        }

        /// <summary>
        /// 从流中读取CSV格式的一行对象
        /// </summary>
        /// <param name="stream">读取的流</param>
        /// <returns>反序列化得到的对象</returns>
        /// <exception cref="InvalidCsvFormatException"/>
        public T DeserializeLine(Stream stream)
        {
            return DeserializeLine(ParseLine(stream));
        }

        /// <summary>
        /// 从Parse过的文本对象中反序列化数据对象
        /// </summary>
        internal T DeserializeLine(IList<string> line)
        {
            var datum = new T();

            var start = UseLineNumbers ? 1 : 0;
            for (int i = start; i < line.Count; i++)
            {
                var value = line[i];
                PropertyInfo p;

                if (columns != null)
                {
                    //如果从csv中读到表头则优先按表格读取
                    var column = columns[i];

                    //忽略未找到的属性
                    p = _properties.FirstOrDefault(a => a.Name.Equals(column, StringComparison.InvariantCultureIgnoreCase));
                    if (p == null)
                        continue;
                }
                else p = _properties[i - start];

                try
                {
                    var converter = TypeDescriptor.GetConverter(p.PropertyType);
                    var convertedvalue = converter.ConvertFrom(value.Trim());
                    p.SetValue(datum, convertedvalue);
                }
                catch (Exception e)
                {
                    throw new InvalidCsvFormatException($"类型转换时出现错误:{e.Message}\n请考虑是否没有转换标题行！", e);
                }
            }

            return datum;
        }
        #endregion

        #region Serialize
        /// <summary>
        /// 序列化表头
        /// </summary>
        /// <param name="stream">写入的流</param>
        public void SerializeHeader(Stream stream)
        {
            var sw = new StreamWriter(stream);
            var header = _properties.Select(a => a.Name);
            if (UseLineNumbers)
            {
                string ntitle = RowNumberColumnTitle;
                if (Escape)
                    ntitle = ntitle.Replace(Separator.ToString(), Replacement)
                                   .Replace(Environment.NewLine, NewlineReplacement);
                if (UseTextQualifier || (!Escape &&
                        (ntitle.Contains(',') || ntitle.Contains('\"') || ntitle.Contains('\r') || ntitle.Contains('\n'))))
                    ntitle = $"\"{ntitle.Replace("\"", "\"\"")}\"";
                sw.Write(ntitle + ",");
            }
            sw.WriteLine(string.Join(Separator.ToString(), header));
            sw.Flush();
        }

        /// <summary>
        /// 序列化
        /// </summary>
        /// <param name="stream">写入的流</param>
        /// <param name="data">需要写入的对象</param>
        public void Serialize(Stream stream, IEnumerable<T> data)
        {
            var sb = new StringBuilder();
            var values = new List<string>();

            foreach (var item in data)
            {
                values.Clear();

                if (UseLineNumbers)
                    values.Add(_row++.ToString());

                foreach (var p in _properties)
                {
                    var raw = p.GetValue(item);
                    if(raw == null)
                    {
                        values.Add(string.Empty);
                        continue;
                    }
                    var value = raw.ToString();
                    if (Escape)
                        value = value.Replace(Separator.ToString(), Replacement)
                                     .Replace(Environment.NewLine, NewlineReplacement);

                    if (UseTextQualifier || (!Escape &&
                        (value.Contains(',') || value.Contains('\"') || value.Contains('\r') || value.Contains('\n'))))
                        value = $"\"{value.Replace("\"", "\"\"")}\"";

                    values.Add(value);
                }
                sb.AppendLine(string.Join(Separator.ToString(), values));
            }
            
            var sw = new StreamWriter(stream, Encoding.UTF8, sb.Length, true);
            sw.WriteLine(sb.ToString().Trim());
            sw.Close();
        }

        /// <summary>
        /// 序列化一行数据
        /// </summary>
        /// <param name="stream">写入的流</param>
        /// <param name="item">写入的对象</param>
        public void Serialize(Stream stream, T item)
        {
            var values = new List<string>();

            if (UseLineNumbers)
                values.Add(_row++.ToString());

            foreach (var p in _properties)
            {
                var raw = p.GetValue(item);
                if (raw == null)
                {
                    values.Add(string.Empty);
                    continue;
                }
                var value = raw.ToString();
                if (Escape)
                    value = value.Replace(Separator.ToString(), Replacement)
                                 .Replace(Environment.NewLine, NewlineReplacement);

                if (UseTextQualifier || (!Escape &&
                    (value.Contains(',') || value.Contains('\"') || value.Contains('\r') || value.Contains('\n'))))
                    value = $"\"{value.Replace("\"", "\"\"")}\"";

                values.Add(value);
            }
            string line = string.Join(Separator.ToString(), values);

            var sw = new StreamWriter(stream, Encoding.UTF8, line.Length, true);
            sw.WriteLine(line);
            sw.Close();
        }
        #endregion
    }

    /// <summary>
    /// 表示CSV格式错误的异常
    /// </summary>
    public class InvalidCsvFormatException : FormatException
    {
        /// <summary>
        /// CSV格式错误异常
        /// </summary>
        /// <param name="message">错误消息</param>
        public InvalidCsvFormatException(string message)
            : base(message)
        {
        }

        public InvalidCsvFormatException(string message, Exception ex)
            : base(message, ex)
        {
        }
    }

    /// <summary>
    /// 标志在CSV序列化时不序列化该成员
    /// </summary>
    public class CsvIgnoreAttribute : Attribute { }
}
