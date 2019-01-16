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
            var list = GetPriorOperations(target).ToArray(); // prevent modifying enumerator
            return list.SelectMany(op => RemoveOperation(op)).Distinct();
        }
        
        public IEnumerable<OperationDelegate> GetPriorOperations(OperationTarget target)
        {
            foreach (var op in Operations)
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
            foreach (var op in Operations)
                if (op.Inputs.Contains(target))
                    yield return op;
        }
        private IEnumerable<OperationTarget> GetPosteriorTargets(OperationTarget target)
        {
            foreach (var op in GetPosteriorOperations(target))
                foreach (var post in op.Outputs)
                    yield return post;
        }

        public IList<OperationDelegate> Sort()
        {
            HashSet<OperationDelegate> candidate = new HashSet<OperationDelegate>(Operations);
            List<OperationDelegate> result = new List<OperationDelegate>();
            foreach (var op in candidate)
                if (op.Inputs.All(target => target.Kind == OperationTargetKind.Input))
                    result.AddRange(SortAt(op, candidate));

            result.Reverse();
            return result;
        }

        private IEnumerable<OperationDelegate> SortAt(OperationDelegate root, HashSet<OperationDelegate> mark)
        {
            foreach(var target in root.Outputs.Where(target => target.Kind != OperationTargetKind.Output))
                foreach(var postop in GetPosteriorOperations(target))
                {
                    if (mark.Contains(postop))
                        continue;
                    foreach (var result in SortAt(root, mark))
                        yield return result;
                }

            mark.Add(root);
            yield return root;
        }
    }
}
