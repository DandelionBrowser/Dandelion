# Building Dandelion

Dandelion builds from Chromium source with GN and Ninja. Expect the first build
to take hours; incremental builds after it take minutes.

## Requirements

| | |
| --- | --- |
| Disk | ~100 GB checkout + ~60 GB per build configuration |
| RAM | 16 GB minimum, 32 GB recommended |
| OS | Windows 10/11 x64 (macOS and Linux are not yet wired up) |

### Windows

1. **Visual Studio 2022 or 2026** with the *Desktop development with C++*
   workload, plus the **C++ ATL** and **C++ MFC** components. Build Tools
   editions are sufficient — the full IDE is not required.
2. **Windows SDK 10.0.26100.0** exactly. Chromium pins this version in
   `build/vs_toolchain.py`; other versions are rejected.
3. **Debugging Tools for Windows**. Chromium requires `dbghelp.dll` from
   `<SDK>\Debuggers\x64` and fails the build without it. The SDK installed via
   the Visual Studio installer omits this, so install it from the standalone
   [Windows SDK installer](https://developer.microsoft.com/en-us/windows/downloads/windows-sdk/):

   ```sh
   winsdksetup.exe /features OptionId.WindowsDesktopDebuggers
   ```

4. **depot_tools**, cloned with full history (a shallow clone breaks its
   self-update) and added to `PATH`:

   ```sh
   git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git C:\src\depot_tools
   ```

5. **Long paths enabled**, or the checkout will fail on deeply nested files:

   ```sh
   reg add HKLM\SYSTEM\CurrentControlSet\Control\FileSystem /v LongPathsEnabled /t REG_DWORD /d 1 /f
   ```

### Environment

```sh
setx DEPOT_TOOLS_WIN_TOOLCHAIN 0
```

`DEPOT_TOOLS_WIN_TOOLCHAIN=0` tells depot_tools to use your local Visual Studio
rather than Google's internal packaged toolchain, which is unavailable outside
Google.

Chromium locates Visual Studio 2026 under `%ProgramFiles%\Microsoft Visual
Studio\18`. If yours installed elsewhere — the Build Tools edition commonly
lands in `Program Files (x86)` — point Chromium at it explicitly, otherwise
detection fails:

```sh
setx vs2026_install "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools"
```

Verify detection before starting a checkout:

```sh
python <chromium>\build\vs_toolchain.py get_toolchain_dir
```

## Checkout

```sh
python build/sync.py
```

This fetches Chromium at the version pinned in `CHROMIUM_VERSION`, mounts this
repository into it as `src/dandelion`, and applies Dandelion's patches. The
checkout defaults to `C:\src\chromium`; override it with
`DANDELION_CHROMIUM_ROOT`.

The path is deliberately short. Several tools in the Chromium build still break
on long paths even with `LongPathsEnabled` set.

The first checkout downloads roughly 100 GB and takes hours. It is safe to
re-run: an interrupted sync resumes, and a partial checkout is repaired rather
than restarted. Capture the output, because a failure hours in is otherwise
invisible:

```sh
python build\sync.py --no-hooks 2>&1 | Tee-Object sync.log
```

`--no-hooks` skips the toolchain setup step, so the download can run before
Visual Studio's ATL/MFC components and the Debugging Tools are installed. Run
`gclient runhooks` in the checkout afterwards to complete it.

Chromium is fetched at tip-of-tree and then moved to the pinned release tag, so
dependencies are synced twice. This is the flow Chromium's own release-branch
instructions prescribe; the second pass is mostly local checkouts.

Note that the environment variables above are only picked up by shells started
after they were set. Open a new terminal before running the checkout.

## Tests

The build tooling has its own tests, which run against synthetic git
repositories and need neither depot_tools nor a Chromium checkout:

```sh
python build/run_tests.py
```

## Build

```sh
python build/build.py                     # dev config, chrome target
python build/build.py --config release
python build/build.py --target unit_tests
```

`dev` is a component build with DCHECKs on — the configuration to develop
against. `release` is the shipping configuration: official, statically linked
and profile-guided, and far slower to build.

To override GN arguments locally without modifying tracked files, create
`build/args/local.gn`. It is appended to the generated `args.gn` and is ignored
by git.

## Running

```sh
C:\src\chromium\src\out\dev\chrome.exe --user-data-dir=C:\src\dandelion-profile
```

Always pass `--user-data-dir` so that development runs cannot corrupt a real
browser profile.
