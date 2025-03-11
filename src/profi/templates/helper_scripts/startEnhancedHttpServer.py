from http.server import HTTPServer, SimpleHTTPRequestHandler
import click
import os

class EnhancedRequestHandler(SimpleHTTPRequestHandler):
    show_headers = False

    def do_GET(self):
        print("=" * 32)
        if EnhancedRequestHandler.show_headers:
            for key, value in self.headers.items():
                print(f"{key}: {value}")
        super().do_GET()

@click.command()
@click.option("-b", "--bind", type=click.STRING, default="0.0.0.0", help="Address of the server to bind.")
@click.option("-p", "--port", type=click.INT, required=True, help="Port of the server to bind.")
@click.option("-d", "--directory", type=click.Path(file_okay=False, resolve_path=True), help="Serve this directory.")
@click.option("-sh", "--show-headers", is_flag=True, help="Whether to show request headers or not.")
def main(bind, port, directory, show_headers):
    EnhancedRequestHandler.show_headers = show_headers

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
