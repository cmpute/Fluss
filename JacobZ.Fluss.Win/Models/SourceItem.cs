﻿using System;
using System.Collections.Generic;
using JacobZ.Fluss.Win.Operations;

namespace JacobZ.Fluss.Win.Models
{
    sealed class SourceItem
    {
        public string FilePath { get; set; }
        public ISourceOperation[] RelatedOperations { get; set; }
    }
}
