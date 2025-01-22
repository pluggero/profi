import argparse
import csv
import os
import re
import sys
import zipfile
from pathlib import Path


def find_file_in_zip(zip_file, filename):
    with zipfile.ZipFile(zip_file, "r") as z:
        for f in z.namelist():
            if filename in f:
                return f
    return None


def extract_ip_data(zip_file, hosts_path, output_dir):
    with zipfile.ZipFile(zip_file, "r") as z:
        with z.open(hosts_path, "r") as file:
            # Decode the byte stream to string
            lines = (line.decode("utf-8") for line in file)
            csv_reader = csv.reader(lines)
            next(csv_reader)  # Skip the header
            for row in csv_reader:
                ip = row[0].strip('"')
                if re.match(r"[0-9]+(?:\.[0-9]+){3}", ip):
                    ip_file = Path(output_dir, f"{ip}.md")
                    with open(ip_file, "w") as out_file:
                        extract_service_data(zip_file, ip, out_file)


def extract_service_data(zip_file, ip, out_file):
    services_path = find_file_in_zip(zip_file, "services.csv")
    if services_path:
        with zipfile.ZipFile(zip_file, "r") as z:
            with z.open(services_path, "r") as file:
                # Decode the byte stream to string
                lines = (line.decode("utf-8") for line in file)
                csv_reader = csv.reader(lines)
                next(csv_reader)  # Skip the header
                services = []
                for row in csv_reader:
                    if row[6] == "OPEN" and row[0].strip('"') == ip:
                        port_protocol = f"{row[4]}/{row[3]}" if row[4] else row[3]
                        service_info = (
                            f"### Port {port_protocol} **{row[2]}** ({row[5]})"
                        )
                        services.append(service_info)
                services.sort(
                    key=lambda x: (
                        int(re.search(r"(\d+)", x).group()),
                        x.split("/")[-1],
                    )
                )
                for service in services:
                    out_file.write(service + "\n")


def setup_argparse():
    parser = argparse.ArgumentParser(
        description="Extract IP and services data from a ZIP file."
    )
    parser.add_argument(
        "zip_file", type=str, help="Path to the ZIP file containing the data."
    )
    parser.add_argument(
        "output_directory", type=str, help="Directory to store the output files."
    )
    return parser


def main():
    parser = setup_argparse()
    args = parser.parse_args()

    if not os.path.isfile(args.zip_file):
        print("Error: ZIP file not found at the provided path.")
        sys.exit(1)

    hosts_path = find_file_in_zip(args.zip_file, "hosts.csv")
    if not hosts_path:
        print("Error: hosts.csv not found inside the ZIP file.")
        sys.exit(1)

    if not os.path.exists(args.output_directory):
        os.makedirs(args.output_directory)

    extract_ip_data(args.zip_file, hosts_path, args.output_directory)
    print("Export successful!")


if __name__ == "__main__":
    main()
