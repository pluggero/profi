{
  lib,
  buildPythonPackage,
  fetchPypi,
  setuptools,
  pythonRelaxDepsHook,
  aiohttp,
  gql,
  pycryptodome,
}:

buildPythonPackage rec {
  pname = "mythic";
  version = "0.2.10";
  pyproject = true;

  src = fetchPypi {
    inherit pname version;
    hash = "sha256-Sj3xUIE1SVFnxvTmRbVoZ/IVsEuwPODweQnnsvGWnuQ=";
  };

  build-system = [ setuptools ];

  nativeBuildInputs = [ pythonRelaxDepsHook ];

  # gql is pinned to 3.5.3 but nixpkgs ships 4.x
  pythonRelaxDeps = [ "gql" ];
  # asyncio is in stdlib
  pythonRemoveDeps = [ "asyncio" ];

  dependencies = [
    aiohttp
    gql
    pycryptodome
  ];

  # Tests require a running Mythic C2 instance
  doCheck = false;

  meta = {
    description = "Python library for interacting with Mythic C2 Framework instances";
    homepage = "https://github.com/MythicMeta/Mythic_Scripting";
    maintainers = [ ];
  };
}
