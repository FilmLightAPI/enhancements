# Packaging and distributing an effect

## What each machine needs

Every machine that renders the effect, the UI host and each render node, needs:

- **Baselight or Daylight 7.0.3 or later**, with FilmLight's Flexi effects installed. They bring
  the shared Flexi platforms (`pytorch-2.8`, and `pytorch-2.2` on Intel Macs) that Python effects
  are built on. Check with `ls "<flexi dir>/platforms"`.
- **Python 3.12**: the python.org framework build on macOS
  (`/Library/Frameworks/Python.framework`), `/usr/bin/python3.12` on Linux. Effect venvs, packaged
  ones included, run this Python; the Flexi platforms need it too, so it is present wherever
  FilmLight's Flexi effects run.
- **A supported GPU**: NVIDIA with a driver recent enough for the platform's CUDA (`pytorch-2.8`
  uses CUDA 12.8, driver 570 or later) on Linux; Apple silicon or a Metal GPU on macOS. Baselight
  turns Flexi off on GPUs with less than 16 GB of VRAM (Linux, Intel Macs), and on Apple silicon
  with less than 24 GB of unified memory.
- **Anything else the effect runs**: an effect in another language needs its runtime (Node.js,
  etc.) on every machine, or bundled with the effect.
- **The Flexi licence options** on the Baselight licence.

`<flexi dir>` is `/vol/.support/flexi`: on macOS a link to `/Library/Application Support/FilmLight/flexi`,
on Linux the same folder as `/usr/fl/flexi`.

## One package per platform

A prepared effect contains a Python venv built for one OS and CPU, and linked to that machine's
platform. Build and test a package on each platform you support, on that platform:

| Platform | Manifest section | Flexi platform | Build on |
|---|---|---|---|
| Linux, NVIDIA | `linux` | `pytorch-2.8` | a Linux render node or workstation |
| macOS, Apple silicon | `macos` | `pytorch-2.8` | an Apple silicon Mac |
| macOS, Intel | `macos-intel` | `pytorch-2.2` | an Intel Mac |

Intel Macs need their own section because PyTorch stopped publishing Intel Mac builds after 2.2:
pin package versions that still support PyTorch 2.2 and NumPy 1.26 there, and avoid features
missing from that PyTorch on MPS (antialiased `interpolate`, `area` resizes with uneven ratios).

## Native binaries

An effect that is, or runs, a compiled program (`examples/cpp-invert`, or a tool wrapped as in
`examples/run-tool`) has more to get right than a Python one:

- **macOS: one universal binary.** Build with `-arch arm64 -arch x86_64` and a deployment target
  (`-mmacosx-version-min=11.0`): one file then runs on Apple silicon and Intel Macs. Check with
  `lipo -archs <binary>`.
- **Linux: build on the oldest distribution you support.** A binary needs the glibc it was built
  against or newer: one built on Ubuntu 22.04 needs glibc 2.34 and does not start on Rocky Linux 8
  (2.28). Check what it needs with
  `objdump -T <binary> | grep -o 'GLIBC_[0-9.]*' | sort -uV | tail -1`. Link the C++ runtime
  statically (`-static-libstdc++ -static-libgcc`) so glibc is the only system library left.
- **Bundle the libraries it needs**, in the effect folder, and point the binary at them:
  `-Wl,-rpath,@executable_path/lib` on macOS, `-Wl,-rpath,'$ORIGIN/lib'` on Linux. `otool -L` and
  `ldd` should list nothing outside the system and the effect folder.
- **List the binary in the manifest's `sources`** and launch it by a relative path
  (`"launch_command": "./my_effect"`). The installer keeps its executable bit.
- **Sign it on macOS** before packaging: see the next section.

## Building a package

On each platform, from the folder with the `.flexi` file, its sources and weights. `FLEXI_DIR` is
the Flexi directory and `PLATFORM` the platform the manifest names for this machine:

```bash
mkdir -p platforms dist
cp "$FLEXI_DIR/platforms/$PLATFORM/$PLATFORM.flexiplatform" platforms/
# Use the installed platform rather than building a copy
mkdir -p dist/platform_scratch && ln -s "$FLEXI_DIR/platforms/$PLATFORM" dist/platform_scratch/$PLATFORM

fl-make-flexi-package --version 1.2.0 --targetdir "$PWD/dist/my_effect-1.2.0" \
    my_effect com.yourstudio.my_effect.v1.flexi
```

This prepares the effect in `--targetdir`: `effects/com.yourstudio.my_effect.v1/` (named after
the `.flexi` file) with sources,
weights, a venv and a `VERSION` file. The venv's helper scripts still name the build folder, so
point them at the install location, drop compiled Python files, and make the package. On macOS
use `/vol/.support/flexi`, the same folder by a path without a space (script `#!` lines cannot
contain one); on Linux use `/usr/fl/flexi`:

```bash
T="$PWD/dist/my_effect-1.2.0"
RELOCATE=/vol/.support/flexi
find "$T" -name '*.pyc' -delete
grep -rlIF "$T" "$T" | while IFS= read -r f; do perl -pi -e "s|\Q$T\E|$RELOCATE|g" "$f"; done

# macOS: an installer package
pkgbuild --root "$T" --install-location "$FLEXI_DIR" \
    --identifier com.yourstudio.my_effect --version 1.2.0 [--sign "Developer ID Installer: …"] \
    dist/my_effect-1.2.0-macos-arm64.pkg
# Linux (or macOS): a tarball, installed with  sudo tar -xzf my_effect.tar.gz -C "$FLEXI_DIR"
tar -C "$T" -czf dist/my_effect-1.2.0-linux.tar.gz effects
```

Name each package for its platform (`-linux`, `-macos-arm64`, `-macos-intel`): a package for the
wrong one installs without complaint and then fails to start.

The package contains the effect only. The Flexi platform it names must already be installed by
FilmLight's Flexi effects on the target machine.

## Signing and notarization (macOS)

FilmLight signs and notarizes the packages it publishes. **A package you build is not covered by
that.** Decide how your users will install it:

- **Signed and notarized** (recommended for anything you send out): sign with your own Apple
  *Developer ID Installer* certificate (`--sign`), then notarize with your Apple developer account
  and staple the ticket:

  ```bash
  xcrun notarytool submit my_effect.pkg --keychain-profile <profile> --wait
  xcrun stapler staple my_effect.pkg
  ```

  The package then installs with a double-click like any other.
- **Unsigned**: fine inside your own facility. A downloaded unsigned package is blocked by
  Gatekeeper on double-click; install it with `sudo installer -pkg my_effect.pkg -target /`, or
  right-click → Open. Tell your users which to expect.

**Notarization checks every binary inside the package**, not only the package: executables,
`.dylib` and `.so` files, including compiled Python packages in the effect's venv. Each must be
signed with your *Developer ID Application* certificate (a different certificate from the
*Installer* one), with the hardened runtime and a timestamp, before you run `pkgbuild`:

```bash
find "$T" -type f \( -perm -u+x -o -name '*.so' -o -name '*.dylib' \) -exec sh -c \
    'file "$1" | grep -q Mach-O && codesign --force --options runtime --timestamp \
     --sign "Developer ID Application: …" "$1"' _ {} \;
```

The python.org Python that effect venvs run accepts libraries signed by your team.

A binary unpacked from a downloaded `.tar.gz` keeps the download's quarantine flag, and macOS
can refuse to run an unsigned one. For tarballs, sign the binaries the same way, or have users
clear the flag after unpacking: `sudo xattr -dr com.apple.quarantine "$FLEXI_DIR/effects/<effect>"`.

## Installing and updating

- Install: the `.pkg`, the tarball, or on a machine with the source folder
  `fl-install-flexi-effect -t <flexi dir> com.yourstudio.my_effect.v1.flexi`. On a system
  with a separate UI host, run `fl-install-flexi-effect` and `fl-flexi` on the node: they refuse
  to run on the UI host.
- Check: `fl-flexi check com.yourstudio.my_effect --full` (fl-diag runs the same tests and a
  few more: `references/testing.md`, step 8), then restart Baselight.
- List what is installed: `fl-flexi` prints every installed effect with its version, package
  build, platform and folder.
- Before moving a scene that uses the effect to another machine or site:
  `fl-flexi scene <host:job:scene> --check` lists the Flexi effects the scene needs, how often
  each is used, and whether each is installed and intact on this machine.
- Find it: `filter` effects are in the layer operator list and the Flexi Effect strip, `source`
  effects in Flexi Source, `multi_input` effects in the Flexi Effect strip only. When several
  versions are installed, Baselight lists only the newest unless the user turns off
  "hide older versions".
- Update the same version in place for fixes that do not change params or results.
- Bump `version` in the manifest (`my_effect.v2.flexi`) when params change or results change
  visibly, and install it beside v1: scenes graded with v1 keep using v1.
- Remove with `fl-flexi remove com.yourstudio.my_effect=1`.

## The `download` field

`"download": {"web_page": …, "web_instructions": …}` in the manifest's `install` section
(`all`, `linux` or `macos`) gives users who open a scene
without your effect a link to get it, in Baselight's "effect not installed" dialog. It only works
on machines that have the bare `.flexi` file in the Flexi directory itself (not under `effects/`).
