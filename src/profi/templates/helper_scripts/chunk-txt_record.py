import sys
def format_string_to_txt_record(payload: str, chunk_size: int = 255, record_name: str = "cdn", domain: str = "example.com") -> list[str]:
    records = []
    record_num = 0

    for index in range(0, len(payload), chunk_size):
        chunk = payload[index:index + chunk_size]
        records.append(f"txt-record={record_num}.{record_name}.{domain},{chunk}")
        record_num += 1

    records.append(f"txt-record={domain},{record_num - 1}")

    return records


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(f"Usage: {sys.argv[0]} <payload> [chunk_size] [record_name] [domain]")
        print()
        print("  payload       The string to split into DNS TXT records")
        print("  chunk_size    Characters per record (default: 255)")
        print("  record_name   Subdomain label prefix (default: cdn)")
        print("  domain        Target domain (default: example.com)")
        sys.exit(0)

    payload = sys.argv[1]
    chunk_size = int(sys.argv[2]) if len(sys.argv) > 2 else 255
    record_name = sys.argv[3] if len(sys.argv) > 3 else "cdn"
    domain = sys.argv[4] if len(sys.argv) > 4 else "example.com"

    for line in format_string_to_txt_record(payload, chunk_size, record_name, domain):
        print(line)

