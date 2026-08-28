{
  description = "Reproducible engineering environment for filament-recycler";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" ];
      forAllSystems = nixpkgs.lib.genAttrs systems;
    in {
      devShells = forAllSystems (system:
        let
          pkgs = import nixpkgs { inherit system; };
          openmodelica-omc = if system == "x86_64-linux"
            then pkgs.callPackage ./nix/openmodelica.nix { }
            else null;
        in {
          default = pkgs.mkShell {
            packages = (with pkgs; [
              freecad
              gmsh
              calculix-ccx
              prusa-slicer
              typst
              python3
              git-lfs
            ]) ++ pkgs.lib.optionals (openmodelica-omc != null) [ openmodelica-omc ];
            shellHook = ''
              export FILAMENT_RECYCLER_ROOT="$PWD"
              echo "filament-recycler engineering shell"
            '';
          };
        });
    };
}
