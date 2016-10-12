using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace JacobC.Music.Crawlers
{
    public enum LoginResult
    {
        /// <summary>
        /// 登录成功
        /// </summary>
        Success,
        /// <summary>
        /// 密码错误
        /// </summary>
        WrongPassword,
        /// <summary>
        /// 验证码错误
        /// </summary>
        WrongVerifyCode
    }
}
