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

project_name = "RecompExternalPython_API"
project_tests_name = "Test_" + project_name
project_version_string = "2.0.0"

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
        "dependencies": []
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
    
    zig_download, zig_extraction = add_archive_download_and_extract(
        "zig",
        "https://ziglang.org/download/0.14.1/zig-x86_64-windows-0.14.1.zip",
        binaries_dir.joinpath("zig_win")
    )
    zig_dir_path = binaries_dir.joinpath("zig_win/zig-x86_64-windows-0.14.1")
    zig_bin_path = zig_dir_path.joinpath("zig.exe")
    

    llvm_download, llvm_extraction = add_archive_download_and_extract(
        "llvm",
        "https://github.com/llvm/llvm-project/releases/download/llvmorg-19.1.7/clang+llvm-19.1.7-x86_64-pc-windows-msvc.tar.xz",
        binaries_dir.joinpath("llvm_win")
    )
    
    llvm_path = binaries_dir.joinpath("llvm_win/clang+llvm-19.1.7-x86_64-pc-windows-msvc")
        
    
elif platform.system() == "Darwin":
    llvmmips_download, llvmmips_extraction = add_archive_download_and_extract(
        "llvmmips",
        "https://github.com/LT-Schmiddy/n64recomp-clang/releases/download/release-21.1.8/Darwin-arm64-ClangEssentialsAndN64Recomp-ClangVersion21.1.8-MipsOnly.tar.xz",
        binaries_dir.joinpath("llvmmips_macos")
    )
    make_mips_compiler_path = binaries_dir.joinpath("llvmmips_macos/nrs_bin/clang")
    make_mips_linker_path = binaries_dir.joinpath("llvmmips_macos/nrs_bin/ld.lld")
    mod_tool_path = binaries_dir.joinpath("llvmmips_macos/nrs_bin/RecompModTool")
    
    zig_download, zig_extraction = add_archive_download_and_extract(
        "zig",
        "https://ziglang.org/download/0.14.1/zig-aarch64-macos-0.14.1.tar.xz",
        binaries_dir.joinpath("zig_macos")
    )
    zig_dir_path = binaries_dir.joinpath("zig_linux/zig-aarch64-macos-0.14.1")
    zig_bin_path = zig_dir_path.joinpath("zig")
    
    
    llvm_download, llvm_extraction = add_archive_download_and_extract(
        "llvm",
        "https://github.com/llvm/llvm-project/releases/download/llvmorg-19.1.7/LLVM-19.1.7-macOS-ARM64.tar.xz",
        binaries_dir.joinpath("llvm_macos")
    )
    llvm_path = binaries_dir.joinpath("llvm_macos/LLVM-19.1.7-macOS-ARM64")
    
else:
    llvmmips_download, llvmmips_extraction = add_archive_download_and_extract(
        "llvmmips",
        "https://github.com/LT-Schmiddy/n64recomp-clang/releases/download/release-21.1.8/Linux-x86_64-ClangEssentialsAndN64Recomp-ClangVersion21.1.8-MipsOnly.tar.xz",
        binaries_dir.joinpath("llvmmips_linux")
    )
    
    make_mips_compiler_path = binaries_dir.joinpath("llvmmips_linux/nrs_bin/clang")
    make_mips_linker_path = binaries_dir.joinpath("llvmmips_linux/nrs_bin/ld.lld")
    mod_tool_path = binaries_dir.joinpath("llvmmips_linux/nrs_bin/RecompModTool")
    
    zig_download, zig_extraction = add_archive_download_and_extract(
        "zig",
        "https://ziglang.org/download/0.14.1/zig-x86_64-linux-0.14.1.tar.xz",
         binaries_dir.joinpath("zig_linux")
    )
    zig_dir_path = binaries_dir.joinpath("zig_linux/zig-x86_64-linux-0.14.1")
    zig_bin_path = binaries_dir.joinpath("zig")
    
    llvm_download, llvm_extraction = add_archive_download_and_extract(
        "llvm",
        "https://github.com/llvm/llvm-project/releases/download/llvmorg-19.1.7/LLVM-19.1.7-Linux-X64.tar.xz",
        binaries_dir.joinpath("llvm_linux")
    )
    llvm_path = binaries_dir.joinpath("llvm_linux/LLVM-19.1.7-Linux-X64")

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
        "_SRC_DIR": "src/mod",
        "_PY_BUILD_FLAGS": "-DRECOMP_PY_BUILD_MODE"
    }
)
mod_makefile.depends_on([llvmmips_extraction])

makefiles['tests'] = tests_makefile = MakefileJob(
    root_dir.joinpath("mod_elf.mk"),
    {
        "_ELF_PATH": str(tests_elf_path),
        "_BUILD_DIR": str(tests_build_dir),
        "_MIPS_CC": str(make_mips_compiler_path),
        "_MIPS_LD": str(make_mips_linker_path),
        "_SRC_DIR": "src/tests",
        "_PY_BUILD_FLAGS": ""
    }
)
tests_makefile.depends_on([llvmmips_extraction])

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

def populate_repy_api_file_injection(injections: dict[Path, Path], search_dir: Path, inject_root: Path):
    for inject_path, file_path in [(inject_root.joinpath(i), search_dir.joinpath(i)) for i in os.listdir(search_dir)]:
        if file_path.is_file():
            injections[inject_path] = file_path
        elif file_path.is_dir():
            populate_repy_api_file_injection(injections, file_path, inject_path)

repy_api_files = {}
populate_repy_api_file_injection(repy_api_files, repy_api_src, Path("repy_api"))

mm_mod_toml, mm_mod_nrm = add_toml_and_nrm_job("mm", "mod", mod_build_dir, [mod_common_data, mm_toml_data, mod_toml_data], [archive_extractions["llvmmips"], makefiles['mod']], repy_api_files)
bk_mod_toml, bk_mod_nrm = add_toml_and_nrm_job("bk", "mod", mod_build_dir, [mod_common_data, bk_toml_data, mod_toml_data], [archive_extractions["llvmmips"], makefiles['mod']], repy_api_files)
sf64_mod_toml, sf64_mod_nrm = add_toml_and_nrm_job("sf64", "mod", mod_build_dir, [mod_common_data, sf64_toml_data, mod_toml_data], [archive_extractions["llvmmips"], makefiles['mod']], repy_api_files)
mk64_mod_toml, mk64_mod_nrm = add_toml_and_nrm_job("mk64", "mod", mod_build_dir, [mod_common_data, mk64_toml_data, mod_toml_data], [archive_extractions["llvmmips"], makefiles['mod']], repy_api_files)
mnsg_mod_toml, mnsg_mod_nrm = add_toml_and_nrm_job("mnsg", "mod", mod_build_dir, [mod_common_data, mnsg_toml_data, mod_toml_data], [archive_extractions["llvmmips"], makefiles['mod']], repy_api_files)
mm_tests_toml, mm_tests_nrm = add_toml_and_nrm_job("mm", "tests", tests_build_dir, [tests_common_data, mm_toml_data, tests_toml_data], [archive_extractions["llvmmips"], makefiles['tests']])
bk_tests_toml, bk_tests_nrm = add_toml_and_nrm_job("bk", "tests", tests_build_dir, [tests_common_data, bk_toml_data, tests_toml_data], [archive_extractions["llvmmips"], makefiles['tests']])
sf64_tests_toml, sf64_tests_nrm = add_toml_and_nrm_job("sf64", "tests", tests_build_dir, [tests_common_data, sf64_toml_data, tests_toml_data], [archive_extractions["llvmmips"], makefiles['tests']])
mk64_tests_toml, mk64_tests_nrm = add_toml_and_nrm_job("mk64", "tests", tests_build_dir, [tests_common_data, mk64_toml_data, tests_toml_data], [archive_extractions["llvmmips"], makefiles['tests']])
mnsg_tests_toml, mnsg_tests_nrm = add_toml_and_nrm_job("mnsg", "tests", tests_build_dir, [tests_common_data, mnsg_toml_data, tests_toml_data], [archive_extractions["llvmmips"], makefiles['tests']])

# Extlib Compilation
extlib_name = "RecompPythonNative"
extlib = CMakeProjectConfig(
    root_dir,
    {
        # Unlike with clangmips, we're gonna prepend the LLVM and ZIG directories to the PATH that CMake recieves.
        "PATH": prepend_to_env_path([llvm_path.joinpath("bin"), zig_dir_path]),
        "LIB_NAME": extlib_name,
        "PYTHON_WIN_ARCHIVE": str(python_windows_download.download_path),
        "PYTHON_MACOS_ARCHIVE": str(python_macos_download.download_path),
        "PYTHON_LINUX_ARCHIVE": str(python_linux_download.download_path),
        "PYTHON_ARCHIVE_VSTR_NT": python_version_string_nt,
        "PYTHON_ARCHIVE_VSTR_POSIX": python_version_string_posix,
    }
)

def get_preset_lib_path(preset_name: str) -> Path:
    global root_dir
    return root_dir.joinpath(f"build/{preset_name}/lib")

def with_windows_dlls(preset_string: str, output_paths: dict[Path, Path]) -> dict[Path, Path]:
    global root_dir
    windows_dll_names = [
        "libcrypto-3-x64.dll",
        "libffi-8.dll",
        "libssl-3-x64.dll",
        "pyexpat.cp314t-win_amd64.pyd",
        "select.cp314t-win_amd64.pyd",
        "sqlite3.dll",
        "tcl86t.dll",
        "tk86t.dll",
        "unicodedata.cp314t-win_amd64.pyd",
        "winsound.cp314t-win_amd64.pyd",
        "zlib1.dll",
        "_asyncio.cp314t-win_amd64.pyd",
        "_bz2.cp314t-win_amd64.pyd",
        "_ctypes.cp314t-win_amd64.pyd",
        "_ctypes_test.cp314t-win_amd64.pyd",
        "_decimal.cp314t-win_amd64.pyd",
        "_elementtree.cp314t-win_amd64.pyd",
        "_hashlib.cp314t-win_amd64.pyd",
        "_lzma.cp314t-win_amd64.pyd",
        "_multiprocessing.cp314t-win_amd64.pyd",
        "_overlapped.cp314t-win_amd64.pyd",
        "_queue.cp314t-win_amd64.pyd",
        "_remote_debugging.cp314t-win_amd64.pyd",
        "_socket.cp314t-win_amd64.pyd",
        "_sqlite3.cp314t-win_amd64.pyd",
        "_ssl.cp314t-win_amd64.pyd",
        "_testbuffer.cp314t-win_amd64.pyd",
        "_testcapi.cp314t-win_amd64.pyd",
        "_testclinic.cp314t-win_amd64.pyd",
        "_testclinic_limited.cp314t-win_amd64.pyd",
        "_testconsole.cp314t-win_amd64.pyd",
        "_testimportmultiple.cp314t-win_amd64.pyd",
        "_testinternalcapi.cp314t-win_amd64.pyd",
        "_testlimitedcapi.cp314t-win_amd64.pyd",
        "_testmultiphase.cp314t-win_amd64.pyd",
        "_testsinglephase.cp314t-win_amd64.pyd",
        "_tkinter.cp314t-win_amd64.pyd",
        "_uuid.cp314t-win_amd64.pyd",
        "_wmi.cp314t-win_amd64.pyd",
        "_zoneinfo.cp314t-win_amd64.pyd",
        "_zstd.cp314t-win_amd64.pyd"
    ]
    
    python_dll_dir =  root_dir.joinpath(f"build/{preset_string}/python-standalone/python/install/DLLs")
    
    for file in [python_dll_dir.joinpath(i) for i in windows_dll_names]:
        if file.suffix == ".dll":
            output_paths[Path(file.name)] = file
        elif file.suffix == ".pyd":
            ## Doing it this way removed the python version pre-suffix.
            output_paths[Path(file.with_suffix("").with_suffix(".dll").name)] = file
            
    return output_paths

def native_preset_name(build_type: str):
    if platform.system() == "Windows":
        return f"native-windows-x64-{build_type}"
    if platform.system() == "Darwin":
        return f"native-macos-aarch64-{build_type}"
    if platform.system() == "Linux":
        return f"native-linux-x64-{build_type}"
    
def native_python_download():
    if platform.system() == "Windows":
        return python_windows_download
    if platform.system() == "Darwin":
        return python_macos_download
    if platform.system() == "Linux":
        return python_linux_download

def native_output_files(build_type: str) -> dict[Path, Path]:
    preset_name = native_preset_name(build_type)
    if platform.system() == "Windows":
        win_base = {
            Path("python313.dll"): get_preset_lib_path(preset_name).joinpath(f"{python_version_string_nt}.dll"),
            Path(f"{extlib_name}.dll"): get_preset_lib_path(preset_name).joinpath(f"{extlib_name}.dll")
        }
        if build_type == "Debug" or build_type == "RelWithDebInfo" or build_type == "TracyProfiling":
            win_base[Path(f"{extlib_name}.pdb")] = get_preset_lib_path(preset_name).joinpath(f"{extlib_name}.pdb")
        return with_windows_dlls(preset_name, win_base)
    if platform.system() == "Darwin":
        return {
            Path(f"lib{python_version_string_posix}.dylib"): get_preset_lib_path(preset_name).joinpath(f"lib{python_version_string_posix}.dylib"),
            Path(f"{extlib_name}.dylib"): get_preset_lib_path(preset_name).joinpath(f"{extlib_name}.dylib")
        }
    if platform.system() == "Linux":
        return {
            Path(f"lib{python_version_string_posix}.so.1.0"): get_preset_lib_path(preset_name).joinpath(f"lib{python_version_string_posix}.so.1.0"),
            Path(f"{extlib_name}.so"): get_preset_lib_path(preset_name).joinpath(f"{extlib_name}.so")
        }
    
cmake_default_build_group_name: str = "Debug"
cmake_build_groups = {
    "Debug" : {
        "Windows": CMakeBuildJob.from_preset_pair(extlib, with_windows_dlls("zig-windows-x64-Debug", {
                Path(f"{python_version_string_nt}.dll"): get_preset_lib_path("zig-windows-x64-Debug").joinpath(f"{python_version_string_nt}.dll"),
                Path(f"{extlib_name}.dll"): get_preset_lib_path("zig-windows-x64-Debug").joinpath(f"{extlib_name}.dll"),
                Path(f"{extlib_name}.pdb"): get_preset_lib_path("zig-windows-x64-Debug").joinpath(f"{extlib_name}.pdb")
            }), "zig-windows-x64-Debug"),
        "Darwin": CMakeBuildJob.from_preset_pair(extlib, {
                Path(f"lib{python_version_string_posix}.dylib"): get_preset_lib_path("zig-macos-aarch64-Debug").joinpath(f"lib{python_version_string_posix}.dylib"),
                Path(f"{extlib_name}.dylib"): get_preset_lib_path("zig-macos-aarch64-Debug").joinpath(f"{extlib_name}.dylib")
            }, "zig-macos-aarch64-Debug"),
        "Linux": CMakeBuildJob.from_preset_pair(extlib, {
                Path(f"lib{python_version_string_posix}.so.1.0"): get_preset_lib_path("zig-linux-x64-Debug").joinpath(f"lib{python_version_string_posix}.so.1.0"),
                Path(f"{extlib_name}.so"): get_preset_lib_path("zig-linux-x64-Debug").joinpath(f"{extlib_name}.so")
            }, "zig-linux-x64-Debug"),
    },
    "Release" : {
        "Windows": CMakeBuildJob.from_preset_pair(extlib, with_windows_dlls("zig-windows-x64-Release", {
                 Path(f"{python_version_string_nt}.dll"): get_preset_lib_path("zig-windows-x64-Release").joinpath(f"{python_version_string_nt}.dll"),
                Path(f"{extlib_name}.dll"): get_preset_lib_path("zig-windows-x64-Release").joinpath(f"{extlib_name}.dll")
            }), "zig-windows-x64-Release"),
        "Darwin": CMakeBuildJob.from_preset_pair(extlib, {
                Path(f"lib{python_version_string_posix}.dylib"): get_preset_lib_path("zig-macos-aarch64-Release").joinpath(f"lib{python_version_string_posix}.dylib"),
                Path(f"{extlib_name}.dylib"): get_preset_lib_path("zig-macos-aarch64-Release").joinpath(f"{extlib_name}.dylib")
            }, "zig-macos-aarch64-Release"),
        "Linux": CMakeBuildJob.from_preset_pair(extlib, {
                Path(f"lib{python_version_string_posix}.so.1.0"): get_preset_lib_path("zig-linux-x64-Release").joinpath(f"lib{python_version_string_posix}.so.1.0"),
                Path(f"{extlib_name}.so"): get_preset_lib_path("zig-linux-x64-Release").joinpath(f"{extlib_name}.so")
            }, "zig-linux-x64-Release"),
    }, 
    "RelWithDebInfo": {
        "Windows": CMakeBuildJob.from_preset_pair(extlib, with_windows_dlls("zig-windows-x64-RelWithDebInfo", {
                Path(f"{python_version_string_nt}.dll"): get_preset_lib_path("zig-windows-x64-RelWithDebInfo").joinpath(f"{python_version_string_nt}.dll"),
                Path(f"{extlib_name}.dll"): get_preset_lib_path("zig-windows-x64-RelWithDebInfo").joinpath(f"{extlib_name}.dll"),
                Path(f"{extlib_name}.pdb"): get_preset_lib_path("zig-windows-x64-RelWithDebInfo").joinpath(f"{extlib_name}.pdb")
            }), "zig-windows-x64-RelWithDebInfo"),
        "Darwin": CMakeBuildJob.from_preset_pair(extlib, {
                Path(f"lib{python_version_string_posix}.dylib"): get_preset_lib_path("zig-macos-aarch64-RelWithDebInfo").joinpath(f"lib{python_version_string_posix}.dylib"),
                Path(f"{extlib_name}.dylib"): get_preset_lib_path("zig-macos-aarch64-RelWithDebInfo").joinpath(f"{extlib_name}.dylib")
            }, "zig-macos-aarch64-RelWithDebInfo"),
        "Linux": CMakeBuildJob.from_preset_pair(extlib, {
                Path(f"lib{python_version_string_posix}.so.1.0"): get_preset_lib_path("zig-linux-x64-RelWithDebInfo").joinpath(f"lib{python_version_string_posix}.so.1.0"),
                Path(f"{extlib_name}.so"): get_preset_lib_path("zig-linux-x64-RelWithDebInfo").joinpath(f"{extlib_name}.so")
            }, "zig-linux-x64-RelWithDebInfo"),
    },
    "TracyProfiling": {
        "Windows": CMakeBuildJob.from_preset_pair(extlib, with_windows_dlls("zig-windows-x64-TracyProfiling", {
                Path(f"{python_version_string_nt}.dll"): get_preset_lib_path("zig-windows-x64-TracyProfiling").joinpath(f"{python_version_string_nt}.dll"),
                Path(f"{extlib_name}.dll"): get_preset_lib_path("zig-windows-x64-TracyProfiling").joinpath(f"{extlib_name}.dll"),
                Path(f"{extlib_name}.pdb"): get_preset_lib_path("zig-windows-x64-TracyProfiling").joinpath(f"{extlib_name}.pdb")
            }), "zig-windows-x64-TracyProfiling"),
        "Darwin": CMakeBuildJob.from_preset_pair(extlib, {
                Path(f"lib{python_version_string_posix}.dylib"): get_preset_lib_path("zig-macos-aarch64-TracyProfiling").joinpath(f"lib{python_version_string_posix}.dylib"),
                Path(f"{extlib_name}.dylib"): get_preset_lib_path("zig-macos-aarch64-TracyProfiling").joinpath(f"{extlib_name}.dylib")
            }, "zig-macos-aarch64-TracyProfiling"),
        "Linux": CMakeBuildJob.from_preset_pair(extlib, {
                Path(f"lib{python_version_string_posix}.so.1.0"): get_preset_lib_path("zig-linux-x64-TracyProfiling").joinpath(f"lib{python_version_string_posix}.so.1.0"),
                Path(f"{extlib_name}.so"): get_preset_lib_path("zig-linux-x64-TracyProfiling").joinpath(f"{extlib_name}.so")
            }, "zig-linux-x64-TracyProfiling"),
    },
    
    "MinSizeRel": {
        "Windows": CMakeBuildJob.from_preset_pair(extlib, with_windows_dlls("zig-windows-x64-MinSizeRel", {
                Path(f"{python_version_string_posix}.dll"): get_preset_lib_path("zig-windows-x64-MinSizeRel").joinpath(f"{python_version_string_posix}.dll"),
                Path(f"{extlib_name}.dll"): get_preset_lib_path("zig-windows-x64-MinSizeRel").joinpath(f"{extlib_name}.dll")
            }), "zig-windows-x64-MinSizeRel"),
        "Darwin": CMakeBuildJob.from_preset_pair(extlib, {
                Path(f"lib{python_version_string_posix}.dylib"): get_preset_lib_path("zig-macos-aarch64-MinSizeRel").joinpath(f"lib{python_version_string_posix}.dylib"),
                Path(f"{extlib_name}.dylib"): get_preset_lib_path("zig-macos-aarch64-MinSizeRel").joinpath(f"{extlib_name}.dylib")
            }, "zig-macos-aarch64-MinSizeRel"),
        "Linux": CMakeBuildJob.from_preset_pair(extlib, {
                Path(f"lib{python_version_string_posix}.so.1.0"): get_preset_lib_path("zig-linux-x64-MinSizeRel").joinpath(f"lib{python_version_string_posix}.so.1.0"),
                Path(f"{extlib_name}.so"): get_preset_lib_path("zig-linux-x64-MinSizeRel").joinpath(f"{extlib_name}.so")
            }, "zig-linux-x64-MinSizeRel"),
    },
    "native-Debug" : {
        "Native": CMakeBuildJob.from_preset_pair(extlib, native_output_files("Debug"), native_preset_name("Debug")),
    },
    "native-Release" : {
        "Native": CMakeBuildJob.from_preset_pair(extlib, native_output_files("Release"), native_preset_name("Release")),
    },
    "native-RelWithDebInfo": {
        "Native": CMakeBuildJob.from_preset_pair(extlib, native_output_files("RelWithDebInfo"), native_preset_name("RelWithDebInfo")),
    },
    "native-TracyProfiling": {
        "Native": CMakeBuildJob.from_preset_pair(extlib, native_output_files("TracyProfiling"), native_preset_name("TracyProfiling")),
    },
    "native-MinSizeRel": {
        "Native": CMakeBuildJob.from_preset_pair(extlib, native_output_files("MinSizeRel"), native_preset_name("MinSizeRel")),
    }
}

for group_key, group in cmake_build_groups.items():
    for build_key, build in group.items():
        if not group_key.startswith("native-"):
            build.depends_on([archive_extractions["zig"]])
            if build_key == "Windows":
                build.depends_on([python_windows_download])
            elif build_key == "Darwin":
                build.depends_on([python_macos_download])
            elif build_key == "Linux":
                build.depends_on([python_linux_download])
        else:
            build.depends_on([native_python_download()])
            
        build.depends_on([archive_extractions["llvm"]])
        

def add_build_output(job_name: str, output_path: Path, dependencies: list[JobBase]) -> BuildOutputJob:
    build_outputs[job_name] = build_job = BuildOutputJob(root_dir.joinpath(output_path))
    build_job.depends_on(dependencies)
    return build_job

cmake_debug_builds = [i for i in cmake_build_groups["Debug"].values()]
add_build_output("zelda_debug", "test_env/zelda/mods", [mm_mod_nrm, mm_tests_nrm] + cmake_debug_builds)
add_build_output("bk_debug", "test_env/bk/mods", [bk_mod_nrm, bk_tests_nrm] + cmake_debug_builds)
add_build_output("sf64_debug", "test_env/sf64/mods", [sf64_mod_nrm, sf64_tests_nrm] + cmake_debug_builds)
add_build_output("mk64_debug", "test_env/mk64/mods", [mk64_mod_nrm, mk64_tests_nrm] + cmake_debug_builds)
add_build_output("mnsg_debug", "test_env/mnsg/mods", [mnsg_mod_nrm, mnsg_tests_nrm] + cmake_debug_builds)

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

cmake_release_builds = [i for i in cmake_build_groups["Release"].values()]
add_thunderstore_package("mm", "RecompExternalPython_for_Zelda64Recompiled", project_version_string, [mm_mod_nrm] + cmake_release_builds)
add_thunderstore_package("bk", "RecompExternalPython_for_BanjoRecompiled", project_version_string, [bk_mod_nrm] + cmake_release_builds)
add_thunderstore_package("sf64", "RecompExternalPython_for_Starfox64Recompiled", project_version_string, [sf64_mod_nrm] + cmake_release_builds)
add_thunderstore_package("mk64", "RecompExternalPython_for_MarioKart64Recompiled", project_version_string, [mk64_mod_nrm] + cmake_release_builds)
add_thunderstore_package("mnsg", "RecompExternalPython_for_Goemon64Recompiled", project_version_string, [mnsg_mod_nrm] + cmake_release_builds)

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