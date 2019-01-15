using System;
using System.Collections.Generic;
using JacobZ.Fluss.Operation;

namespace JacobZ.Fluss.Win.Models
{
    public class OperationDelegate
    {
        public OperationTarget[] Inputs { get; set; }
        public OperationTarget[] Outputs { get; set; }
        public IArchiveEntryOperation Operation { get; set; }
    }
}
