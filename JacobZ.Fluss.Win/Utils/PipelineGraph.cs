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
        List<OperationDelegate> Operations { get; } = new List<OperationDelegate>();

        public void AddOperation(OperationDelegate operation)
        {
            Operations.Add(operation);
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
            Operations.Remove(operation);
            return retval;
        }

        public IEnumerable<OperationTarget> RemoveTarget(OperationTarget target)
        {
            var priorop = GetPriorOperation(target);
            if (priorop != null) return RemoveOperation(priorop);
            else return Enumerable.Empty<OperationTarget>();
        }

        // Each target only have one prior operation which generates this target
        public OperationDelegate GetPriorOperation(OperationTarget target)
        {
            foreach (var op in Operations)
                if (op.Outputs.Contains(target))
                    return op;
            return null;
        }

        public IEnumerable<OperationTarget> GetPriorTargets(OperationTarget target)
        {
            var priorop = GetPriorOperation(target);
            if(priorop != null)
                foreach (var pri in priorop.Inputs)
                    yield return pri;
        }
        public IEnumerable<OperationDelegate> GetPosteriorOperations(OperationTarget target)
        {
            foreach (var op in Operations)
                if (op.Inputs.Contains(target))
                    yield return op;
        }
        public IEnumerable<OperationTarget> GetPosteriorTargets(OperationTarget target)
        {
            foreach (var op in GetPosteriorOperations(target))
                foreach (var post in op.Outputs)
                    yield return post;
        }

        public IList<OperationDelegate> Sort()
        {
            HashSet<OperationDelegate> candidate = new HashSet<OperationDelegate>();
            List<OperationDelegate> result = new List<OperationDelegate>();
            foreach (var op in Operations)
                if (op.Inputs.All(target => target.Kind == OperationTargetKind.Input))
                    result.AddRange(SortAt(op, candidate));

            result.Reverse();
            return result;
        }

        private IEnumerable<OperationDelegate> SortAt(OperationDelegate root, HashSet<OperationDelegate> mark)
        {
            foreach(var target in root.Outputs)
                foreach(var postop in GetPosteriorOperations(target))
                {
                    if (mark.Contains(postop))
                        continue;
                    foreach (var result in SortAt(postop, mark))
                        yield return result;
                }

            mark.Add(root);
            yield return root;
        }
    }
}
