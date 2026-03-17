# CHANGELOG

## 2.0.0

* Updated to Python 3.14.3
* Now using a free-threaded build of Python. Python code can now take full advantage of multi-threading.
* Added support for BanjoRecompiled and Starfox64Recompiled, with their own Thunderstore packages.
* Fixed the .nrm containing `\\` in path names, which prevented use of the `repy_api` module on POSIX systems.
* Critical Python files such as the standard library are no longer stored in the mods folder, but instead stored in `python314t` to match the Python version.
* Total rewrite of the build-scripting. Building is now invoked via `./modbuild.py`

## Version 1.0.0

* Initial release
