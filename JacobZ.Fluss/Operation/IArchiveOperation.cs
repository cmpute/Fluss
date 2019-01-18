using System;
using System.Collections.Generic;
using System.Text;
using SharpCompress.Archives;

namespace JacobZ.Fluss.Operation
{
    public interface IArchiveEntryOperation
    {
        /// <summary>
        /// Get recommended output path for give inputs. If the operation is not suitable then return <c>null</c>.
        /// </summary>
        /// <param name="archive">Music archive input</param>
        /// <param name="entryIndices">Indices for selected archive entries</param>
        /// <returns>List of recommended output path, <c>null</c> if the operation is not suitable</returns>
        string[] Pass(params IArchiveEntry[] archiveEntries);

        /// <summary>
        /// Run the operation on given input
        /// </summary>
        /// <param name="archive">Music archive input</param>
        /// <param name="entryIndices">Indices for selected archive entries</param>
        /// <param name="outputPath">Paths for output files</param>
        void Execute(IArchiveEntry[] entryIndices, params string[] outputPath);

        /// <summary>
        /// Access the properties of the operation
        /// </summary>
        object Properties { get; set; }
    }
    
    public interface IArchiveOperation
    {
        /// <summary>
        /// Get recommended output path for give inputs. If the operation is not suitable then return <c>null</c>.
        /// </summary>
        /// <param name="archive">Music archive</param>
        /// <returns>List of recommended output path, <c>null</c> if the operation is not suitable</returns>
        string[] Pass(MusicArchive archive);

        /// <summary>
        /// Run the operation on given input
        /// </summary>
        /// <param name="archive">Music archive input</param>
        /// <param name="outputPath">Paths for output files</param>
        void Execute(MusicArchive archive, params string[] outputPath);
    }
}
