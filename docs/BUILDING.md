# Building Dandelion

Dandelion builds from Firefox source with `mach`.

## Requirements

| | |
| --- | --- |
| Disk | ~40 GB for the checkout and one build configuration |
| RAM | 8 GB minimum, 16 GB+ recommended |
| OS | Windows 10/11 x64 (macOS and Linux are not yet wired up) |

### Windows

1. **[MozillaBuild](https://ftp.mozilla.org/pub/mozilla/libraries/win32/MozillaBuildSetup-Latest.exe)**.
   Firefox cannot build on Windows without it; it supplies the Unix tools the
   build system shells out to. Install to the default `C:\mozilla-build`.

   The installer is `MozillaBuildSetup-Latest.exe` (~176 MB), in
   [pub/mozilla/libraries/win32/](https://ftp.mozilla.org/pub/mozilla/libraries/win32/)
   alongside the numbered releases.
2. **Visual Studio 2022 or later** with the *Desktop development with C++*
   workload and the Windows SDK. Build Tools editions are sufficient.
3. **Rust and clang**, installed for you by `mach bootstrap` — see below.

The checkout path must contain **no spaces**; Firefox will not build from one.
`build/sync.py` refuses such a path rather than letting the build fail later.

## Checkout

```sh
python build\sync.py --bootstrap
```

This clones Firefox at the release pinned in `FIREFOX_VERSION`, mounts
`branding/` into the tree as `browser/branding/dandelion`, applies Dandelion's
patches, and runs `mach bootstrap` to install Rust and clang.

The checkout defaults to `C:\src\firefox`; override it with
`DANDELION_FIREFOX_SRC`. Re-running is safe — an interrupted clone resumes.

Drop `--bootstrap` if the toolchain is already installed. Add `--depth 1` for a
shallow clone, at the cost of needing `git fetch --unshallow` before your first
Firefox roll.

### Watching a clone in progress

The size of `.git` is a useless progress signal until the clone finishes.
Windows does not refresh a file's directory entry while a process holds it
open, so the incoming pack reports 0 bytes for the entire download even as
gigabytes land on disk. Use the process counters and free disk space instead:

```powershell
Get-CimInstance Win32_Process -Filter "Name='git.exe'" |
  Sort-Object WorkingSetSize -Descending | Select-Object -First 1 |
  ForEach-Object {
    "read {0:N2} GB / written {1:N2} GB" -f `
      ($_.ReadTransferCount/1GB), ($_.WriteTransferCount/1GB)
  }
"free {0:N0} GB" -f ((Get-PSDrive C).Free/1GB)
```

The three phases are distinguishable by their signatures:

| Phase | Read | Write | Tell |
| --- | --- | --- | --- |
| Downloading | high | high | free disk falling steadily |
| Resolving deltas | high | **zero** | multi-GB RAM, ~1 core busy |
| Updating files | low | high | entries appearing in the worktree |

Expect roughly 5 GB of pack for a full clone. On Windows the checkout is often
slower than the download, and real-time virus scanning makes it slower still —
excluding the checkout directory from Defender is worth doing before the
checkout phase begins, and helps every build afterwards.

## Build

```sh
python build\build.py                    # dev: full build, ~30-60 min
python build\build.py --config artifact  # frontend only, ~1-2 min
python build\build.py --run              # build, then launch
```

**`dev`** is a full local build. Branding is compiled into the binary, so this
is the configuration a rebrand needs.

**`artifact`** downloads prebuilt C++ and compiles only the frontend. This is
what makes a Gecko fork pleasant to work on: use it for chrome JavaScript, CSS
and markup. It cannot express changes to compiled code, including branding.

Each configuration has its own object directory, so switching between them
never forces a rebuild of the other.

Any other mach command can be passed through:

```sh
python build\build.py --mach package
```

## Branding assets

`branding/icon.png` is the only artwork under source control. After changing
it, regenerate the icons, tiles and installer bitmaps Firefox expects:

```sh
python build\generate_branding_assets.py
```

## Tests

The build tooling has its own tests, which run against synthetic git
repositories and need no Firefox checkout:

```sh
python build\run_tests.py
```
