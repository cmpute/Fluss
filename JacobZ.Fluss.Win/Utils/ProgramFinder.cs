using System;
using System.Collections.Generic;
using System.Linq;
using System.IO;
using System.Threading.Tasks;
using Microsoft.Win32;
using JacobZ.Fluss.Audio;
using JacobZ.Fluss.Utils;
using JacobZ.Fluss.Operation;

namespace JacobZ.Fluss.Win.Utils
{
    static class ProgramFinder
    {
        public static readonly string TempPath = Path.Combine(Path.GetTempPath(), "fluss");

        public static void FindCodec(AudioCodecType ext)
        {
            switch (ext)
            {
                case AudioCodecType.Wavpack:
                    WavPack.WavPackPath = SearchForExe("wavpack");
                    break;
                case AudioCodecType.TTA:
                    TTA.TTAPath = SearchForExe("tta");
                    break;
            }
        }

        internal static string SearchForExe(string name, params string[] additionalPaths)
        {
            string exeName = name + ".exe";

            // search for PATH
            foreach (var path in Environment.GetEnvironmentVariable("PATH").Split(';'))
                    if(Directory.Exists(path))
                    foreach (var file in Directory.GetFiles(path))
                        if (Path.GetFileName(file).ToLower() == exeName)
                            return file;

            // search for current dir
            foreach (var file in Directory.GetFiles(Environment.CurrentDirectory))
                if (Path.GetFileName(file).ToLower() == exeName)
                    return file;

            // search for registry
            string key = @"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\" + exeName;
            RegistryKey registryKey = Registry.LocalMachine.OpenSubKey(key);
            if (registryKey != null)
                return registryKey.GetValue("").ToString(); // "(Default)"

            // search for additional dirs
            foreach (var apath in additionalPaths)
                foreach (var file in Directory.GetFiles(apath))
                    if (Path.GetFileName(file).ToLower() == exeName)
                        return file;

            throw new FileNotFoundException("Cannot find the executable " + exeName);
        }
    }
}
