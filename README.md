# PRofi (Pentest Rofi)

[![CI](https://github.com/pluggero/profi/actions/workflows/ci.yml/badge.svg)](https://github.com/pluggero/profi/actions/workflows/ci.yml)

<a id="readme-top"></a>

## Usage

### Tags

You can search for templates either by name or by tag.
All our templates have sounding names that should be self explaining, what this template is for.
Every template may have some tags, that group them together, in case you need some inspiration of which template could help you.

We currently support these tags:

| Tag                                    | What's it for?                                                                                                                             |
| -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| <span color='cyan'>web</span>          | For templates that target web applications<br>- The line between `web` and `api` is blurry, but `web` templates usually require a frontend |
| <span color='teal'>api</span>          | For templates that target APIs                                                                                                             |
| <span color='orange'>system</span>     | For templates that target services that may be host independent (e.g. ssh, ftp, smb, ...)                                                  |
| <span color='green'>mobile</span>      | For templates that target mobile devices (iOS, Android, ...)                                                                               |
| <span color='lightblue'>windows</span> | For templates that target Windows (usually combined with others)                                                                           |
| <span color='yellow'>linux</span>      | For templates that target Linux (usually combined with others)                                                                             |
| <span color='blue'>domain</span>       | For templates that require a domain joined host                                                                                            |
| <span color='red'>shell</span>         | For templates that get you a reverse shell                                                                                                 |
| <span color='purple'>cracking</span>   | For templates that help you get crackable material and crack it                                                                            |
| <span color='pink'>privesc</span>      | For templates that help you elevate your privileges                                                                                        |
| <span color='gray'>proxy</span>        | For templates that help you setting up a proxy for pivoting to different systems (ligolo-ng, chisel, ssh port forwarding)                  |
| <span color='black'>wordlist</span>    | For templates that help you creating wordlists                                                                                             |
| <span color='tomato'>utils</span>      | For templates that run utility scripts                                                                                                     |
| <span color='tan'>enum</span>          | For templates that help you to enumerate targets                                                                                           |
| <span color='plum'>xss</span>          | For templates that help you to exploit xss vulnerabilities                                                                                 |

Some information on how tags are used:

- Tags should be assigned to templates according to the target system
- We currently assume, _PRofi_ is run on a Linux system, thus the pasted commands should all run on Linux. This does not "justify" the Linux tag.

## Getting Started

### Prerequisites

- [rofi](https://github.com/davatorium/rofi)
- [php](https://www.php.net/)
- [xclip](https://github.com/astrand/xclip) (for X11)

### Installation

1. Install prerequisites
2. Clone the repo
   ```sh
   git clone https://github.com/pluggero/profi.git
   cd profi
   ```
3. Install Python Requirements

   ```sh
   pip install -r requirements.txt
   ```

4. Install Tools

   ```sh
   python install.py
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

#### Tags

Using the configuration file, you can specify and configure custom color codings for each tag. Rofi uses the [Pango Markup Language](https://docs.gtk.org/Pango/pango_markup.html) for styling.
`PRofi` will only render those tags in color, which have a color assigned in the config file. All other tags will default to a white font color.

There are two ways in which the colors can be specified:

##### By name ([X11 color names](https://en.wikipedia.org/wiki/X11_color_names))

```

"<tagname>": "green"

```

##### By hexcode

```

"<tagname>": "#00FF00"

```

For more information, please refer to the official [Rofi documentation](https://davatorium.github.io/rofi/current/rofi-dmenu.5/) or the [Pango documentation](https://docs.gtk.org/Pango/pango_markup.html).

### Tools

This list contains a (non-exhaustive) list of template-specific tools:

- [uuid](https://pkg.kali.org/pkg/ossp-uuid)

## Template Authoring

PRofi uses **Jinja2** for template processing, enabling dynamic content with variables, includes, and custom filters.

### Basic Template Structure

```yaml
metadata:
  filename: "example.yaml"
  tags: ["available_tags"]
  created: "2025-03-29"
  author: "Your Name"

content: |
  Your payload with {{ variables }}
```

### Variables

Access configuration values from `~/.config/profi/config.yaml`:

```jinja2
{{ attacker_ip }}           # Auto-detected or from OP_ATTACKER_IP
{{ shell_port }}            # Default: 4444
{{ delivery_outbound_port}} # Default: 8086
{{ tools_dir }}             # Tools directory
{{ delivery_path_windows }} # C:\Windows\Temp
```

### Template Inclusion

Compose complex payloads by including other templates:

```jinja2
{{ include('payloads/revshell-linux.yaml') }}

# With encoding
{{ include('payloads/revshell-powershell.yaml') | base64_pwsh }}
```

### Custom Filters

Specialized encoding for security testing:

- `url_encode` - URL encoding
- `base64` - Standard base64
- `base64_pwsh` - PowerShell compatible (UTF-16 LE)
- `hex_encode` - Hexadecimal encoding

Example:

```jinja2
powershell.exe -EncodedCommand {{ include('payloads/cmd.yaml') | base64_pwsh }}
```

### Raw Content

For content with Jinja2-like syntax that should not be processed:

```yaml
content: |
  {% raw %}PS1='\[\033[0m\][\D{%F %T}]\$ '{% endraw %}
```

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
