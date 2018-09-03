using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Text;
using System.Threading.Tasks;
using JacobZ.Fluss.Win.Operations;

namespace JacobZ.Fluss.Win.Utils
{
    class OperationFinder
    {
        static List<ISourceOperation> _ops = new List<ISourceOperation>();

        static OperationFinder()
        {
            var types = Assembly.GetExecutingAssembly().GetTypes();
            foreach (Type t in types)
                if (t.GetInterface(nameof(ISourceOperation)) != null && !t.IsAbstract)
                    _ops.Add(Activator.CreateInstance(t) as ISourceOperation);
        }

        public static List<ISourceOperation> OperationInstances => _ops;
    }
}
