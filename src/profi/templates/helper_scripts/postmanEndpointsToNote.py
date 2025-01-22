import json
import os
import argparse

def parse_item(item, indent=0):
    markdown = ""

    # Check if the item contains nested items
    if "item" in item:
        markdown += "\n" + "\t" * indent + "- [ ] " + item["name"]
        for sub_item in item["item"]:
            markdown += parse_item(sub_item, indent + 1)
    # If the item doesn't contain nested items, it should contain a request
    elif "request" in item:
        markdown += "\n" + "\t" * indent + "- [ ] " + "**" + item["request"].get("method", "METHOD") + "** " + item["name"] + " (`" + item["request"]["url"]["raw"] + "`)"
        description = item["request"].get("description", "").strip()
        if description:  # Check if description is not empty
            description = description.replace('\n', ' ')  # Remove newline characters
            markdown += "\n" + "\t" * (indent + 1) + "- Description: " + description

    return markdown

def postman_to_markdown(json_file, output_dir):
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

    markdown = "- " + data["info"]["name"]

    for item in data["item"]:
        markdown += parse_item(item, 1)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    md_file = os.path.join(output_dir, data["info"]["name"] + ".md")

    with open(md_file, 'w') as f:
        f.write(markdown)

def main():
    # Initialize the argparse.ArgumentParser
    parser = argparse.ArgumentParser(description='Extracts the API Endpoints from a Postman collection to Markdown format.')
    # Define the expected command line arguments
    parser.add_argument('postman_collection_file', type=str, help='The path to the Postman collection JSON file')
    parser.add_argument('output_path', type=str, help='The directory to output the markdown file')

    # Parse the command line arguments
    args = parser.parse_args()

    # Call the postman_to_markdown function with parsed arguments
    postman_to_markdown(args.postman_collection_file, args.output_path)

if __name__ == "__main__":
    main()

