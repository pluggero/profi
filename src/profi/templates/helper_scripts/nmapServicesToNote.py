import argparse
import sys
import xml.etree.ElementTree as ET


def parse_nmap_xml(xml_file: str) -> dict[str, list[dict[str, str]]]:
    try:
        tree = ET.parse(xml_file)
    except FileNotFoundError:
        print(f"Error: file not found: {xml_file}", file=sys.stderr)
        sys.exit(1)
    except ET.ParseError as e:
        print(f"Error: failed to parse XML: {e}", file=sys.stderr)
        sys.exit(1)

    root = tree.getroot()
    hosts: dict[str, list[dict[str, str]]] = {}

    for host in root.findall("host"):
        ip_address = "unknown"
        hostname = "unknown"

        ip_element = host.find("address[@addrtype='ipv4']")
        if ip_element is not None:
            ip_address = ip_element.get("addr")

        hostname_elem = host.find("hostnames/hostname[@name]")
        if hostname_elem is not None:
            hostname = hostname_elem.get("name")

        ports: list[dict[str, str]] = []
        for ports_elem in host.findall("ports"):
            for port in ports_elem.findall("port"):
                port_data: dict[str, str] = {
                    "protocol": port.get("protocol"),
                    "portid": port.get("portid"),
                }

                service = port.find("service")
                if service is not None:
                    port_data["service_name"] = service.get("name")
                    port_data["product"] = service.get("product", "N/A")
                    port_data["version"] = service.get("version", "N/A")
                else:
                    # for udp scans this is not available
                    port_data["service_name"] = "N/A"
                    port_data["product"] = "N/A"
                    port_data["version"] = "N/A"

                ports.append(port_data)

        hosts[f"{hostname}-{ip_address}"] = ports

    return hosts


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract host services from an Nmap XML scan result."
    )
    parser.add_argument("xml_file", help="Path to the Nmap XML output file")
    args = parser.parse_args()

    hosts = parse_nmap_xml(args.xml_file)
    for host_key, ports in hosts.items():
        print(f"## {host_key}")
        for entry in ports:
            print(
                f"### Port {entry['portid']}/{entry['protocol']} "
                f"**{entry['service_name']}** ({entry['product']} {entry['version']})"
            )


if __name__ == "__main__":
    main()
