using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace JacobC.Music
{
    /// <summary>
    /// 信息条目的基类
    /// </summary>
    public class InfoBase
    {
        /// <summary>
        /// 信息来源
        /// string: RetrieveSource 信息获取的来源数据库/网站的标识符
        /// object: RetrieveParameter 从RetrieveSource获取信息的参数
        /// </summary>
        /// <remarks>
        /// 例如从A坛下载的专辑可以有一个Keypair是
        /// ["AstostID"]=1000xxx
        /// 又例如找到Vgmdb中对应的条目以后可以是
        /// ["Vgmdb"]={Type=Album, ID=XXXX}，是一个结构体
        /// </remarks>
        public Dictionary<string, object> InfoSource;
    }
}
