using System;
using System.Collections.Generic;
using System.Linq;
using System.IO;
using System.Threading.Tasks;
using JacobZ.Fluss.Archiver;
using JacobZ.Fluss.AudioCodec;
using Microsoft.Win32;

namespace JacobZ.Fluss.Win.Utils
{
    static class ProgramFinder
    {
        public static string FindArchiver<Archiver>()
            where Archiver : IArchiver
        {
            var archiver = typeof(Archiver);
            if (archiver == typeof(RAR))
                return Frar();
            else return null;
        }

        public static string FindAudioEncoder<Codec>()
            where Codec : IPcmCodec
        {
            var codec = typeof(Codec);
            if (codec == typeof(TTA))
                return Ftta();
            else if (codec == typeof(WavPack))
                return Fwavpack();
            else return null;
        }

        public static string FindAudioDecoder<Codec>()
            where Codec : IPcmCodec
        {
            var codec = typeof(Codec);
            if (codec == typeof(TTA))
                return Ftta();
            else if (codec == typeof(WavPack))
                return Fwvunpack();
            else return null;
        }

        private static string Fwavpack()
        {
            throw new NotImplementedException();
        }

        private static string Fwvunpack()
        {
            throw new NotImplementedException();
        }

        private static string Ftta()
        {
            throw new NotImplementedException();
        }

        private static string Frar()
        {
            // search for registry
            string key = @"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\WinRAR.exe";
            RegistryKey registryKey = Registry.LocalMachine.OpenSubKey(key);
            if (registryKey != null)
            {
                string path = registryKey.GetValue("Path").ToString();
                registryKey.Close();
                return Path.Combine(path, "rar.exe");
            }

            // search for PATH
            foreach (var path in Environment.GetEnvironmentVariable("PATH").Split(';'))
                foreach(var file in Directory.GetFiles(path))
                    if(Path.GetFileName(file).ToLower() == "rar.exe")
                        return file;

            // search for current dir
            foreach (var file in Directory.GetFiles(Environment.CurrentDirectory))
                if (Path.GetFileName(file).ToLower() == "rar.exe")
                    return file;

            return null;
        }
    }
}
