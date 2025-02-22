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

        upload = pkgs.writeShellScriptBin "upload" ''
          mkdir -p ./micropython/.temp
          mkdir -p ./micropython/.temp/config

          cat ./micropython/config/config.json | jq -c > ./micropython/.temp/config/config.json
          cat ./micropython/config/secrets.json | jq -c > ./micropython/.temp/config/secrets.json

          python3 ./micropython/dev_utils/clean.py ./micropython/user/ ./micropython/.temp/user
          python3 ./micropython/dev_utils/clean.py ./micropython/ssa ./micropython/.temp/ssa

          mpremote cp -r ./micropython/.temp/config/ :
          mpremote cp -r ./micropython/.temp/user/ :
          mpremote cp -r ./micropython/.temp/ssa/ :

          rm -rf ./micropython/.temp
        '';

        run = pkgs.writeShellScriptBin "run" ''
          mpremote run ./micropython/ssa/bootstrap.py
        '';

        flash = pkgs.writeShellScriptBin "flash" ''
          upload
          mpremote cp -r ./micropython/boot.py :
        '';

        nuke = pkgs.writeShellScriptBin "nuke" ''
          mpremote run ./micropython/dev_utils/nuke.py
        '';

        del_user = pkgs.writeShellScriptBin "del_user" ''
          mpremote rm :./user/app.py
          mpremote rmidr :./user
        '';
      in
      {
        devShells.default = pkgs.mkShell {
          shellHook = ''
            export PATH=$PATH:$(pwd)/api/node_modules/.bin
          '';
          buildInputs = with pkgs; [
            # helper scripts

            # temporarily open/close firewall for mqtt
            openfw
            closefw

            # micropython utils
            run
            nuke
            flash
            upload
            del_user

            jq # json cli parser

            mpremote # micropython remote tool
            mosquitto # mqtt broker

            # to install asyncapi cli
            nodejs_23
            # edge node development
            deno # dev tools and runtime

            doxygen # documentation generator

            # For clean.py script
            python312Packages.astor
          ];
        };
      }
    );
}
