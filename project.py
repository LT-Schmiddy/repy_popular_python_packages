import platform, shutil, enum, os, subprocess
from pathlib import Path
from modbuildcore.jobs import *
from modbuildcore.job_base import JobBase
import toml

root_dir: Path = Path(__file__).parent

archive_downloads_dir: Path = root_dir.joinpath("downloads")
build_dir: Path = root_dir.joinpath("build")
binaries_dir: Path = root_dir.joinpath("binaries")

mod_build_dir = build_dir.joinpath("mod")
tests_build_dir = build_dir.joinpath("tests")

package_dir = root_dir.joinpath("thunderstore_packages")

make_mips_compiler_path: Path = None
make_mips_linker_path: Path = None
mod_tool_path: Path = None
zig_dir_path: Path = None
llvm_path: Path = None

downloads: dict[str, DownloadJob] = {}
archive_extractions: dict[str, ArchiveExtractJob] = {}
makefiles: dict[str, MakefileJob] = {}
tomls: dict[str, GenerateTomlJob] = {}
nrms: dict[str, ModToNRMJob] = {}
cmake_build_groups: dict[str, dict[str, CMakeBuildJob]] = {}
build_outputs: dict[str, BuildOutputJob] = {}
thunderstore_packages: dict[str, ThunderstorePackageJob] = {}

project_name = "REPY_PopularPythonPackages"
project_tests_name = "Test_" + project_name
project_version_string = "1.0.0"

mod_elf_path = mod_build_dir.joinpath("mod.elf")
tests_elf_path = tests_build_dir.joinpath("tests.elf")

repy_api_src = root_dir.joinpath("./src/repy_api") # The repy_api module

mm_toml_data = {
    "manifest": {
        "game_id": "mm",
        "minimum_recomp_version": "1.2.1"
    },
    "inputs": {
        "func_reference_syms_file": str(root_dir.joinpath("./syms/Zelda64RecompSyms/mm.us.rev1.syms.toml")),
        "data_reference_syms_files": [ 
            str(root_dir.joinpath("./syms/Zelda64RecompSyms/mm.us.rev1.datasyms.toml")),
            str(root_dir.joinpath("./syms/Zelda64RecompSyms/mm.us.rev1.datasyms_static.toml")),
        ]
    }
}

bk_toml_data = {
    "manifest": {
        "game_id": "bk",
        "minimum_recomp_version": "0.0.1"
    },
    "inputs": {
        "func_reference_syms_file": str(root_dir.joinpath("./syms/BanjoRecompSyms/bk.us.rev0.syms.toml")),
        "data_reference_syms_files": [ 
            str(root_dir.joinpath("./syms/BanjoRecompSyms/bk.us.rev0.datasyms.toml"))
        ]
    }
}

sf64_toml_data = {
    "manifest": {
        "game_id": "sf64",
        "minimum_recomp_version": "1.0.0"
    },
    "inputs": {
        "func_reference_syms_file": str(root_dir.joinpath("./syms/Starfox64RecompSyms/sf64.us.rev1.syms.toml")),
        "data_reference_syms_files": [ 
            str(root_dir.joinpath("./syms/Starfox64RecompSyms/sf64.us.rev1.datasyms.toml"))
        ]
    }
}

mk64_toml_data = {
    "manifest": {
        "game_id": "mk64",
        "minimum_recomp_version": "0.0.9"
    },
    "inputs": {
        "func_reference_syms_file": str(root_dir.joinpath("./syms/MarioKart64RecompSyms/mk64.us.syms.toml")),
        "data_reference_syms_files": [ 
            str(root_dir.joinpath("./syms/MarioKart64RecompSyms/mk64.us.datasyms.toml"))
        ]
    }
}

mnsg_toml_data = {
    "manifest": {
        "game_id": "mnsg",
        "minimum_recomp_version": "0.1.0"
    },
    "inputs": {
        "func_reference_syms_file": str(root_dir.joinpath("./syms/Goemon64RecompSyms/mnsg.syms.toml")),
        "data_reference_syms_files": [ 
            str(root_dir.joinpath("./syms/Goemon64RecompSyms/mnsg.datasyms.toml"))
        ]
    }
}


mod_toml_data = {
    "manifest": {
        "id": project_name,
        "version": project_version_string,
        "dependencies": [
            "RecompExternalPython_API:2.0.0"
        ]
    },
    "inputs": {
        "elf_path": str(mod_elf_path),
        "additional_files": [ 
            str(root_dir.joinpath("icons/mod/thumb.dds"))
        ],
        "mod_filename": project_name
    }
}

tests_toml_data = {
    "manifest": {
        "id": project_tests_name,
        "version": project_version_string,
        "dependencies": [
            f"{project_name}:{project_version_string}"
        ]
    },
    "inputs": {
        "elf_path": str(tests_elf_path),
        "additional_files": [
            str(root_dir.joinpath("icons/tests/thumb.dds"))],
        "mod_filename": project_tests_name
    }
}

# If you need this enabled, you should probably rethink whatever it is you're doing:
# Convienience function for downloading compiler artifacts.
def add_archive_download_and_extract(name: str, url: str, extract_dir: Path) -> tuple[DownloadJob, ArchiveExtractJob]:
    global archive_extractions, downloads, archive_downloads_dir
    
    new_download = DownloadJob(url, archive_downloads_dir)
    new_extraction = ArchiveExtractJob(new_download.download_path, extract_dir)
    new_extraction.depends_on([new_download])
    downloads[name] = new_download
    archive_extractions[name] = new_extraction
    
    return new_download, new_extraction

# Deciding with compiler/tool archive to download for your platform:
if platform.system() == "Windows":
    llvmmips_download, llvmmips_extraction = add_archive_download_and_extract(
        "llvmmips",
        "https://github.com/LT-Schmiddy/n64recomp-clang/releases/download/release-21.1.8/Windows-AMD64-ClangEssentialsAndN64Recomp-ClangVersion21.1.8-MipsOnly.zip",
        binaries_dir.joinpath("llvmmips_win")
    )
    make_mips_compiler_path = binaries_dir.joinpath("llvmmips_win/nrs_bin/clang.exe")
    make_mips_linker_path = binaries_dir.joinpath("llvmmips_win/nrs_bin/ld.lld.exe")
    mod_tool_path = binaries_dir.joinpath("llvmmips_win/nrs_bin/RecompModTool.exe")
        
    
elif platform.system() == "Darwin":
    llvmmips_download, llvmmips_extraction = add_archive_download_and_extract(
        "llvmmips",
        "https://github.com/LT-Schmiddy/n64recomp-clang/releases/download/release-21.1.8/Darwin-arm64-ClangEssentialsAndN64Recomp-ClangVersion21.1.8-MipsOnly.tar.xz",
        binaries_dir.joinpath("llvmmips_macos")
    )
    make_mips_compiler_path = binaries_dir.joinpath("llvmmips_macos/nrs_bin/clang")
    make_mips_linker_path = binaries_dir.joinpath("llvmmips_macos/nrs_bin/ld.lld")
    mod_tool_path = binaries_dir.joinpath("llvmmips_macos/nrs_bin/RecompModTool")
    
else:
    llvmmips_download, llvmmips_extraction = add_archive_download_and_extract(
        "llvmmips",
        "https://github.com/LT-Schmiddy/n64recomp-clang/releases/download/release-21.1.8/Linux-x86_64-ClangEssentialsAndN64Recomp-ClangVersion21.1.8-MipsOnly.tar.xz",
        binaries_dir.joinpath("llvmmips_linux")
    )
    

python_version_string_nt = "python314t"
python_version_string_posix = "python3.14t"

downloads["python_win"] = python_windows_download = DownloadJob(
    "https://github.com/astral-sh/python-build-standalone/releases/download/20260203/cpython-3.14.3+20260203-x86_64-pc-windows-msvc-freethreaded+pgo-full.tar.zst",
    archive_downloads_dir
)

downloads["python_macos"] = python_macos_download = DownloadJob(
    "https://github.com/astral-sh/python-build-standalone/releases/download/20260203/cpython-3.14.3+20260203-aarch64-apple-darwin-freethreaded+pgo+lto-full.tar.zst",
    archive_downloads_dir
)

downloads["python_linux"] = python_linux_download = DownloadJob(
    "https://github.com/astral-sh/python-build-standalone/releases/download/20260203/cpython-3.14.3+20260203-x86_64-unknown-linux-gnu-freethreaded+pgo+lto-full.tar.zst",
    archive_downloads_dir
)

def prepend_to_env_path(to_append: Path) -> str:
    global llvm_path
    PATH_DELIMITER = ";" if os.name == 'nt' else ":"
    env_path = os.environ['PATH']
    for i in to_append:
        env_path = str(i) + PATH_DELIMITER + env_path
    return env_path

# ELF Binaries:
makefiles['mod'] = mod_makefile = MakefileJob(
    root_dir.joinpath("mod_elf.mk"),
    {
        "_ELF_PATH": str(mod_elf_path),
        "_BUILD_DIR": str(mod_build_dir),
        "_MIPS_CC": str(make_mips_compiler_path),
        "_MIPS_LD": str(make_mips_linker_path),
        "_SRC_DIR": "src",
        "_PY_BUILD_FLAGS": ""
    }
)
mod_makefile.depends_on([llvmmips_extraction])

# makefiles['tests'] = tests_makefile = MakefileJob(
#     root_dir.joinpath("mod_elf.mk"),
#     {
#         "_ELF_PATH": str(tests_elf_path),
#         "_BUILD_DIR": str(tests_build_dir),
#         "_MIPS_CC": str(make_mips_compiler_path),
#         "_MIPS_LD": str(make_mips_linker_path),
#         "_SRC_DIR": "src/tests",
#         "_PY_BUILD_FLAGS": ""
#     }
# )
# tests_makefile.depends_on([llvmmips_extraction])

def add_toml_and_nrm_job(game_id: str, toml_type: str, build_dir: Path, data_dicts: list[dict], nrm_dependencies: list[JobBase], inject_files: dict[Path, Path] = None) -> tuple[GenerateTomlJob, ModToNRMJob]:
    global tomls, nrms
    
    mod_key = f"{game_id}_{toml_type}"
    
    nrm_build_dir = build_dir.joinpath(game_id)
    toml_path = nrm_build_dir.joinpath(f"{mod_key}.toml")
    
    tomls[mod_key] = mod_toml = GenerateTomlJob.from_merged_dicts(toml_path, data_dicts)
    nrms[mod_key] = mod_nrm = ModToNRMJob(mod_tool_path, toml_path, nrm_build_dir, delay_read=True, nrm_path_fix=True, inject_files=inject_files)
    mod_nrm.depends_on([mod_toml] + nrm_dependencies)
    
    return mod_toml, mod_nrm

# Loading TOML Data:
mod_common_data = toml.loads(root_dir.joinpath("mod_common.toml").read_text())
tests_common_data = toml.loads(root_dir.joinpath("tests_common.toml").read_text())

from package_files import include_python_files

mm_mod_toml, mm_mod_nrm = add_toml_and_nrm_job("mm", "ppp", mod_build_dir, [mod_common_data, mm_toml_data, mod_toml_data], [archive_extractions["llvmmips"], makefiles['mod']], include_python_files)
bk_mod_toml, bk_mod_nrm = add_toml_and_nrm_job("bk", "ppp", mod_build_dir, [mod_common_data, bk_toml_data, mod_toml_data], [archive_extractions["llvmmips"], makefiles['mod']], include_python_files)
sf64_mod_toml, sf64_mod_nrm = add_toml_and_nrm_job("sf64", "ppp", mod_build_dir, [mod_common_data, sf64_toml_data, mod_toml_data], [archive_extractions["llvmmips"], makefiles['mod']], include_python_files)
mk64_mod_toml, mk64_mod_nrm = add_toml_and_nrm_job("mk64", "ppp", mod_build_dir, [mod_common_data, mk64_toml_data, mod_toml_data], [archive_extractions["llvmmips"], makefiles['mod']], include_python_files)
mnsg_mod_toml, mnsg_mod_nrm = add_toml_and_nrm_job("mnsg", "ppp", mod_build_dir, [mod_common_data, mnsg_toml_data, mod_toml_data], [archive_extractions["llvmmips"], makefiles['mod']], include_python_files)

def add_build_output(job_name: str, output_path: Path, dependencies: list[JobBase]) -> BuildOutputJob:
    build_outputs[job_name] = build_job = BuildOutputJob(root_dir.joinpath(output_path))
    build_job.depends_on(dependencies)
    return build_job

add_build_output("zelda_debug", "test_env/zelda/mods", [mm_mod_nrm])
add_build_output("bk_debug", "test_env/bk/mods", [bk_mod_nrm])
add_build_output("sf64_debug", "test_env/sf64/mods", [sf64_mod_nrm])
add_build_output("mk64_debug", "test_env/mk64/mods", [mk64_mod_nrm])
add_build_output("mnsg_debug", "test_env/mnsg/mods", [mnsg_mod_nrm])

def package_url_from_git() -> str:
    result = subprocess.run(
        [
            shutil.which("git"),
            "config", 
            "--get", 
            "remote.origin.url"
        ],
        cwd=root_dir,
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        return result.stdout.strip()
    else:
        return None

def add_thunderstore_package(job_name: str, package_name: str, version_str: str, dependencies: list[JobBase]) -> ThunderstorePackageJob:
    thunderstore_packages[job_name] = package = ThunderstorePackageJob(
        package_dir.joinpath(f"{package_name}.thunderstore.zip"),
        {
            "name": package_name,
            "version_number": version_str,
            "website_url": package_url_from_git(),
            "description": "A resource for modders. Enables use of Python code and the Python Standard Library within mods, enabling many behaviors that would otherwise require an external library to be compiled.",
            "dependencies": []
        },
        root_dir.joinpath("thunderstore_info/README.md").read_text(),
        root_dir.joinpath("thunderstore_info/CHANGELOG.md").read_text(),
        root_dir.joinpath("icons/mod/thumb.png")
    )
    package.depends_on(dependencies)
    
    return package

add_thunderstore_package("mm", "RecompExternalPython_for_Zelda64Recompiled", project_version_string, [mm_mod_nrm])
add_thunderstore_package("bk", "RecompExternalPython_for_BanjoRecompiled", project_version_string, [bk_mod_nrm])
add_thunderstore_package("sf64", "RecompExternalPython_for_Starfox64Recompiled", project_version_string, [sf64_mod_nrm])
add_thunderstore_package("mk64", "RecompExternalPython_for_MarioKart64Recompiled", project_version_string, [mk64_mod_nrm])
add_thunderstore_package("mnsg", "RecompExternalPython_for_Goemon64Recompiled", project_version_string, [mnsg_mod_nrm])

clean_paths: list[Path] = [
    build_dir
] + [
    i.test_path for i in build_outputs.values()
] + [
    i.package_file for i in thunderstore_packages.values()
]

distclean_paths: list[Path] = [
    binaries_dir,
    archive_downloads_dir,
]