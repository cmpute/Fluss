using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Text;
using System.Threading.Tasks;
using JacobZ.Fluss.Operation;
using SharpCompress.Archives;

namespace JacobZ.Fluss.Utils
{
    public class OperationFactory
    {
        static List<Type> _op_types;
        static List<IArchiveEntryOperation> _op_instances;

        static OperationFactory()
        {
            var types = Assembly.GetExecutingAssembly().GetTypes();
            _op_types = types.Where(t => t.GetInterface(nameof(IArchiveEntryOperation)) != null && !t.IsAbstract).ToList();
            _op_instances = _op_types.Select(t => Activator.CreateInstance(t) as IArchiveEntryOperation).ToList();
        }

        public static List<Type> EntryOperationTypes => _op_types;

        public static bool CheckOperation(Type operation, params IArchiveEntry[] entries)
        {
            var opidx = _op_types.IndexOf(operation);
            return _op_instances[opidx].Pass(entries) != null;
        }

        public static IArchiveEntryOperation NewOperation(Type operation)
        {
            return Activator.CreateInstance(operation) as IArchiveEntryOperation;
        }
    }
}