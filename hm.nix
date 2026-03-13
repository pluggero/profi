self:
{
  config,
  lib,
  pkgs,
  ...
}:

with lib;

let
  inherit (pkgs.stdenv.hostPlatform) system;
  profi = self.packages.${system}.profi;
  cfg = config.profi;

  defaultSettings = {
    attacker_interface = "tun0";
    attacker_ip = "";
    delivery_inbound_port = 8085;
    delivery_outbound_port = 8086;
    delivery_path_linux = "/dev/shm";
    delivery_path_windows = "C:\\Windows\\Temp";
    delivery_dir_listing = false;
    proxy_port = 8087;
    shell_port = 4444;
    webdav_port = 80;
  };

in
{

  options.profi = {
    enable = mkEnableOption "profi";

    yamlSettings = {
      tools_dir = mkOption {
        type = types.str;
        default = "${profi}/share/tools";
        example = "${config.xdg.dataHome}/profi/tools";
        description = "Directory containing external tools used by profi";
      };

      templates_dir = mkOption {
        type = types.str;
        default = "${profi}/share/templates";
        example = "${config.xdg.dataHome}/profi/templates";
        description = "Directory containing templates used by profi";
      };

      copy_command = mkOption {
        type = types.str;
        default = "xclip -selection clipboard";
        example = "wl-copy";
        description = "Command to store generated output into clipboard";
      };
      settings = mkOption {
        type = types.submodule {
          options = {
            attacker_interface = mkOption {
              type = types.str;
              default = defaultSettings.attacker_interface;
              description = "Attacker's network interface";
            };
            attacker_ip = mkOption {
              type = types.str;
              default = defaultSettings.attacker_ip;
              description = "Attacker's ip address";
            };
            delivery_inbound_port = mkOption {
              type = types.int;
              default = defaultSettings.delivery_inbound_port;
              description = "Port used for webservers designed to receive files from targetted machines";
            };
            delivery_outbound_port = mkOption {
              type = types.int;
              default = defaultSettings.delivery_outbound_port;
              description = "Port used for webservers designed to transfer files to targetted machines";
            };
            delivery_path_linux = mkOption {
              type = types.str;
              default = defaultSettings.delivery_path_linux;
              description = "Path used to place transferred payloads on linux targets";
            };
            delivery_path_windows = mkOption {
              type = types.str;
              default = defaultSettings.delivery_path_windows;
              description = "Path used to place transferred payloads on windows targets";
            };
            delivery_dir_listing = mkOption {
              type = types.bool;
              default = defaultSettings.delivery_dir_listing;
              description = "Whether to enable directory listing for the delivery webserver";
            };
            proxy_port = mkOption {
              type = types.int;
              default = defaultSettings.proxy_port;
              description = "Port used for proxy servers";
            };
            shell_port = mkOption {
              type = types.int;
              default = defaultSettings.shell_port;
              description = "Port used for catching reverse shells";
            };
            webdav_port = mkOption {
              type = types.int;
              default = defaultSettings.webdav_port;
              description = "Port used for webdav servers";
            };
            c2_settings = mkOption {
              type = types.submodule {
                options = {
                  mythic_url = mkOption {
                    type = types.str;
                    default = "https://127.0.0.1:7443";
                    description = "Mythic C2 server URL";
                  };
                  mythic_api_token = mkOption {
                    type = types.str;
                    default = "";
                    description = "Mythic API authentication token";
                  };
                  mythic_callback_url = mkOption {
                    type = types.str;
                    default = "http://127.0.0.1";
                    description = "C2 callback server URL (can differ from mythic_url)";
                  };
                  mythic_callback_port = mkOption {
                    type = types.str;
                    default = "80";
                    description = "C2 callback port";
                  };
                  mythic_callback_interval = mkOption {
                    type = types.str;
                    default = "5";
                    description = "Callback interval in seconds";
                  };
                  mythic_callback_jitter = mkOption {
                    type = types.str;
                    default = "23";
                    description = "Callback jitter percentage";
                  };
                  mythic_killdate = mkOption {
                    type = types.str;
                    default = "2027-12-31";
                    description = "Payload kill date in YYYY-MM-DD format";
                  };
                  mythic_payload_commands = mkOption {
                    type = types.listOf types.str;
                    default = ["all"];
                    description = "List of commands to include in payload";
                  };
                };
              };
              default = { };
              description = "C2 framework settings";
            };
          };
        };
        default = defaultSettings;
      };
      colors = mkOption {
        type = types.submodule {
          options = {
            web = mkOption {
              type = types.str;
              default = "cyan";
              description = "Color for web-related text.";
            };
            api = mkOption {
              type = types.str;
              default = "teal";
              description = "Color for api-related text.";
            };
            system = mkOption {
              type = types.str;
              default = "orange";
              description = "Color for system-related text.";
            };
            shell = mkOption {
              type = types.str;
              default = "red";
              description = "Color for shell-related text.";
            };
            linux = mkOption {
              type = types.str;
              default = "yellow";
              description = "Color for linux-related text.";
            };
            windows = mkOption {
              type = types.str;
              default = "lightblue";
              description = "Color for windows-related text.";
            };
            domain = mkOption {
              type = types.str;
              default = "blue";
              description = "Color for domain-related text.";
            };
            mobile = mkOption {
              type = types.str;
              default = "green";
              description = "Color for mobile-related text.";
            };
            cracking = mkOption {
              type = types.str;
              default = "purple";
              description = "Color for cracking-related text.";
            };
            privesc = mkOption {
              type = types.str;
              default = "pink";
              description = "Color for privesc-related text.";
            };
            proxy = mkOption {
              type = types.str;
              default = "gray";
              description = "Color for proxy-related text.";
            };
            wordlist = mkOption {
              type = types.str;
              default = "black";
              description = "Color for wordlist-related text.";
            };
            utils = mkOption {
              type = types.str;
              default = "tomato";
              description = "Color for utils-related text.";
            };
            enum = mkOption {
              type = types.str;
              default = "tan";
              description = "Color for enum-related text.";
            };
            xss = mkOption {
              type = types.str;
              default = "plum";
              description = "Color for xss-related text.";
            };
            c2 = mkOption {
              type = types.str;
              default = "magenta";
              description = "Color for c2-related text.";
            };
          };
        };
        default = { };
        description = "Color settings for profi output";
      };
    };
  };

  config = mkIf cfg.enable {
    home.packages = [
      profi
    ];
    xdg.configFile."profi/config.yaml" = {
      text = builtins.toJSON cfg.yamlSettings;
    };
  };
}
