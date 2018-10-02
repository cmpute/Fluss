using System;
using System.Collections.Generic;
using JacobZ.Fluss.Win.Operations;

namespace JacobZ.Fluss.Win.Models
{
    sealed class OutputItem
    {
        public string FileName { get; set; }
        public ISourceOperation[] RelatedOperations { get; set; }
    }
}
