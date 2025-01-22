{
  description = "OSCPasting Flake";

  inputs = {
    # Nixpkgs / NixOS version to use.
    nixpkgs.url = "github:nixos/nixpkgs/nixpkgs-unstable";

    mimikatz.url = "file+https://github.com/gentilkiwi/mimikatz/releases/download/2.2.0-20220919/mimikatz_trunk.zip";
    mimikatz.flake = false;

    invoke-mimikatz.url = "github:PluggeRo/Invoke-Mimikatz";
    invoke-mimikatz.flake = false;

    sysinternals.url = "file+https://download.sysinternals.com/files/SysinternalsSuite.zip";
    sysinternals.flake = false;

    chisel-windows.url = "https://github.com/jpillora/chisel/releases/download/v1.9.1/chisel_1.9.1_windows_amd64.gz";
    chisel-windows.flake = false;

    # This is already in nixpkgs as pkgs.chisel
    chisel-linux.url = "https://github.com/jpillora/chisel/releases/download/v1.9.1/chisel_1.9.1_linux_amd64.gz";
    chisel-linux.flake = false;

    ghostpack.url = "github:r3motecontrol/Ghostpack-CompiledBinaries";
    ghostpack.flake = false;

    pspy.url = "https://github.com/DominicBreuker/pspy/releases/download/v1.2.1/pspy64";
    pspy.flake = false;

    ligolo-ng-agent-windows.url = "file+https://github.com/nicocha30/ligolo-ng/releases/download/v0.6.2/ligolo-ng_agent_0.6.2_windows_amd64.zip";
    ligolo-ng-agent-windows.flake = false;

    # Broken due to being tar.gz => need to fix in postUnpackPhase
    # ligolo-ng-proxy-linux.url = "https://github.com/nicocha30/ligolo-ng/releases/download/v0.6.2/ligolo-ng_proxy_0.6.2_linux_amd64.tar.gz";
    # ligolo-ng-proxy-linux.flake = false;

    ligolo-ng-agent-wintun.url = "file+https://www.wintun.net/builds/wintun-0.14.1.zip";
    ligolo-ng-agent-wintun.flake = false;

    printspoofer64.url = "https://github.com/itm4n/PrintSpoofer/releases/download/v1.0/PrintSpoofer64.exe";
    printspoofer64.flake = false;

    printspoofer32.url = "https://github.com/itm4n/PrintSpoofer/releases/download/v1.0/PrintSpoofer32.exe";
    printspoofer32.flake = false;

    invoke-vshadow.url = "github:PluggeRo/Invoke-vshadow";
    invoke-vshadow.flake = false;

    godpotato.url = "https://github.com/BeichenDream/GodPotato/releases/download/V1.20/GodPotato-NET4.exe";
    godpotato.flake = false;

    invoke-eventviewer.url = "https://raw.githubusercontent.com/CsEnox/EventViewer-UACBypass/main/Invoke-EventViewer.ps1";
    invoke-eventviewer.flake = false;

    payloadAllTheThings.url = "file+https://github.com/swisskyrepo/PayloadsAllTheThings/archive/refs/tags/3.0.zip";
    payloadAllTheThings.flake = false;
  };

  outputs = { self, nixpkgs, ... }@inputs:
    let

      # to work with older version of flakes
      lastModifiedDate = self.lastModifiedDate or self.lastModified or "19700101";

      # Generate a user-friendly version number.
      version = builtins.substring 0 8 lastModifiedDate;

      # System types to support.
      supportedSystems = [ "x86_64-linux" "x86_64-darwin" "aarch64-linux" "aarch64-darwin" ];

      # Helper function to generate an attrset '{ x86_64-linux = f "x86_64-linux"; ... }'.
      forAllSystems = nixpkgs.lib.genAttrs supportedSystems;

      # Nixpkgs instantiated for supported system types.
      nixpkgsFor = forAllSystems (system: import nixpkgs { inherit system; });

    in
    {

      # Provide some binary packages for selected system types.
      packages = forAllSystems (system:
        let
          pkgs = nixpkgsFor.${system};

          # Mapping of tools to copy in the form of `destination = source`. The
          # destination is a path relative to the XDG_TOOLS_DIR, the source can
          # be anything where we can copy from e.g. a flake input, a zip or a
          # local file.
          # Each entry will be copied during the installPhase.
          external-tools = with inputs; {

            "bloodhound/SharpHound.ps1" = "${pkgs.bloodhound}/lib/BloodHound/resources/app/Collectors/SharpHound.ps1";
            "bloodhound/SharpHound.exe" = "${pkgs.bloodhound}/lib/BloodHound/resources/app/Collectors/SharpHound.exe";

            "Invoke-Mimikatz.ps1" = "${invoke-mimikatz}/Invoke-Mimikatz.ps1";
            "chisel/chisel_windows_amd64.gz" = "${chisel-windows}";
            "chisel/chisel_linux_amd64.gz" = "${pkgs.chisel}/bin/chisel";

            "ghostpack/rubeus.exe" = "${ghostpack}/Rubeus.exe";
            "ghostpack/certify.exe" = "${ghostpack}/Certify.exe";
            "ghostpack/seatbelt.exe" = "${ghostpack}/Seatbelt.exe";
            "pspy/pspy64" = "${pspy}";

            # Workaround for https://github.com/NixOS/nix/issues/7083
            "ligolo-ng/proxy/linux" = pkgs.fetchzip {
              url = "https://github.com/nicocha30/ligolo-ng/releases/download/v0.6.2/ligolo-ng_proxy_0.6.2_linux_amd64.tar.gz";
              sha256 = "sha256-QSDmGfkLGnDF3K9JQEOWUoXigFsD/CBhk3eXsjpvYzw=";
              stripRoot = false;
            };
            # "ligolo-ng/proxy/linux" = "${ligolo-ng-proxy-linux}";

            "printspoofer/PrintSpoofer64.exe" = "${printspoofer64}";
            "printspoofer/PrintSpoofer32.exe" = "${printspoofer32}";
            "vshadow/Invoke-vshadow.ps1" = "${invoke-vshadow}";
            "godpotato/GodPotato-NET4.exe" = "${godpotato}";
            "uacbypass/Invoke-EventViewer.ps1" = "${invoke-eventviewer}";
            "powershell/spray-passwords.ps1" = ./templates/helper_scripts/spray-passwords.ps1;
            "nmap/nmapServicesToNote.py" = ./templates/helper_scripts/nmapServicesToNote.py;
            "nmap/nmapServicesToOrg.py" = ./templates/helper_scripts/nmapServicesToOrg.py;
            "icebreaker/icebreakerServicesToNoteMd.py" = ./templates/helper_scripts/icebreakerServicesToNoteMd.py;
            "postman/postmanEndpointsToNote.py" = ./templates/helper_scripts/postmanEndpointsToNote.py;
            "wsdl/wsdlEndpointsToNote.py" = ./templates/helper_scripts/wsdlEndpointsToNote.py;
            "openapi/openapiEndpointsToNote.py" = ./templates/helper_scripts/openapiEndpointsToNote.py;
            "certificate/createFakeCertificate.py" = ./templates/helper_scripts/createFakeCertificate.py;
            "phpserver/upload.php" = ./templates/helper_scripts/upload.php;
          };

        in
        {

          oscpasting = with pkgs; python3Packages.buildPythonApplication {
            pname = "oscpasting";
            version = "0.1";
            format = "pyproject";

            src = ./.;

            nativeBuildInputs = with python3Packages; [
              setuptools

              unzip
            ];

            propagatedBuildInputs = with python3Packages; [
              findutils
              esh
              rofi
              wl-clipboard # copy to clipboard on Wayland
              xclip # copy to clipboard on X
              perl
              unixtools.ifconfig
              libossp_uuid # For generating uuids
              num-utils # For random numbers
              python312
              pyyaml
            ];

            preFixup =
              let
                toolDir     = "$out/share/tools";
                templateDir = "$out/share/templates";
              in
              ''
                # Create directory for templates
                mkdir -p ${templateDir}
                cp -r templates/* ${templateDir}

                # Create directory for external tools
                mkdir -p ${toolDir}
              ''
              +
              builtins.concatStringsSep "\n" (
                lib.mapAttrsToList
                  (destination: source: ''
                    mkdir -p `dirname "${toolDir}/${destination}"`
                    cp -r -v '${source}' "${toolDir}/${destination}"
                  '')
                  external-tools) +
              ''
              '';

            postUnpack =
              let
                toolDir = "$out/share/tools";
              in
              ''
                mkdir -p `dirname "${toolDir}/mimikatz"`
                unzip ${inputs.mimikatz} -d ${toolDir}/mimikatz

                mkdir -p `dirname "${toolDir}/sysinternals"`
                unzip ${inputs.sysinternals} -d ${toolDir}/sysinternals

                mkdir -p `dirname "${toolDir}/payloadAllTheThings"`
                unzip ${inputs.payloadAllTheThings} -d ${toolDir}/payloadAllTheThings

                mkdir -p `dirname "${toolDir}/ligolo-ng/agent/windows"`
                unzip ${inputs.ligolo-ng-agent-windows} -d ${toolDir}/ligolo-ng/agent/windows

                mkdir -p `dirname "${toolDir}/ligolo-ng/agent/wintun"`
                unzip ${inputs.ligolo-ng-agent-wintun} -d ${toolDir}/ligolo-ng/agent/wintun
              '';
          };

          oscp-script = with pkgs; stdenv.mkDerivation rec {
            pname = "oscpasting";
            inherit version;
            src = ./.;

            buildInputs = [
              findutils
              esh
              rofi
              wl-clipboard # copy to clipboard on Wayland
              xclip # copy to clipboard on X
              perl
              unixtools.ifconfig
              libossp_uuid # For generating uuids
              num-utils # For random numbers
              python312
            ];

            nativeBuildInputs = [ makeWrapper ];

            installPhase =
              let
                toolDir     = "$out/share/tools";
                templateDir = "$out/share/templates";
              in
              ''
                # Install the main script
                mkdir -p $out/bin
                cp script.sh $out/bin/oscpasting
                chmod +x $out/bin/oscpasting

                # Create directory for external tools
                mkdir -p ${toolDir}

                mkdir -p ${templateDir}

                cp -r templates/* ${templateDir}
              ''
              +
              builtins.concatStringsSep "\n" (
                lib.mapAttrsToList
                  (destination: source: ''
                    mkdir -p `dirname "${toolDir}/${destination}"`
                    cp -r -v '${source}' "${toolDir}/${destination}"
                  '')
                  external-tools) +
              ''
                # Wrap the script:
                # - PATH is set to dependencies
                # - XDG_TOOLS_DIR to our directory with external tools

                wrapProgram $out/bin/oscpasting \
                --prefix PATH : ${lib.makeBinPath  buildInputs} \
                --set XDG_TOOLS_DIR "$out/share/tools"
              '';

            meta = {
              # Specify the default binary to run on `nix run`
              mainProgram = "oscpasting";
              description = "Rofi-based tool render common security related templates to clipboard";
              # platforms = platforms.linux;
            };
          };

        });

      homeManagerModules.OSCPasting = import ./hm.nix self;

      # The default package for `nix build` and `nix run`. Use `nix flake show`
      # to inspect the contents or look inside `result` after building
      defaultPackage = forAllSystems (system: self.packages.${system}.oscp-script);
    };
}
