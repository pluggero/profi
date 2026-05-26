from http.server import HTTPServer, SimpleHTTPRequestHandler
import click
import datetime
import ipaddress
import os
import ssl
from urllib.parse import urlparse, parse_qs

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID

class EnhancedRequestHandler(SimpleHTTPRequestHandler):
    show_headers = False
    allow_listing = False

    def do_HEAD(self):
        print("=" * 32)
        self.send_response(200)
        self.end_headers()

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
        import email.parser
        print("=" * 32)
        if EnhancedRequestHandler.show_headers:
            for key, value in self.headers.items():
                print(f"{key}: {value}")

        content_type = self.headers.get("Content-Type", "")
        length = int(self.headers.get("Content-Length", 0))
        uploaded = []

        if content_type.startswith("multipart/form-data"):
            body = self.rfile.read(length)
            mime_data = f"Content-Type: {content_type}\r\n\r\n".encode() + body
            msg = email.parser.BytesParser().parsebytes(mime_data)

            payload = msg.get_payload()
            if not isinstance(payload, list):
                self.send_error(400, "Failed to parse multipart data")
                return
            for part in payload:
                disposition = part.get("Content-Disposition", "")
                if "filename=" not in disposition:
                    continue
                filename = os.path.basename(part.get_filename() or "")
                if not filename:
                    continue
                filepath = os.path.join(os.getcwd(), filename)
                with open(filepath, "wb") as f:
                    f.write(part.get_payload(decode=True))
                print(f"Uploaded: {filepath}")
                uploaded.append(filename)

        elif content_type.startswith("application/octet-stream") or content_type == "":
            # Try Content-Disposition request header first (WebClient.UploadFile sends this)
            disposition = self.headers.get("Content-Disposition", "")
            filename = ""
            if "filename=" in disposition:
                for part in disposition.split(";"):
                    part = part.strip()
                    if part.lower().startswith("filename="):
                        filename = part[9:].strip().strip('"').strip("'")
                        break
            if not filename:
                # Fall back to ?filename= query param (iwr with query string)
                parsed = urlparse(self.path)
                params = parse_qs(parsed.query)
                filename = params.get("filename", ["upload"])[0]
            filename = os.path.basename(filename) or "upload"
            filepath = os.path.join(os.getcwd(), filename)
            with open(filepath, "wb") as f:
                f.write(self.rfile.read(length))
            print(f"Uploaded: {filepath}")
            uploaded.append(filename)

        else:
            self.send_error(400, "Unsupported Content-Type")
            return

        if uploaded:
            body = f"Saved: {', '.join(uploaded)}\n".encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_error(400, "No file found in upload")


class TLSHTTPServer(HTTPServer):
    def __init__(self, server_address, RequestHandlerClass, ssl_context):
        super().__init__(server_address, RequestHandlerClass)
        self.ssl_context = ssl_context

    def get_request(self):
        conn, addr = self.socket.accept()
        try:
            ssl_conn = self.ssl_context.wrap_socket(conn, server_side=True)
            return ssl_conn, addr
        except ssl.SSLError as e:
            print(f"[TLS] Handshake failed from {addr}: {e}")
            conn.close()
            raise


def generate_self_signed_cert(directory, bind, san=None):
    private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())

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

    cert_builder = cert_builder.add_extension(
        x509.KeyUsage(
            digital_signature=True,
            key_encipherment=True,
            content_commitment=False,
            key_agreement=False,
            key_cert_sign=False,
            crl_sign=False,
            encipher_only=False,
            decipher_only=False,
            data_encipherment=False,
        ),
        critical=True,
    ).add_extension(
        x509.ExtendedKeyUsage([x509.oid.ExtendedKeyUsageOID.SERVER_AUTH]),
        critical=False,
    )

    san_ip = san or (bind if bind != "0.0.0.0" else None)
    if san_ip:
        try:
            cert_builder = cert_builder.add_extension(
                x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address(san_ip))]),
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
@click.option("--san", type=click.STRING, default=None, help="IP or hostname to include as SAN in generated cert.")
def main(bind, port, directory, show_headers, allow_listing, tls, tls_cert, tls_key, san):
    EnhancedRequestHandler.show_headers = show_headers
    EnhancedRequestHandler.allow_listing = allow_listing

    if directory:
        os.chdir(directory)

    serve_dir = directory or os.getcwd()
    server_address = (bind, port)

    if tls:
        if not tls_cert or not tls_key:
            cert_dir = os.path.dirname(serve_dir) if directory else serve_dir
            existing_cert = os.path.join(cert_dir, "server.pem")
            existing_key = os.path.join(cert_dir, "server.key")
            if os.path.exists(existing_cert) and os.path.exists(existing_key):
                tls_cert, tls_key = existing_cert, existing_key
                print(f"Using existing certificate: {tls_cert}")
            else:
                tls_cert, tls_key = generate_self_signed_cert(cert_dir, bind, san)
                print(f"Generated self-signed certificate: {tls_cert}")
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        ctx.set_ciphers("HIGH:!aNULL:!MD5:!RC4")
        ctx.load_cert_chain(certfile=tls_cert, keyfile=tls_key)
        httpd = TLSHTTPServer(server_address, EnhancedRequestHandler, ctx)
        protocol = "https"
    else:
        httpd = HTTPServer(server_address, EnhancedRequestHandler)
        protocol = "http"

    print(f"Serving {serve_dir} over {protocol.upper()} ({protocol}://{bind}:{port}/) ...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received, exiting.")
        httpd.server_close()

if __name__ == "__main__":
    main()
