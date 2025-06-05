{ pkgs ? import <nixpkgs> {
    config = {
      allowUnfree = true;
    };
  }
}:

pkgs.mkShell {
  packages = with pkgs; [ 
    postgresql_17
    python312Full
  ];
  shellHook = ''
    export LD_LIBRARY_PATH=${pkgs.lib.makeLibraryPath [
      pkgs.stdenv.cc.cc
    ]}
    
    # Create a local socket directory for PostgreSQL
    mkdir -p $PWD/pg_socket
    export PGHOST=$PWD/pg_socket
    export PGDATA=$PWD/pgdata
    export PGPORT=5432

    # Add PostgreSQL binaries to PATH
    export PATH="${pkgs.postgresql_17}/bin:$PATH"
  '';
}
