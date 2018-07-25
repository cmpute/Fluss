using System;
using System.Collections.Generic;
using System.Text;

namespace JacobZ.Fluss.Archiver
{
    public class CompressSettings
    {
        /// <summary>
        /// 压缩时的分卷大小，0代表不分卷
        /// </summary>
        public UInt64 SubsectionSize { get; set; } = 0;

        /// <summary>
        /// 压缩包注释
        /// </summary>
        public string Comment { get; set; } = null;

        /// <summary>
        /// 是否添加恢复记录
        /// </summary>
        /// <remarks>默认对WinRAR使用%3的恢复记录，而对于其他压缩文件则使用MultiPar构建par3恢复文件</remarks>
        public bool AddRecoveryRecord { get; set; } = true;

        /// <summary>
        /// 压缩包密码，为<c>null</c>代表不加密
        /// </summary>
        public string Password { get; set; } = null;
    }
}
