﻿using System;
using System.Diagnostics;
using System.IO;

namespace JacobZ.Fluss.Audio
{
    using JacobZ.Fluss.Utils;

    public class TTA : IPcmCodec
    {
        string _tta;

        public TTA(string ttaPath) { _tta = ttaPath; }

        public Stream Decode(string inputFile, PcmEncodingType type)
        {
            Process exec = ProcessHelper.Generate(_tta, "-d", inputFile, "-");
            exec.Start();
            return new ProcessStream(exec, ProcessPipeType.Stdout);
        }

        public void Encode(string outputFile, Stream input, PcmEncodingType type)
        {
            Process exec = ProcessHelper.Generate(_tta, "-e", "-", outputFile);
            exec.Start();
            input.CopyTo(exec.StandardInput.BaseStream);
            exec.StandardInput.Close();
            exec.EnsureExit();
        }
    }
}
