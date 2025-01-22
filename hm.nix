self: { config, lib, pkgs, ... }:

with lib;

let
  inherit (pkgs.stdenv.hostPlatform) system;
  oscpasting = self.packages.${system}.oscpasting;
  cfg = config.OSCPasting;

  defaultSettings = {
    attacker_interface = "tun0";
    attacker_ip = "";
    delivery_inbound_port = 8085;
    delivery_outbound_port = 8086;
    delivery_path_linux = "/dev/shm";
    delivery_path_windows = "C:\\Windows\\Temp";
    proxy_port = 8087;
    shell_port = 4444;
    webdav_port = 80;
  };

in {

    options.OSCPasting = {
      enable = mkEnableOption "OSCPasting";

      yamlSettings = {
        tools_dir = mkOption {
          type = types.str;
          default = "${oscpasting}/share/tools";
          example = "${config.xdg.dataHome}/oscpasting/tools";
          description = "Directory containing external tools used by OSCPasting";
        };

        templates_dir = mkOption {
          type = types.str;
          default = "${oscpasting}/share/templates";
          example = "${config.xdg.dataHome}/oscpasting/templates";
          description = "Directory containing templates used by OSCPasting";
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
            };
          };
          default = defaultSettings;
        };
      };
    };

    config = mkIf cfg.enable {
        home.packages = [
          oscpasting
        ];
        xdg.configFile."oscpasting/config.yaml" = {
          text = builtins.toJSON cfg.yamlSettings;
        };
    };
}
