{
  description = "profi Flake";

  inputs = {
    # Nixpkgs / NixOS version to use.
    nixpkgs.url = "github:nixos/nixpkgs/nixpkgs-unstable";

    mimikatz.url = "file+https://github.com/gentilkiwi/mimikatz/releases/download/2.2.0-20220919/mimikatz_trunk.zip";
    mimikatz.flake = false;

    invoke-mimikatz.url = "github:PluggeRo/Invoke-Mimikatz";
    invoke-mimikatz.flake = false;

    sysinternals.url = "file+https://download.sysinternals.com/files/SysinternalsSuite.zip";
    sysinternals.flake = false;

    chisel-windows.url = "https://github.com/jpillora/chisel/releases/download/v1.10.1/chisel_1.10.1_windows_amd64.gz";
    chisel-windows.flake = false;

    # This is already in nixpkgs as pkgs.chisel
    chisel-linux.url = "https://github.com/jpillora/chisel/releases/download/v1.10.1/chisel_1.10.1_linux_amd64.gz";
    chisel-linux.flake = false;

    ghostpack.url = "github:r3motecontrol/Ghostpack-CompiledBinaries";
    ghostpack.flake = false;

    pspy.url = "https://github.com/DominicBreuker/pspy/releases/download/v1.2.1/pspy64";
    pspy.flake = false;

    ligolo-ng-agent-windows.url = "file+https://github.com/nicocha30/ligolo-ng/releases/download/v0.8.2/ligolo-ng_agent_0.8.2_windows_amd64.zip";
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

    payloadAllTheThings.url = "file+https://github.com/swisskyrepo/PayloadsAllTheThings/archive/refs/tags/4.1.zip";
    payloadAllTheThings.flake = false;

    ysoserial-net.url = "file+https://github.com/pwntester/ysoserial.net/releases/download/v1.36/ysoserial-1dba9c4416ba6e79b6b262b758fa75e2ee9008e9.zip";
    ysoserial-net.flake = false;
  };

  outputs =
    { self, nixpkgs, ... }@inputs:
    let

      # to work with older version of flakes
      lastModifiedDate = self.lastModifiedDate or self.lastModified or "19700101";

      # Generate a user-friendly version number.
      version = builtins.substring 0 8 lastModifiedDate;

      # System types to support.
      supportedSystems = [
        "x86_64-linux"
        "x86_64-darwin"
        "aarch64-linux"
        "aarch64-darwin"
      ];

      # Helper function to generate an attrset '{ x86_64-linux = f "x86_64-linux"; ... }'.
      forAllSystems = nixpkgs.lib.genAttrs supportedSystems;

      # Nixpkgs instantiated for supported system types.
      nixpkgsFor = forAllSystems (system: import nixpkgs { inherit system; });

    in
    {

      # Provide some binary packages for selected system types.
      packages = forAllSystems (
        system:
        let
          pkgs = nixpkgsFor.${system};

          templatesDir = ./src/profi/templates;

          # Mapping of tools to copy in the form of `destination = source`. The
          # destination is a path relative to the XDG_TOOLS_DIR, the source can
          # be anything where we can copy from e.g. a flake input, a zip or a
          # local file.
          # Each entry will be copied during the installPhase.
          external-tools = with inputs; {

            "bloodhound/SharpHound.ps1" =
              "${pkgs.bloodhound}/lib/BloodHound/resources/app/Collectors/SharpHound.ps1";
            "bloodhound/SharpHound.exe" =
              "${pkgs.bloodhound}/lib/BloodHound/resources/app/Collectors/SharpHound.exe";

            "Invoke-Mimikatz.ps1" = "${invoke-mimikatz}/Invoke-Mimikatz.ps1";
            "chisel/chisel_windows_amd64.gz" = "${chisel-windows}";
            "chisel/chisel_linux_amd64.gz" = "${pkgs.chisel}/bin/chisel";

            "ghostpack/rubeus.exe" = "${ghostpack}/Rubeus.exe";
            "ghostpack/certify.exe" = "${ghostpack}/Certify.exe";
            "ghostpack/seatbelt.exe" = "${ghostpack}/Seatbelt.exe";
            "pspy/pspy64" = "${pspy}";

            # Workaround for https://github.com/NixOS/nix/issues/7083
            "ligolo-ng/proxy/linux" = pkgs.fetchzip {
              url = "https://github.com/nicocha30/ligolo-ng/releases/download/v0.7.5/ligolo-ng_proxy_0.7.5_linux_amd64.tar.gz";
              sha256 = "sha256-YfX6DFbDe9PtZnVEKAyS2PFEkjjPxl+8nUYb40HJLak=";
              stripRoot = false;
            };
            # "ligolo-ng/proxy/linux" = "${ligolo-ng-proxy-linux}";

            "printspoofer/PrintSpoofer64.exe" = "${printspoofer64}";
            "printspoofer/PrintSpoofer32.exe" = "${printspoofer32}";
            "vshadow/Invoke-vshadow.ps1" = "${invoke-vshadow}";
            "godpotato/GodPotato-NET4.exe" = "${godpotato}";
            "uacbypass/Invoke-EventViewer.ps1" = "${invoke-eventviewer}";
            "powershell/spray-passwords.ps1" = templatesDir + /helper_scripts/spray-passwords.ps1;
            "nmap/nmapServicesToNote.py" = templatesDir + /helper_scripts/nmapServicesToNote.py;
            "nmap/nmapServicesToOrg.py" = templatesDir + /helper_scripts/nmapServicesToOrg.py;
            "icebreaker/icebreakerServicesToNoteMd.py" =
              templatesDir + /helper_scripts/icebreakerServicesToNoteMd.py;
            "postman/postmanEndpointsToNote.py" = templatesDir + /helper_scripts/postmanEndpointsToNote.py;
            "wsdl/wsdlEndpointsToNote.py" = templatesDir + /helper_scripts/wsdlEndpointsToNote.py;
            "openapi/openapiEndpointsToNote.py" = templatesDir + /helper_scripts/openapiEndpointsToNote.py;
            "certificate/createFakeCertificate.py" = templatesDir + /helper_scripts/createFakeCertificate.py;
            "phpserver/upload.php" = templatesDir + /helper_scripts/upload.php;
          };

        in
        {

          profi =
            with pkgs;
            python3Packages.buildPythonApplication {
              pname = "profi";
              version = "1.1.0";
              format = "pyproject";

              src = ./.;

              nativeBuildInputs = with python3Packages; [
                setuptools

                unzip
                pkgs.installShellFiles
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
                python
                pyyaml
                click
              ];

              preFixup =
                let
                  outToolsDir = "$out/share/tools";
                  outTemplatesDir = "$out/share/templates";
                in
                ''
                  # Create directory for templates
                  mkdir -p ${outTemplatesDir}
                  cp -r ${templatesDir}/* ${outTemplatesDir}

                  # Create directory for external tools
                  mkdir -p ${outToolsDir}
                ''
                + builtins.concatStringsSep "\n" (
                  lib.mapAttrsToList (destination: source: ''
                    mkdir -p `dirname "${outToolsDir}/${destination}"`
                    cp -r -v '${source}' "${outToolsDir}/${destination}"
                  '') external-tools
                )
                + '''';

              postUnpack =
                let
                  outToolsDir = "$out/share/tools";
                in
                ''
                  mkdir -p "${outToolsDir}/mimikatz"
                  unzip ${inputs.mimikatz} -d ${outToolsDir}/mimikatz

                  mkdir -p "${outToolsDir}/sysinternals"
                  unzip ${inputs.sysinternals} -d ${outToolsDir}/sysinternals

                  mkdir -p "${outToolsDir}/payloadAllTheThings"
                  unzip ${inputs.payloadAllTheThings} -d ${outToolsDir}/payloadAllTheThings

                  mkdir -p "${outToolsDir}/ysoserial-net"
                  cp ${inputs.ysoserial-net} ${outToolsDir}/ysoserial-net/Release.zip

                  mkdir -p "${outToolsDir}/ligolo-ng/agent/windows"
                  unzip ${inputs.ligolo-ng-agent-windows} -d ${outToolsDir}/ligolo-ng/agent/windows

                  mkdir -p "${outToolsDir}/ligolo-ng/agent/wintun"
                  unzip ${inputs.ligolo-ng-agent-wintun} -d ${outToolsDir}/ligolo-ng/agent/wintun
                '';
              postInstall = ''
                export HOME=$(pwd)

                #installShellCompletion --cmd profi \
                #--bash <(_PROFI_COMPLETE=bash_source $out/bin/profi) \
                #--fish <(_PROFI_COMPLETE=fish_source $out/bin/profi) \
              '';
            };

          profi-script =
            with pkgs;
            stdenv.mkDerivation rec {
              pname = "profi";
              inherit version;
              src = ./.;

              nativeBuildInputs = [ makeWrapper ];

              installPhase =
                let
                  outToolsDir = "$out/share/tools";
                  outTemplatesDir = "$out/share/templates";
                in
                ''
                  # Install the main script
                  mkdir -p $out/bin
                  cp script.sh $out/bin/profi
                  chmod +x $out/bin/profi

                  # Create directory for external tools
                  mkdir -p ${outToolsDir}

                  mkdir -p ${outTemplatesDir}

                  cp -r ${templatesDir}/* ${outTemplatesDir}
                ''
                + builtins.concatStringsSep "\n" (
                  lib.mapAttrsToList (destination: source: ''
                    mkdir -p `dirname "${outToolsDir}/${destination}"`
                    cp -r -v '${source}' "${outToolsDir}/${destination}"
                  '') external-tools
                )
                + ''
                  # Wrap the script:
                  # - PATH is set to dependencies
                  # - XDG_TOOLS_DIR to our directory with external tools

                  wrapProgram $out/bin/profi \
                  --prefix PATH : ${lib.makeBinPath buildInputs} \
                  --set XDG_TOOLS_DIR "$out/share/tools"
                '';

              meta = {
                # Specify the default binary to run on `nix run`
                mainProgram = "profi";
                description = "Rofi-based tool render common security related templates to clipboard";
                # platforms = platforms.linux;
              };
            };

        }
      );

      homeManagerModules.profi = import ./hm.nix self;

      # The default package for `nix build` and `nix run`. Use `nix flake show`
      # to inspect the contents or look inside `result` after building
      defaultPackage = forAllSystems (system: self.packages.${system}.profi);
    };
}
