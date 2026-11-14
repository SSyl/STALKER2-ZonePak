# Building the patched retoc yourself

This page explains how to build the patched `retoc.exe` from source instead of downloading it.

ZonePak runs retoc only to build mods with text overrides. Cfg-only mods do not need it. The patched retoc lives in
[STALKER2-zonekit-retoc](https://github.com/SSyl/STALKER2-zonekit-retoc), a fork of trumank's retoc whose release
`v0.1.5-zonekit.1` is the build ZonePak downloads. To build the same `retoc.exe` yourself, install Git from
https://git-scm.com and the Rust toolchain with rustup from https://rustup.rs. Rust on Windows also needs the
Microsoft C++ build tools. rustup's installer offers to install them, and if it does not, install **Desktop
development with C++** from the Visual Studio Build Tools. Then run these commands in a command prompt:

```
git clone --branch v0.1.5-zonekit.1 https://github.com/SSyl/STALKER2-zonekit-retoc C:\Tools\retoc-src
cd /d C:\Tools\retoc-src
set CARGO_TARGET_DIR=C:\t\retoc
cargo build --locked --release -p retoc_cli
```

The result is `C:\t\retoc\release\retoc.exe`. Copy it into ZonePak's `third_party` folder, or set `retoc` in the
config file to its path. `CARGO_TARGET_DIR` keeps the build folder's path short, because the `blake3` build script
fails under a long path on Windows.

The fork's README lists what it changes. It lets retoc set the container mount point and the package redirects that
ZonePak's text builds need.
