{ lib
, stdenv
, fetchurl
, dpkg
, autoPatchelfHook
, makeWrapper
, unzip
, blas
, lapack
, curl
, expat
, libuuid
, omniorb
, gcc
, gfortran
, zlib
}:

stdenv.mkDerivation (finalAttrs: {
  pname = "openmodelica-omc";
  version = "1.27.0-5-ga0783c0";

  srcs = [
    (fetchurl {
      url = "https://build.openmodelica.org/apt/pool/contrib-noble/omc-common_1.27.0~5-ga0783c0-1_all.deb";
      sha256 = "4c44f18309d93f17af13235de13b75ce61f0f69281214ef6eba64cd675ed1f6d";
    })
    (fetchurl {
      url = "https://build.openmodelica.org/apt/pool/contrib-noble/libomcsimulation_1.27.0~5-ga0783c0-1_amd64.deb";
      sha256 = "0a8cc7ffebacae8d9f9e2f4e7090b2eddc7689414511f6245cb6f7a0c80ce0a8";
    })
    (fetchurl {
      url = "https://build.openmodelica.org/apt/pool/contrib-noble/libomc_1.27.0~5-ga0783c0-1_amd64.deb";
      sha256 = "fb0f8e279502cb4d81ff32c0b9084a18adebd1a3f5dfcbe34dd8ebb37b0bbc59";
    })
    (fetchurl {
      url = "https://build.openmodelica.org/apt/pool/contrib-noble/omc_1.27.0~5-ga0783c0-1_amd64.deb";
      sha256 = "4cbe79779ff652e3ee18bc6b20cd51191c3d430178a5f5d6db0e613d756ab849";
    })
    (fetchurl {
      url = "https://build.openmodelica.org/apt/pool/contrib-noble/omlibrary_1.27.0~5-ga0783c0-1_all.deb";
      sha256 = "fa13b0f8df1c67c20366fe6022ab605cd6950e93536b3dd750818ec9eb391898";
    })
  ];

  nativeBuildInputs = [ dpkg autoPatchelfHook makeWrapper unzip ];
  buildInputs = [ blas lapack curl expat libuuid omniorb gcc.cc.lib gfortran.cc.lib zlib ];

  dontConfigure = true;
  dontBuild = true;
  unpackPhase = ''
    runHook preUnpack
    mkdir unpacked
    for archive in $srcs; do
      dpkg-deb -x "$archive" unpacked
    done
    runHook postUnpack
  '';

  installPhase = ''
    runHook preInstall
    mkdir -p "$out"
    cp -a unpacked/usr/. "$out/"
    # The Debian omlibrary package carries the exact MSL archives as an
    # offline cache.  Materialize MSL 4.0.0 inside the immutable output so a
    # headless build never writes to ~/.openmodelica or downloads libraries.
    mkdir msl
    unzip -q "$out/share/omlibrary/cache/96032134c36668898e1693e69bd9f81aa38de3dd.zip" -d msl
    msl_root="$(find msl -mindepth 1 -maxdepth 1 -type d | head -n 1)"
    mkdir -p "$out/share/omlibrary/libraries/Modelica 4.0.0"
    cp -a "$msl_root/Modelica/." "$out/share/omlibrary/libraries/Modelica 4.0.0/"
    for library_name in Complex ModelicaServices ModelicaReference; do
      mkdir -p "$out/share/omlibrary/libraries/$library_name 4.0.0"
      if [ -d "$msl_root/$library_name" ]; then
        cp -a "$msl_root/$library_name/." "$out/share/omlibrary/libraries/$library_name 4.0.0/"
      else
        cp "$msl_root/$library_name.mo" "$out/share/omlibrary/libraries/$library_name 4.0.0/package.mo"
      fi
    done
    wrapProgram "$out/bin/omc" \
      --set OPENMODELICAHOME "$out" \
      --set-default OPENMODELICALIBRARY "$out/share/omlibrary/libraries" \
      --prefix LIBRARY_PATH : "${blas}/lib:${lapack}/lib"
    runHook postInstall
  '';

  meta = {
    description = "OpenModelica compiler pinned for the recycler digital baseline";
    homepage = "https://openmodelica.org/";
    license = lib.licenses.gpl3Plus;
    platforms = [ "x86_64-linux" ];
  };
})
