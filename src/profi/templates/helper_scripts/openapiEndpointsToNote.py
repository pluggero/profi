import argparse
import json
import os

import yaml


def load_openapi_file(openapi_file_path):
    # Determine file format (JSON or YAML) and parse the OpenAPI file
    _, file_extension = os.path.splitext(openapi_file_path)

    with open(openapi_file_path, "r", encoding="utf-8") as file:
        if file_extension in [".yaml", ".yml"]:
            return yaml.safe_load(file)
        elif file_extension == ".json":
            return json.load(file)
        else:
            raise ValueError(
                "Unsupported file format. Only .json and .yaml/.yml are supported."
            )


def extract_api_endpoints(openapi_spec):
    # Extract API endpoints and methods from the OpenAPI spec
    paths = openapi_spec.get("paths", {})
    operations_set = set()

    # Iterate through paths and methods, add formatted operations to set
    for path, methods in paths.items():
        for method in methods:
            operation_name = f"{method.upper()} {path}"
            operations_set.add(operation_name)

    # Return sorted list of unique operations
    return sorted(operations_set)


def print_endpoints_in_markdown(endpoints):
    # Print each API endpoint in markdown format
    for endpoint in endpoints:
        print(f"### {endpoint}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Parse an OpenAPI file and output all API endpoints in markdown."
    )
    parser.add_argument(
        "openapi_file_path",
        type=str,
        help="The path to the OpenAPI file (YAML or JSON)",
    )

    args = parser.parse_args()

    # Load OpenAPI file and extract endpoints
    openapi_spec = load_openapi_file(args.openapi_file_path)
    endpoints = extract_api_endpoints(openapi_spec)

    # Output endpoints in markdown
    print_endpoints_in_markdown(endpoints)
