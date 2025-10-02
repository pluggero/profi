import json
import os
import argparse

def parse_item(item, level=2):
    markdown = ""

    # Check if the item contains nested items
    if "item" in item:
        markdown += "#" * level + " " + item["name"] + "\n"
        for sub_item in item["item"]:
            markdown += parse_item(sub_item, level + 1)
    # If the item doesn't contain nested items, it should contain a request
    elif "request" in item:
        method = item["request"].get("method", "METHOD")
        name = item["name"]
        url = item["request"]["url"]["raw"]
        markdown += "#" * level + " " + method + " " + name + " (" + url + ")\n"

    return markdown

def postman_to_markdown(json_file):
    # Check if file exists
    if not os.path.exists(json_file):
        print(f"Error: File does not exist!")
        return

    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error: Provided file is not a valid JSON file - {e}")
        return

    # Check if it's a Postman collection by checking for 'info' and 'item' keys
    if not all(key in data for key in ["info", "item"]):
        print(f"Error: Provided file does not seem to be a valid Postman collection!")
        return

    markdown = "# " + data["info"]["name"] + "\n"

    for item in data["item"]:
        markdown += parse_item(item, 2)

    print(markdown)

def main():
    # Initialize the argparse.ArgumentParser
    parser = argparse.ArgumentParser(description='Extracts the API Endpoints from a Postman collection to Markdown format.')
    # Define the expected command line arguments
    parser.add_argument('postman_collection_file', type=str, help='The path to the Postman collection JSON file')

    # Parse the command line arguments
    args = parser.parse_args()

    # Call the postman_to_markdown function with parsed arguments
    postman_to_markdown(args.postman_collection_file)

if __name__ == "__main__":
    main()

