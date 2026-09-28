#!/usr/bin/env bash
# Headless boot-test for a built ZachOS ISO: boots it under QEMU (software
# emulation, no KVM needed) with the kernel's own console mirrored to stdout,
# so you get the full boot log without needing a graphical display. Useful
# for catching a broken mkinitcpio/boot-parameter change before handing the
# ISO to anyone.
#
# Usage: qemu-boot.sh /path/to/zachos.iso [seconds to run, default 150]
#
# Run this from inside a container that already has the ISO bind-mounted at
# /iso and a scratch volume at /work, e.g.:
#   docker run --rm --privileged -v "$PWD/output:/iso:ro" -v zachos-qemu:/work \
#     archlinux:latest bash -c 'pacman -Sy --noconfirm --needed qemu-base; \
#     bash src/build/qemu-boot.sh /iso/zachos-*.iso'
set -euo pipefail

ISO=${1:?usage: qemu-boot.sh /path/to/zachos.iso [seconds]}
RUN_SECONDS=${2:-150}
WORK=/work/extracted

mkdir -p /mnt/iso "$WORK"
mount -o loop,ro "$ISO" /mnt/iso
cp -f /mnt/iso/zachos/boot/x86_64/vmlinuz-linux-zen "$WORK/"
cp -f /mnt/iso/zachos/boot/x86_64/initramfs-linux-zen.img "$WORK/"
UUID=$(blkid -o value -s UUID "$ISO")
umount /mnt/iso

qemu-system-x86_64 \
  -m 4096 -smp 2 -accel tcg \
  -kernel "$WORK/vmlinuz-linux-zen" \
  -initrd "$WORK/initramfs-linux-zen.img" \
  -append "archisobasedir=zachos archisosearchuuid=$UUID console=ttyS0,115200n8 systemd.mask=systemd-time-wait-sync.service systemd.mask=systemd-timesyncd.service" \
  -cdrom "$ISO" \
  -serial stdio -display none -no-reboot \
  -netdev user,id=n0 -device virtio-net-pci,netdev=n0 &
QEMU_PID=$!
sleep "$RUN_SECONDS"
kill -9 "$QEMU_PID" 2>/dev/null || true
