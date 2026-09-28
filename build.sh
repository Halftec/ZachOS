#!/usr/bin/env bash
# Builds the ZachOS ISO from scratch, using Docker so it works the same way
# on any host (no local Arch install or archiso package needed).
#
# Pipeline:
#   1. Seed a scratch volume with the upstream archiso 'releng' profile
#      (syslinux/grub/EFI boot chrome, base airootfs skeleton).
#   2. Overlay this repo's own packages.x86_64 / pacman.conf / profiledef.sh.
#   3. Copy in src/zachos (the ZachOS-specific files) and run finalize.sh,
#      which places everything, brands the boot/login/desktop, and wires up
#      the update lock and driver rollback.
#   4. Run mkarchiso against the assembled profile.
#   5. Copy the finished .iso out to ./output/.
#
# Requires: Docker, with enough free disk space for ~9GB of packages plus
# the squashfs build (~15GB scratch space recommended). Takes 15-30 minutes
# depending on network speed and CPU.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

PROFILE_VOL=zachos-profile
WORK_VOL=zachos-work
OUT_VOL=zachos-out
IMAGE=archlinux:latest

echo "==> Resetting scratch volumes..."
docker rm -f zachos-build >/dev/null 2>&1 || true
for v in "$PROFILE_VOL" "$WORK_VOL" "$OUT_VOL"; do
    docker volume rm "$v" >/dev/null 2>&1 || true
    docker volume create "$v" >/dev/null
done

echo "==> Seeding the profile with the upstream archiso releng skeleton..."
docker run --rm -v "$PROFILE_VOL":/profile "$IMAGE" bash -c '
    pacman -Sy --noconfirm archiso >/dev/null
    cp -a /usr/share/archiso/configs/releng/. /profile/
'

echo "==> Copying this repo's overrides and source files into the profile..."
docker create --name zachos-seed -v "$PROFILE_VOL":/profile "$IMAGE" true >/dev/null
docker cp profile/packages.x86_64        zachos-seed:/profile/packages.x86_64
docker cp profile/pacman.conf            zachos-seed:/profile/pacman.conf
docker cp src/build/profiledef.sh        zachos-seed:/profile/profiledef.sh
docker cp src/build/finalize.sh          zachos-seed:/profile/finalize.sh
docker cp src/zachos/.                   zachos-seed:/profile/src-zachos/
docker rm -f zachos-seed >/dev/null

echo "==> Running finalize.sh (branding, boot splash, services, hooks)..."
docker run --rm -v "$PROFILE_VOL":/profile "$IMAGE" bash /profile/finalize.sh

echo "==> Sanity-checking the boot-config edits for linux-zen + quiet/splash..."
docker run --rm -v "$PROFILE_VOL":/profile "$IMAGE" bash -c '
    grep -q "vmlinuz-linux-zen" /profile/syslinux/archiso_sys-linux.cfg
    grep -q plymouth /profile/airootfs/etc/mkinitcpio.conf.d/archiso.conf
'

echo "==> Building the ISO with mkarchiso (this is the slow part)..."
docker run --rm --privileged --name zachos-build \
    -v "$PROFILE_VOL":/profile -v "$OUT_VOL":/out -v "$WORK_VOL":/work \
    "$IMAGE" bash -c '
        set -e
        pacman -Sy --noconfirm archiso >/dev/null
        mkarchiso -v -w /work -o /out /profile
    '

echo "==> Copying the finished ISO out to ./output/..."
mkdir -p output
docker create --name zachos-fetch -v "$OUT_VOL":/out "$IMAGE" true >/dev/null
ISO_NAME=$(docker run --rm -v "$OUT_VOL":/out "$IMAGE" bash -c 'ls /out/*.iso' | xargs basename)
docker cp "zachos-fetch:/out/$ISO_NAME" "output/$ISO_NAME"
docker rm -f zachos-fetch >/dev/null

echo
echo "Done: output/$ISO_NAME"
