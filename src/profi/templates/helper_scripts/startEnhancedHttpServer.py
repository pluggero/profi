import os
import re
from http.server import HTTPServer, SimpleHTTPRequestHandler
from typing import Optional, Tuple

import click

# Range support adapted from https://github.com/danvk/RangeHTTPServer
BYTE_RANGE_RE = re.compile(r"bytes=(\d+)-(\d+)?$")


def parse_byte_range(byte_range: str) -> Tuple[Optional[int], Optional[int]]:
    """Return the two numbers in 'bytes=123-456' or raise ValueError.

    The last number or both numbers may be None.
    """
    if byte_range.strip() == "":
        return None, None

    m = BYTE_RANGE_RE.match(byte_range)
    if not m:
        raise ValueError("Invalid byte range %s" % byte_range)

    first = int(m.group(1))
    last_group = m.group(2)
    last = int(last_group) if last_group is not None else None
    if last is not None and last < first:
        raise ValueError("Invalid byte range %s" % byte_range)
    return first, last


def copy_byte_range(infile, outfile, start=None, stop=None, bufsize=16 * 1024):
    """Like shutil.copyfileobj, but only copy an inclusive range of the stream."""
    if start is not None:
        infile.seek(start)
    while True:
        to_read = min(bufsize, stop + 1 - infile.tell() if stop else bufsize)
        buf = infile.read(to_read)
        if not buf:
            break
        outfile.write(buf)


class EnhancedRequestHandler(SimpleHTTPRequestHandler):
    show_headers = False
    allow_listing = False

    def do_GET(self):
        print("=" * 32)
        if EnhancedRequestHandler.show_headers:
            for key, value in self.headers.items():
                print(f"{key}: {value}")
        super().do_GET()

    def list_directory(self, path):
        if not self.allow_listing:
            self.send_error(403, "Directory listing is forbidden")
            return None
        return super().list_directory(path)

    def send_head(self):
        if "Range" not in self.headers:
            self.range = None
            return super().send_head()
        try:
            self.range = parse_byte_range(self.headers["Range"])
        except ValueError:
            self.send_error(400, "Invalid byte range")
            return None
        first, last = self.range
        if first is None:
            self.range = None
            return super().send_head()

        path = self.translate_path(self.path)
        ctype = self.guess_type(path)
        try:
            f = open(path, "rb")
        except IOError:
            self.send_error(404, "File not found")
            return None

        fs = os.fstat(f.fileno())
        file_len = fs[6]
        if first >= file_len:
            f.close()
            self.send_error(416, "Requested Range Not Satisfiable")
            return None

        if last is None or last >= file_len:
            last = file_len - 1
        response_length = last - first + 1

        self.send_response(206)
        self.send_header("Content-type", ctype)
        self.send_header("Content-Range", "bytes %s-%s/%s" % (first, last, file_len))
        self.send_header("Content-Length", str(response_length))
        self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
        self.end_headers()
        return f

    def end_headers(self):
        self.send_header("Accept-Ranges", "bytes")
        return super().end_headers()

    def copyfile(self, source, outputfile):
        rng = getattr(self, "range", None)
        if rng is None:
            return super().copyfile(source, outputfile)
        start, stop = rng
        copy_byte_range(source, outputfile, start, stop)


@click.command()
@click.option(
    "-b",
    "--bind",
    type=click.STRING,
    default="0.0.0.0",
    help="Address of the server to bind.",
)
@click.option(
    "-p", "--port", type=click.INT, required=True, help="Port of the server to bind."
)
@click.option(
    "-d",
    "--directory",
    type=click.Path(file_okay=False, resolve_path=True),
    help="Serve this directory.",
)
@click.option(
    "-sh",
    "--show-headers",
    is_flag=True,
    help="Whether to show request headers or not.",
)
@click.option(
    "-al",
    "--allow-listing",
    is_flag=True,
    help="Whether to enable directory listing or not.",
)
def main(bind, port, directory, show_headers, allow_listing):
    EnhancedRequestHandler.show_headers = show_headers
    EnhancedRequestHandler.allow_listing = allow_listing

    if directory:
        os.chdir(directory)

    server_address = (bind, port)
    httpd = HTTPServer(server_address, EnhancedRequestHandler)
    print(f"Serving {directory or os.getcwd()} over HTTP (http://{bind}:{port}/) ...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received, exiting.")
        httpd.server_close()


if __name__ == "__main__":
    main()
