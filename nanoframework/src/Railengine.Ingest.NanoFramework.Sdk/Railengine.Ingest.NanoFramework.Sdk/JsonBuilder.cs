using System;
using System.Collections;
using System.Text;

namespace Railengine.Ingestion.Nano.Helpers
{
    public class JsonBuilder
    {
        /// <summary>
        /// Creates a JSON string from a flat Hashtable containing only primitive values or arrays of primitives.
        /// </summary>
        /// <returns>A JSON string representation of the Hashtable.</returns> 
        public static string FromHashTable(Hashtable message)
        {
            var jsonPayload = new StringBuilder("{");
            foreach (var kv in message.Keys)
            {
                var value = message[kv];
                jsonPayload.Append($"\"{kv}\":");
                jsonPayload.Append(FormatValue(value));
                jsonPayload.Append(",");
            }
            // trim trailing comma
            jsonPayload.Remove(jsonPayload.Length - 1, 1);
            jsonPayload.Append("}");
            return jsonPayload.ToString();
        }

        private static string FormatValue(object value)
        {
            if (value == null)
                return "null";

            if (value is bool b)
                return b ? "true" : "false";

            if (value is int || value is long || value is double || value is float)
                return value.ToString();

            if (value is ArrayList || value is Array)
            {
                var jsonArray = new StringBuilder("[");
                var enumerable = value as IEnumerable;
                foreach (var item in enumerable)
                {
                    jsonArray.Append(FormatValue(item));
                    jsonArray.Append(",");
                }
                if (jsonArray.Length > 1)
                    jsonArray.Remove(jsonArray.Length - 1, 1); // remove trailing comma
                jsonArray.Append("]");
                return jsonArray.ToString();
            }

            // Default: treat as string
            return $"\"{value}\"";
        }

    }
}
