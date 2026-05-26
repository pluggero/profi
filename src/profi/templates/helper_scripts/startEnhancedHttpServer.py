from http.server import HTTPServer, SimpleHTTPRequestHandler
import click
import datetime
import ipaddress
import os
import ssl

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

class EnhancedRequestHandler(SimpleHTTPRequestHandler):
    show_headers = False
    allow_listing = False

    def do_GET(self):
        print("=" * 32)
        if EnhancedRequestHandler.show_headers:
            for key, value in self.headers.items():
                print(f"{key}: {value}")
        super().do_GET()
    
    def list_directory(self, path):
        if not self.allow_listing:
            self.send_error(403, "Directory listing is forbidden")
            return None
        else:
            return super().list_directory(path)

    def do_POST(self):
        import cgi
        print("=" * 32)
        if EnhancedRequestHandler.show_headers:
            for key, value in self.headers.items():
                print(f"{key}: {value}")

        content_type = self.headers.get("Content-Type", "")
        if not content_type.startswith("multipart/form-data"):
            self.send_error(400, "Expected multipart/form-data")
            return

        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={"REQUEST_METHOD": "POST", "CONTENT_TYPE": content_type},
        )

        uploaded = []
        for field in form.list or []:
            if field.filename:
                filename = os.path.basename(field.filename)
                filepath = os.path.join(os.getcwd(), filename)
                with open(filepath, "wb") as f:
                    f.write(field.file.read())
                print(f"Uploaded: {filepath}")
                uploaded.append(filename)

        if uploaded:
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(f"Saved: {', '.join(uploaded)}\n".encode())
        else:
            self.send_error(400, "No file found in upload")


def generate_self_signed_cert(directory, bind):
    private_key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    )

    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "localhost")])
    cert_builder = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.now(datetime.timezone.utc))
        .not_valid_after(
            datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)
        )
    )

    if bind != "0.0.0.0":
        try:
            cert_builder = cert_builder.add_extension(
                x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address(bind))]),
                critical=False,
            )
        except ValueError:
            pass

    cert = cert_builder.sign(private_key, hashes.SHA256(), default_backend())

    key_path = os.path.join(directory, "server.key")
    cert_path = os.path.join(directory, "server.pem")

    with open(key_path, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ))

    with open(cert_path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    return cert_path, key_path


@click.command()
@click.option("-b", "--bind", type=click.STRING, default="0.0.0.0", help="Address of the server to bind.")
@click.option("-p", "--port", type=click.INT, required=True, help="Port of the server to bind.")
@click.option("-d", "--directory", type=click.Path(file_okay=False, resolve_path=True), help="Serve this directory.")
@click.option("-sh", "--show-headers", is_flag=True, help="Whether to show request headers or not.")
@click.option("-al", "--allow-listing", is_flag=True, help="Whether to enable directory listing or not.")
@click.option("--tls/--no-tls", default=True, help="Enable TLS (HTTPS). Default: enabled.")
@click.option("--tls-cert", type=click.Path(), default=None, help="Path to TLS certificate PEM file.")
@click.option("--tls-key", type=click.Path(), default=None, help="Path to TLS private key PEM file.")
def main(bind, port, directory, show_headers, allow_listing, tls, tls_cert, tls_key):
    EnhancedRequestHandler.show_headers = show_headers
    EnhancedRequestHandler.allow_listing = allow_listing

    if directory:
        os.chdir(directory)

    serve_dir = directory or os.getcwd()
    server_address = (bind, port)
    httpd = HTTPServer(server_address, EnhancedRequestHandler)

    if tls:
        if not tls_cert or not tls_key:
            cert_dir = os.path.dirname(serve_dir) if directory else serve_dir
            existing_cert = os.path.join(cert_dir, "server.pem")
            existing_key = os.path.join(cert_dir, "server.key")
            if os.path.exists(existing_cert) and os.path.exists(existing_key):
                tls_cert, tls_key = existing_cert, existing_key
                print(f"Using existing certificate: {tls_cert}")
            else:
                tls_cert, tls_key = generate_self_signed_cert(cert_dir, bind)
                print(f"Generated self-signed certificate: {tls_cert}")
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(certfile=tls_cert, keyfile=tls_key)
        httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)
        protocol = "https"
    else:
        protocol = "http"

    print(f"Serving {serve_dir} over {protocol.upper()} ({protocol}://{bind}:{port}/) ...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received, exiting.")
        httpd.server_close()

if __name__ == "__main__":
    main()
