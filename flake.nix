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


        upload = pkgs.writeShellScriptBin "upload" ''
          mpremote cp -r ./micropython/src/ :
        '';

        run = pkgs.writeShellScriptBin "run" ''
          mpremote run ./micropython/src/main.py
        '';

        flash = pkgs.writeShellScriptBin "flash" ''
          mpremote cp -r ./micropython/* :
        '';
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            # helper scripts
            upload
            run
            flash

            mpremote
            mosquitto # mqtt broker
          ];
        };
      }
    );
}
