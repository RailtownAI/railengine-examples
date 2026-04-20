using System.Collections;
using System.Net.Http;
using System.Net.Security;
using System.Security.Cryptography.X509Certificates;
using System.Text;
using Railengine.Ingestion.Nano.Helpers;

namespace Railengine.Ingest.NanoFramework.Sdk
{
    public class IngestClient
    {
        private const string railAuthHeader = "x-rail-auth";
        private readonly string ingestApiUrl;
        private readonly HttpClient httpClient;

        /// <param name="caCert">Root CA certificate for SSL validation. Pass null to skip validation (development only).</param>
        public IngestClient(string ingestApiUrl, string ingestApiKey, X509Certificate caCert = null)
        {
            this.ingestApiUrl = ingestApiUrl;

            httpClient = new HttpClient();
            httpClient.SslProtocols = SslProtocols.Tls12;
            httpClient.DefaultRequestHeaders.Add(railAuthHeader, ingestApiKey);

            if (caCert != null)
            {
                httpClient.HttpsAuthentCert = caCert;
                httpClient.SslVerification = SslVerification.CertificateRequired;
            }
            else
            {
                httpClient.SslVerification = SslVerification.NoVerification;
            }
        }

        /// <summary>
        /// Sends data to a Railengine.
        /// </summary>
        /// <param name="data">
        /// A Hashtable where keys are strings and values are primitive types (int, string, bool, etc.)
        /// or arrays of primitives. Does not support nested objects or multi-dimensional arrays.
        /// </param>
        /// <returns>true for success, false for failure</returns>
        public bool Send(Hashtable payload)
        {
            var json = JsonBuilder.FromHashTable(payload);
            return Send(json);
        }

        /// <summary>
        /// Sends data to a Railengine.
        /// </summary>
        /// <param name="jsonData">A JSON string representing a serialized object.</param>
        /// <param name="encoding">The character encoding used, defaults to UTF8</param>
        /// <returns>true for success, false for failure</returns>
        public bool Send(string jsonData, Encoding encoding = null)
        {
            encoding ??= Encoding.UTF8;

            var content = new StringContent(jsonData, encoding, "application/json");
            var response = httpClient.Post(ingestApiUrl, content);
            return response.IsSuccessStatusCode;
        }
    }
}
