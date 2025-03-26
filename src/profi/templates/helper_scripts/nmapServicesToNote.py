import argparse
import xml.etree.ElementTree as ET


def parse_nmap_xml(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    hosts = {}
    for host in root.findall("host"):
        extracted_data = []
        ip_address = "unknown"
        hostname = "unknown"

        ip_element = host.find("address[@addrtype='ipv4']")
        if ip_element is not None:
            ip_address = ip_element.get("addr")

        hostname_elem = host.find("hostnames/hostname[@name]")
        if hostname_elem is not None:
            hostname = hostname_elem.get("name")

        for ports in host.findall("ports"):
            for port in ports.findall("port"):
                port_data = {}
                port_data["protocol"] = port.get("protocol")
                port_data["portid"] = port.get("portid")

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

                extracted_data.append(port_data)
        hosts[f"{hostname}-{ip_address}"] = extracted_data
    return hosts


def save_to_file(data, output_path, ip_address):
    filename = f"{output_path}/{ip_address}-services.md"
    with open(filename, "w") as f:
        for entry in data:
            f.write(
                f"### Port {entry['portid']}/{entry['protocol']} **{entry['service_name']}** ({entry['product']} {entry['version']})\n"
            )


def main():
    parser = argparse.ArgumentParser(
        description="Extracts the host services from the nmap scan result."
    )
    parser.add_argument("xml_file", help="Path to the Nmap XML output file")
    parser.add_argument("output_path", help="Path to save the extracted file")
    args = parser.parse_args()

    hosts_info = parse_nmap_xml(args.xml_file)
    for key in hosts_info:
        save_to_file(hosts_info[key], args.output_path, key)


if __name__ == "__main__":
    main()
