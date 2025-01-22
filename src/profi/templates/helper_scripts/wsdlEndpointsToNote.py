import xml.etree.ElementTree as ET
import argparse

def parse_wsdl(wsdl_file_path):
    # Parse the WSDL file
    tree = ET.parse(wsdl_file_path)
    root = tree.getroot()

    # Define namespaces to search tags properly
    namespaces = {
        'wsdl': 'http://schemas.xmlsoap.org/wsdl/',
        'soap': 'http://schemas.xmlsoap.org/wsdl/soap/',
        'xsd': 'http://www.w3.org/2001/XMLSchema'
    }

    # Use a set to track unique operations
    operations_set = set()

    # Iterate through all operations and add them to the set
    for operation in root.findall('.//wsdl:operation', namespaces):
        operations_set.add(operation.get('name'))

    # Sort operations in ascending order
    sorted_operations = sorted(operations_set)

    # Print operations without duplicates, in sorted order
    for operation_name in sorted_operations:
        print(f"### {operation_name}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Parse a WSDL file and outputs all endpoints in markdown.')
    parser.add_argument('wsdl_file_path', type=str, help='The path to the WSDL file')

    args = parser.parse_args()
    parse_wsdl(args.wsdl_file_path)

