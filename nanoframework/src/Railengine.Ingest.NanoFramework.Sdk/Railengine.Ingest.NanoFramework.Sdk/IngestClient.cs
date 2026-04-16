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
            httpClient.SslProtocols = System.Net.Security.SslProtocols.Tls12;
            httpClient.DefaultRequestHeaders.Add(railAuthHeader, ingestApiKey);

            if (caCert != null)
            {
                httpClient.HttpsAuthentCert = caCert;
                httpClient.SslVerification = SslVerification.CertificateRequired;
            }
            else
            {
                // TODO: provide caCert in production
                httpClient.SslVerification = SslVerification.NoVerification;
            }
        }

        public bool Send(Hashtable payload)
        {
            var json = JsonBuilder.FromHashTable(payload);
            var content = new StringContent(json, Encoding.UTF8, "application/json");
            var response = httpClient.Post(ingestApiUrl, content);
            return response.IsSuccessStatusCode;
        }
    }
}
