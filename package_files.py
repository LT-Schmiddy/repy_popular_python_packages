import os
from pathlib import Path

root_dir = Path(__file__).parent

# Including individual files:
schema_src_dir = root_dir.joinpath("./extern/schema")
typing_extensions_src_dir = root_dir.joinpath("./extern/typing_extensions/src")
include_python_files: dict[Path, Path] = {
    # Including single files
    # Modules
    Path("schema.py"): schema_src_dir.joinpath("schema.py"),
    Path("typing_extensions.py"): typing_extensions_src_dir.joinpath("typing_extensions.py"),
}

include_suffixes = [".py", ".pem"]

# Including entire directories:
def populate_file_injection(injections: dict[Path, Path], inject_root: Path, search_dir: Path):
    for inject_path, file_path in [(inject_root.joinpath(i), search_dir.joinpath(i)) for i in os.listdir(search_dir)]:
        if file_path.is_file() and file_path.suffix in include_suffixes:
            injections[inject_path] = file_path
        elif file_path.is_dir():
            populate_file_injection(injections, inject_path, file_path)
     
pyyaml_src_dir = root_dir.joinpath("./extern/pyyaml/lib/yaml")
websockets_src_dir = root_dir.joinpath("./extern/websockets/src/websockets")
colorama_src_dir = root_dir.joinpath("./extern/colorama/colorama")
cerifi_src_dir = root_dir.joinpath("./extern/python-certifi/certifi")

populate_file_injection(include_python_files, Path("yaml"), pyyaml_src_dir)
populate_file_injection(include_python_files, Path("websockets"), websockets_src_dir)
populate_file_injection(include_python_files, Path("colorama"), colorama_src_dir)
populate_file_injection(include_python_files, Path("certifi"), cerifi_src_dir)
