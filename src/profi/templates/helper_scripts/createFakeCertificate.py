#!/usr/bin/env python3

import argparse
import datetime
import os

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID


def load_pfx(pfx_path, pfx_password):
    # Load private key and certificate from PFX file
    with open(pfx_path, "rb") as f:
        pfx_data = f.read()

    private_key, certificate, additional_certs = pkcs12.load_key_and_certificates(
        pfx_data, pfx_password.encode(), default_backend()
    )

    return private_key, certificate


def create_self_signed_ca(output_dir, subject):
    # Generate private key for the CA
    private_key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    )

    # Self-signed CA certificate with the same subject as the original
    issuer = subject

    # CA certificate
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.now(datetime.timezone.utc))
        .not_valid_after(
            datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365)
        )  # 1 year validity
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .sign(private_key, hashes.SHA256(), default_backend())
    )

    ca_key_path = os.path.join(output_dir, "ca_key.pem")
    ca_cert_path = os.path.join(output_dir, "ca_cert.pem")

    # Write CA private key to a file
    with open(ca_key_path, "wb") as f:
        f.write(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )

    # Write CA certificate to a file
    with open(ca_cert_path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    print(f"Self-signed CA created and saved to {ca_cert_path}")
    return private_key, cert


def create_client_cert(ca_private_key, ca_cert, subject, extensions, output_dir):
    # Generate private key for the client certificate
    client_private_key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    )

    # Client certificate
    cert_builder = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(ca_cert.subject)  # Issued by the CA
        .public_key(client_private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.now(datetime.timezone.utc))
        .not_valid_after(
            datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365)
        )  # 1 year validity
    )

    # Add extensions from the original certificate
    for extension in extensions:
        cert_builder = cert_builder.add_extension(extension.value, extension.critical)

    # Sign the client certificate with the CA's private key
    client_cert = cert_builder.sign(ca_private_key, hashes.SHA256(), default_backend())

    client_key_path = os.path.join(output_dir, "client_key.pem")
    client_cert_path = os.path.join(output_dir, "client_cert.pem")

    # Write client private key to a file
    with open(client_key_path, "wb") as f:
        f.write(
            client_private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )

    # Write client certificate to a file
    with open(client_cert_path, "wb") as f:
        f.write(client_cert.public_bytes(serialization.Encoding.PEM))

    print(f"Client certificate created and saved to {client_cert_path}")

    return client_private_key, client_cert


def create_pfx(output_dir, client_private_key, client_cert, ca_cert, pfx_password):
    # Convert the client certificate and private key to PFX/PKCS#12 format
    pfx_data = pkcs12.serialize_key_and_certificates(
        name=b"MyClientCert",  # Optional friendly name
        key=client_private_key,
        cert=client_cert,
        cas=[ca_cert],  # Include the CA certificate
        encryption_algorithm=serialization.BestAvailableEncryption(
            pfx_password.encode()
        ),  # Encrypt with password
    )

    pfx_output_path = os.path.join(output_dir, "client_cert.pfx")

    # Write the PFX data to a file
    with open(pfx_output_path, "wb") as f:
        f.write(pfx_data)

    print(f"PFX file created and saved to {pfx_output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate self-signed CA, client certificate, and PFX file using metadata from an existing PFX file."
    )
    parser.add_argument("pfx_path", type=str, help="Path to the input PFX file")
    parser.add_argument(
        "pfx_password", type=str, help="Password for the input PFX file"
    )
    parser.add_argument(
        "output_dir",
        type=str,
        help='Directory where the "fake-cert" folder will be created',
    )

    args = parser.parse_args()

    # Create the output directory "fake-cert" inside the provided directory
    output_dir = os.path.join(args.output_dir, "fake-cert")
    os.makedirs(output_dir, exist_ok=True)

    # Step 1: Load the original certificate from PFX file
    original_private_key, original_cert = load_pfx(args.pfx_path, args.pfx_password)

    # Step 2: Extract subject and extensions from the original certificate
    subject = original_cert.subject
    extensions = original_cert.extensions

    # Step 3: Create self-signed CA using the extracted subject
    ca_private_key, ca_cert = create_self_signed_ca(output_dir, subject)

    # Step 4: Create a new client certificate signed by the self-signed CA
    client_private_key, client_cert = create_client_cert(
        ca_private_key, ca_cert, subject, extensions, output_dir
    )

    # Step 5: Package the client certificate, private key, and CA into a PFX file using the same password as the input PFX
    create_pfx(output_dir, client_private_key, client_cert, ca_cert, args.pfx_password)


if __name__ == "__main__":
    main()
