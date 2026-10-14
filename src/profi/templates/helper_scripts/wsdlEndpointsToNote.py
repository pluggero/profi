import argparse
import sys
import xml.etree.ElementTree as ET


def parse_wsdl(wsdl_file_path: str) -> None:
    # Parse the WSDL file
    try:
        tree = ET.parse(wsdl_file_path)
    except FileNotFoundError:
        print(f"Error: file not found: {wsdl_file_path}", file=sys.stderr)
        sys.exit(1)
    except ET.ParseError as e:
        print(f"Error: failed to parse XML: {e}", file=sys.stderr)
        sys.exit(1)

    root = tree.getroot()

    # Define namespaces to search tags properly
    namespaces = {
        "wsdl": "http://schemas.xmlsoap.org/wsdl/",
        "soap": "http://schemas.xmlsoap.org/wsdl/soap/",
        "xsd": "http://www.w3.org/2001/XMLSchema",
    }

    # Use a set to track unique operations
    operations_set = set()

    # Iterate through all operations and add them to the set
    for operation in root.findall(".//wsdl:operation", namespaces):
        operations_set.add(operation.get("name"))

    # Sort operations in ascending order
    sorted_operations = sorted(operations_set)

    # Print operations without duplicates, in sorted order
    for operation_name in sorted_operations:
        print(f"### {operation_name}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract WSDL endpoints and output them in markdown."
    )
    parser.add_argument("wsdl_file_path", type=str, help="Path to the WSDL file")
    args = parser.parse_args()
    parse_wsdl(args.wsdl_file_path)


if __name__ == "__main__":
    main()
