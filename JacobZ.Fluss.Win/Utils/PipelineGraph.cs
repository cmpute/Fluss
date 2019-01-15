using JacobZ.Fluss.Win.Models;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace JacobZ.Fluss.Win.Utils
{
    public class PipelineGraph
    {
        List<OperationDelegate> _operations = new List<OperationDelegate>();

        public void AddOperation(OperationDelegate operation)
        {
            _operations.Add(operation);
        }

        // return all targets to be removed
        public IEnumerable<OperationTarget> RemoveOperation(OperationDelegate operation)
        {
            HashSet<OperationTarget> retval = new HashSet<OperationTarget>();
            foreach (var target in operation.Outputs)
            {
                retval.Add(target);
                foreach (var postop in GetPosteriorOperations(target))
                    foreach (var posttarget in RemoveOperation(postop))
                        retval.Add(target);
            }
            _operations.Remove(operation);
            return retval;
        }

        public IEnumerable<OperationTarget> RemoveTarget(OperationTarget target)
        {
            var list = GetPriorOperations(target).ToArray(); // prevent modifying enumerator
            return list.SelectMany(op => RemoveOperation(op)).Distinct();
        }
        
        public IEnumerable<OperationDelegate> GetPriorOperations(OperationTarget target)
        {
            foreach (var op in _operations)
                if (op.Outputs.Contains(target))
                    yield return op;
        }

        private IEnumerable<OperationTarget> GetPriorTargets(OperationTarget target)
        {
            foreach (var op in GetPriorOperations(target))
                foreach (var pri in op.Inputs)
                    yield return pri;
        }
        public IEnumerable<OperationDelegate> GetPosteriorOperations(OperationTarget target)
        {
            foreach (var op in _operations)
                if (op.Inputs.Contains(target))
                    yield return op;
        }
        private IEnumerable<OperationTarget> GetPosteriorTargets(OperationTarget target)
        {
            foreach (var op in GetPosteriorOperations(target))
                foreach (var post in op.Outputs)
                    yield return post;
        }

        public IList<OperationTarget> Sort() { throw new NotImplementedException(); }
    }
}
