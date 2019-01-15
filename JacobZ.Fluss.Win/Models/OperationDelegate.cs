using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using JacobZ.Fluss.Win.Operations;

namespace JacobZ.Fluss.Win.Models
{
    class OperationDelegate
    {
        public List<OperationTarget> Inputs { get; set; }
        public List<OperationTarget> Outputs { get; set; }
        public ISourceOperation Operation { get; private set; }
    }
}
