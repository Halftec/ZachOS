# ZachOS

A gaming and streaming desktop built on Arch Linux. Boots straight into a working
KDE Plasma setup with drivers for AMD, Intel and Nvidia, Steam, Wine/Proton, OBS,
and a performance overlay already in place - no post-install setup required.

## What makes it different from stock Arch

- **Zach Center** - one app for the overlay, updates, driver rollback, and app installs
- **In-game overlay** - SteamOS-style FPS/performance levels, fully customizable,
  toggled with a hotkey
- **Update lock** - nothing updates, installs a driver, or restarts on its own;
  updates only happen when you press the button, and a driver restore point is
  saved automatically first
- **One-click driver rollback** - undo a bad driver update, or pin drivers so
  updates skip them
- **Curated app installs** - a one-click Flatpak catalog (Discord, Lutris,
  Blender, VLC, etc.) kept separate from the base system
- **Its own look** - custom wallpaper, panel layout, icon/cursor theme, widget
  style, boot splash and login screen, instead of a stock desktop

## Building the ISO

Requires Docker. From the repo root:

```bash
./build.sh
```

This pulls the upstream `archiso` releng profile, applies everything in
`profile/` and `src/`, and builds the ISO with `mkarchiso` inside a container -
no local Arch install needed. Takes 15-30 minutes depending on network speed.
The finished ISO lands in `output/`.

## Testing it

Boot the ISO in a VM (VirtualBox, VMware, or QEMU) with UEFI firmware enabled,
8GB+ RAM, and 3D acceleration turned on. It boots straight to a Plasma desktop
with an autologin session for quick testing - no username or password needed.

To install it to a real disk instead of just testing the live session, open
**Zach Center -> System -> Install ZachOS to disk**, or run `zach-install`
directly. This wipes whichever disk you point it at, so double-check the
target before confirming.

See `docs/ZachOS-User-Guide.pdf` for a full walkthrough of the desktop, Zach
Center's tabs, and the equivalent terminal commands.

## Repository layout

```
build.sh        one-command build (see above)
profile/         package list and pacman.conf for the ISO
src/zachos/      ZachOS-specific source: Zach Center, the overlay tool, the
                 driver-rollback/update scripts, branding assets
src/build/       build-time helpers: finalize.sh (places everything and
                 applies branding), profiledef.sh, a headless-QEMU boot-test
                 script, and the PDF guide generator
docs/            the user guide (PDF)
```

The rest of the profile (boot loader configuration, base airootfs skeleton)
comes from upstream `archiso`'s releng profile at build time rather than being
vendored here, so `build.sh` is always building against a current base.
