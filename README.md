# PRofi (Pentest Rofi)

<a id="readme-top"></a>

## Getting Started

### Prerequisites

- [rofi](https://github.com/davatorium/rofi)
- [esh](https://github.com/jirutka/esh)
- [net-tools](https://github.com/ecki/net-tools)
- [php](https://www.php.net/)
- [xclip](https://github.com/astrand/xclip) (for X11)

### Installation

1. Install prerequisites
2. Clone the repo
   ```sh
   git clone https://github.com/pluggero/profi.git
   cd profi
   ```
3. Install Tools
   ```sh
   python install.py
   ```
4. Install Python Requirements

   ```sh
   pip install -r requirements.txt
   ```

5. Install PRofi
   ```sh
   pip install .
   ```
   <p align="right">(<a href="#readme-top">back to top</a>)</p>

### Configuration

- The configuration file is located at `~/.config/profi/config.yaml`
- In this file you can configure the following:
  - `locations`: The locations of the tools and templates
  - `clipboard`: The clipboard options
  - `template options`: Options for setting various variables in the templates

### Tools

This list contains a (non-exhaustive) list of template-specific tools:

- [uuid](https://pkg.kali.org/pkg/ossp-uuid)

## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.
See the [open issues](https://github.com/pluggero/profi/issues) for a full list of proposed features (and known issues).

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feat/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feat/AmazingFeature`)
5. Open a Pull Request

<p align="right">(<a href="#readme-top">back to top</a>)</p>
