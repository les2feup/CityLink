{
  description = "Micropython dev shell";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      nixpkgs,
      flake-utils,
      ...
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

        openfw = pkgs.writeShellScriptBin "openfw" ''
          sudo iptables -A INPUT -p tcp --dport 1883 -j ACCEPT
          sudo systemctl reload firewall
        '';

        closefw = pkgs.writeShellScriptBin "closefw" ''
          sudo iptables -D INPUT -p tcp --dport 1883 -j ACCEPT
          sudo systemctl reload firewall
        '';

        run = pkgs.writeShellScriptBin "run" ''
          mpremote run ./ssaHAL/boot.py
        '';

        flash = pkgs.writeShellScriptBin "flash" ''
          ${builtins.readFile ./scripts/flash.sh}
        '';

        fw2json = pkgs.writeShellScriptBin "fw2json" ''
          ${builtins.readFile ./scripts/fw2json.sh}
        '';
      in
      {
        devShells.default = pkgs.mkShell {
          shellHook = ''
            export PATH=$PATH:$(pwd)/api/node_modules/.bin
          '';

          nativeBuildInputs = with pkgs; [
            # helper scripts

            # temporarily open/close firewall for mqtt
            openfw
            closefw

            # micropython development
            run
            flash
            fw2json

            jq # json cli parser
            rsbkb # for crc32 package

            nodePackages_latest.prettier # code formatter
            black # python code formatter

            mpremote # micropython remote tool
            micropython # micropython runtime and cross compiler
            mosquitto # mqtt broker

            # edge node development
            deno # dev tools and runtime

            doxygen # documentation generator
            plantuml # uml diagram generator

            python312Packages.astor # For clean.py script
            python312Packages.typing-extensions
          ];
        };
      }
    );
}
