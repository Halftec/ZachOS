#!/usr/bin/env bash
# Runs INSIDE the archlinux container, against the /profile docker volume.
# Places the hand-authored files from /profile/src-zachos into their real
# archiso paths, then does everything that needs real Linux semantics
# (symlinks, uid/gid, exec bits) which can't be done from the Windows side.
set -euo pipefail
P=/profile
A="$P/airootfs"
S="$P/src-zachos"

echo "==> Laying out ZachOS files under airootfs..."
install -d "$A/usr/lib/zachos" "$A/usr/local/bin" "$A/usr/share/zachos" \
           "$A/usr/share/applications" "$A/etc/polkit-1/rules.d" "$A/etc/pacman.d" \
           "$A/etc/pacman.d/hooks" "$A/etc/sddm.conf.d" "$A/etc/sudoers.d" "$A/etc/mkinitcpio.d" \
           "$A/etc/systemd/system/multi-user.target.wants" \
           "$A/etc/NetworkManager/conf.d" "$A/etc/xdg" "$A/etc/xdg/autostart" "$A/root" \
           "$A/usr/share/color-schemes" "$A/usr/share/wallpapers/ZachOS/contents/images" \
           "$A/usr/share/plasma/look-and-feel/org.zachos.desktop/contents/layout"

install -m 755 "$S/overlay.py"                 "$A/usr/lib/zachos/overlay.py"
install -m 755 "$S/zach_center.py"             "$A/usr/lib/zachos/zach_center.py"
install -m 755 "$S/zach-driver-rollback"       "$A/usr/lib/zachos/zach-driver-rollback"
install -m 755 "$S/zach-update-apply"          "$A/usr/lib/zachos/zach-update-apply"
install -m 755 "$S/zach-update"                "$A/usr/local/bin/zach-update"
install -m 755 "$S/zach-driver-rollback-wrapper" "$A/usr/local/bin/zach-driver-rollback"
install -m 755 "$S/zach-overlay"               "$A/usr/local/bin/zach-overlay"
install -m 755 "$S/zach-center-launcher"       "$A/usr/local/bin/zach-center"
install -m 644 "$S/driver-packages.list"       "$A/usr/share/zachos/driver-packages.list"
install -m 644 "$S/49-zachos.rules"            "$A/etc/polkit-1/rules.d/49-zachos.rules"
install -m 644 "$S/etc-pacman.conf"            "$A/etc/pacman.conf"
install -m 644 "$S/zachos-hold.conf"           "$A/etc/pacman.d/zachos-hold.conf"
install -m 755 "$S/zach-install"               "$A/usr/local/bin/zach-install"
install -m 644 "$P/packages.x86_64"            "$A/usr/share/zachos/packages.x86_64"

echo "==> Branding: ZachOS color scheme, look-and-feel, panel layout..."
install -m 644 "$S/ZachOS.colors"              "$A/usr/share/color-schemes/ZachOS.colors"
install -m 644 "$S/lookandfeel-metadata.json"  "$A/usr/share/plasma/look-and-feel/org.zachos.desktop/metadata.json"
install -m 644 "$S/lookandfeel-defaults"       "$A/usr/share/plasma/look-and-feel/org.zachos.desktop/contents/defaults"
install -m 644 "$S/layout.js"                  "$A/usr/share/plasma/look-and-feel/org.zachos.desktop/contents/layout/layout.js"
install -m 644 "$S/etc-xdg-kdeglobals"         "$A/etc/xdg/kdeglobals"
install -m 644 "$S/etc-xdg-kcminputrc"         "$A/etc/xdg/kcminputrc"
install -m 644 "$S/etc-xdg-konsolerc"          "$A/etc/xdg/konsolerc"
install -d "$A/usr/share/konsole"
install -m 644 "$S/ZachOS.colorscheme"         "$A/usr/share/konsole/ZachOS.colorscheme"
install -m 644 "$S/ZachOS.profile"             "$A/usr/share/konsole/ZachOS.profile"

echo "==> Kvantum widget theme (doesn't honor /etc/xdg, needs a real per-user copy)..."
install -d "$A/etc/skel/.config/Kvantum"
install -m 644 "$S/kvantum.kvconfig" "$A/etc/skel/.config/Kvantum/kvantum.kvconfig"
install -m 755 "$S/first-login.sh"             "$A/usr/lib/zachos/first-login.sh"
install -m 644 "$S/zachos-first-run.desktop"   "$A/etc/xdg/autostart/zachos-first-run.desktop"
install -m 644 "$S/zachos-os-release"          "$A/usr/share/zachos/os-release"
install -m 644 "$S/zachos-os-release.hook"     "$A/etc/pacman.d/hooks/zachos-os-release.hook"

echo "==> Rendering the ZachOS wallpaper (SVG -> PNG)..."
pacman -Sy --noconfirm --needed librsvg ttf-dejavu >/dev/null 2>&1 || pacman -S --noconfirm --needed librsvg ttf-dejavu >/dev/null
fc-cache -f >/dev/null 2>&1 || true
rsvg-convert -w 3840 -h 2160 "$S/wallpaper.svg" -o "$A/usr/share/wallpapers/ZachOS/contents/images/3840x2160.png"
rsvg-convert -w 1920 -h 1080 "$S/wallpaper.svg" -o "$A/usr/share/wallpapers/ZachOS/contents/images/1920x1080.png"
cat > "$A/usr/share/wallpapers/ZachOS/metadata.json" <<'EOF'
{ "KPlugin": { "Id": "ZachOS", "Name": "ZachOS", "License": "CC0" } }
EOF
install -d "$A/usr/share/pixmaps"
rsvg-convert -w 512 -h 512 "$S/logo-mark.svg" -o "$A/usr/share/pixmaps/zachos-logo.png"
rsvg-convert -w 256 -h 86 "$S/watermark.svg" -o /tmp/zachos-watermark.png

echo "==> Text-mode branding (motd, issue) so even a terminal/SSH login says ZachOS..."
# /etc/motd isn't package-owned so this is safe directly; /etc/issue IS owned
# by the filesystem package (same conflict class as plymouth's watermark, see
# below), so it goes through the os-release pacman hook instead.
install -m 644 "$S/etc-motd"  "$A/etc/motd"
install -m 644 "$S/etc-issue" "$A/usr/share/zachos/issue"
rm -f "$A/etc/issue"

echo "==> SDDM login theme (based on the stock 'maldives' theme: same battle-tested"
echo "    QML, our background/identity swapped in - not hand-rolled QML from scratch)..."
pacman -Sy --noconfirm --needed sddm plasma-workspace >/dev/null 2>&1 || \
pacman -S --noconfirm --needed sddm plasma-workspace >/dev/null
install -d "$A/usr/share/sddm/themes/zachos"
cp -a /usr/share/sddm/themes/maldives/. "$A/usr/share/sddm/themes/zachos/"
cp "$A/usr/share/wallpapers/ZachOS/contents/images/1920x1080.png" "$A/usr/share/sddm/themes/zachos/background.jpg"
sed -i \
    -e 's/^Name=.*/Name=ZachOS/' \
    -e 's/^Description=.*/Description=The default ZachOS login screen/' \
    -e 's/^Theme-Id=.*/Theme-Id=zachos/' \
    "$A/usr/share/sddm/themes/zachos/metadata.desktop"
rm -f "$A/usr/share/sddm/themes/zachos/maldives.jpg"
install -m 644 "$S/zachos-sddm-theme.conf" "$A/etc/sddm.conf.d/zachos-theme.conf"

echo "==> Plasma session-startup splash (same QML breeze ships, our logo swapped in)..."
install -d "$A/usr/share/plasma/look-and-feel/org.zachos.desktop/contents/splash/images"
SPLASH_QML="$A/usr/share/plasma/look-and-feel/org.zachos.desktop/contents/splash/Splash.qml"
cp /usr/share/plasma/look-and-feel/org.kde.breeze.desktop/contents/splash/Splash.qml "$SPLASH_QML"
cp /usr/share/plasma/look-and-feel/org.kde.breeze.desktop/contents/splash/images/busywidget.svgz \
   "$A/usr/share/plasma/look-and-feel/org.zachos.desktop/contents/splash/images/busywidget.svgz"
sed -i 's#images/plasma\.svgz#images/zachos.png#' "$SPLASH_QML"
# Strip the bottom-right "Plasma made by KDE" attribution row and its logo -
# exactly the kind of tell we don't want on our own splash screen.
sed -i '/^        Row {$/,/^        }$/d' "$SPLASH_QML"
grep -q "made by KDE" "$SPLASH_QML" && { echo "!! failed to strip KDE attribution row"; exit 1; }
rsvg-convert -w 256 -h 256 "$S/logo-mark.svg" \
    -o "$A/usr/share/plasma/look-and-feel/org.zachos.desktop/contents/splash/images/zachos.png"

echo "==> Plymouth boot splash (stock 'spinner' theme, just our watermark instead of the default one)..."
# plymouth's own package ships files at both these paths, so placing them here
# directly (before pacstrap installs plymouth) causes a file-conflict error.
# Stash them under /usr/share/zachos/ instead and let a pacman hook (below)
# drop them into place right after the plymouth package itself is installed.
install -m 644 "$S/plymouthd.conf" "$A/usr/share/zachos/plymouthd.conf"
cp /tmp/zachos-watermark.png "$A/usr/share/zachos/plymouth-watermark.png"
rm -f "$A/etc/plymouth/plymouthd.conf" "$A/usr/share/plymouth/themes/spinner/watermark.png"
cat > "$A/etc/pacman.d/hooks/zachos-plymouth.hook" <<'EOF'
[Trigger]
Operation = Install
Operation = Upgrade
Type = Package
Target = plymouth

[Action]
Description = Applying ZachOS's plymouth theme config and watermark...
When = PostTransaction
Depends = coreutils
Exec = /usr/bin/bash -c "install -d /etc/plymouth /usr/share/plymouth/themes/spinner; cp -f /usr/share/zachos/plymouthd.conf /etc/plymouth/plymouthd.conf; cp -f /usr/share/zachos/plymouth-watermark.png /usr/share/plymouth/themes/spinner/watermark.png"
EOF

echo "==> Boot silently (quiet splash) so Plymouth is what you see, not scrolling text..."
for f in "$P/syslinux/archiso_sys-linux.cfg" "$P/syslinux/archiso_pxe-linux.cfg" \
         "$P/efiboot/loader/entries/01-archiso-linux.conf" \
         "$P/efiboot/loader/entries/02-archiso-speech-linux.conf"; do
    [ -f "$f" ] && sed -i 's/\(archisosearchuuid=%ARCHISO_UUID%\)/\1 quiet splash/' "$f"
done
if [ -f "$P/grub/grub.cfg" ]; then
    sed -i 's/\(archisosearchuuid=%ARCHISO_UUID%\)/\1 quiet splash/' "$P/grub/grub.cfg"
fi

echo "==> mkinitcpio: adding the plymouth hook so it can grab the framebuffer early..."
sed -i "s/\(HOOKS=(.*\bkms\b\)/\1 plymouth/" "$A/etc/mkinitcpio.conf.d/archiso.conf"
grep -q ' plymouth ' "$A/etc/mkinitcpio.conf.d/archiso.conf" || \
  { echo "!! plymouth hook insertion failed, HOOKS line:"; grep HOOKS "$A/etc/mkinitcpio.conf.d/archiso.conf"; exit 1; }

echo "==> Branding and menu entry..."
cat > "$A/etc/hostname" <<'EOF'
zachos
EOF

cat > "$A/usr/share/applications/zach-center.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=Zach Center
Comment=Overlay levels, updates, driver rollback and app installs
Exec=/usr/local/bin/zach-center
Icon=zachos-logo
Categories=Settings;System;
Terminal=false
EOF

echo "==> Live desktop session: liveuser with autologin into Plasma..."
if ! grep -q '^liveuser:' "$A/etc/passwd" 2>/dev/null; then
    echo 'liveuser:x:1000:1000:ZachOS live session:/home/liveuser:/usr/bin/zsh' >> "$A/etc/passwd"
fi
if ! grep -q '^liveuser:' "$A/etc/group" 2>/dev/null; then
    echo 'liveuser:x:1000:' >> "$A/etc/group"
fi
for g in wheel input video audio storage optical network power lp scanner; do
    if grep -q "^${g}:" "$A/etc/group" 2>/dev/null; then
        sed -i "s/^${g}:\([^:]*\):\([^:]*\):\(.*\)$/${g}:\1:\2:\3,liveuser/;s/:,/:/" "$A/etc/group"
    fi
done
if ! grep -q '^liveuser::' "$A/etc/shadow" 2>/dev/null; then
    echo 'liveuser::14871::::::' >> "$A/etc/shadow"
fi
install -d -m 750 "$A/home/liveuser"
# liveuser is hand-appended to passwd/shadow, not made with `useradd -m`, so it
# never gets /etc/skel copied into it automatically - do it ourselves for the
# handful of per-user config files (Kvantum) that don't honor /etc/xdg.
install -d "$A/home/liveuser/.config/Kvantum"
install -m 644 "$S/kvantum.kvconfig" "$A/home/liveuser/.config/Kvantum/kvantum.kvconfig"

cat > "$A/etc/sudoers.d/liveuser" <<'EOF'
liveuser ALL=(ALL) NOPASSWD: ALL
EOF
chmod 440 "$A/etc/sudoers.d/liveuser"

cat > "$A/etc/sddm.conf.d/zachos-autologin.conf" <<'EOF'
[Autologin]
User=liveuser
Session=plasma
Relogin=true
EOF

echo "==> Networking: NetworkManager with iwd as the Wi-Fi backend..."
cat > "$A/etc/NetworkManager/conf.d/zachos-iwd.conf" <<'EOF'
[device]
wifi.backend=iwd
EOF
rm -rf "$A/etc/systemd/network" "$A/etc/systemd/system/multi-user.target.wants/systemd-networkd.service" \
       "$A/etc/systemd/system/dbus-org.freedesktop.network1.service" \
       "$A/etc/systemd/system/sockets.target.wants/systemd-networkd.socket" \
       "$A/etc/systemd/system/network-online.target.wants" \
       "$A/etc/systemd/system/cloud-init.target.wants" 2>/dev/null || true
mkdir -p "$A/etc/systemd/system/network-online.target.wants"

echo "==> A working mirror out of the box (no interactive mirror picker)..."
cat > "$A/etc/pacman.d/mirrorlist" <<'EOF'
## ZachOS - worldwide round-robin mirror (auto geo-routed), always enabled.
Server = https://geo.mirror.pkgbuild.com/$repo/os/$arch
EOF

echo "==> mkinitcpio preset for linux-zen (archiso needs its own, kernel-specific one)..."
cat > "$A/etc/mkinitcpio.d/linux-zen.preset" <<'EOF'
# mkinitcpio preset file for the 'linux-zen' package on archiso

PRESETS=('archiso')

ALL_kver='/boot/vmlinuz-linux-zen'
archiso_config='/etc/mkinitcpio.conf.d/archiso.conf'

archiso_image="/boot/initramfs-linux-zen.img"
EOF
rm -f "$A/etc/mkinitcpio.d/linux.preset"

echo "==> Enabling services (symlinks - only possible on the Linux side)..."
W="$A/etc/systemd/system/multi-user.target.wants"
ln -sf /usr/lib/systemd/system/NetworkManager.service "$W/NetworkManager.service"
ln -sf /usr/lib/systemd/system/iwd.service             "$W/iwd.service"
ln -sf /usr/lib/systemd/system/bluetooth.service       "$W/bluetooth.service"
ln -sf /usr/lib/systemd/system/sddm.service            "$W/sddm.service"
ln -sf /usr/lib/systemd/system/vmtoolsd.service         "$W/vmtoolsd.service"
ln -sf /usr/lib/systemd/system/vmware-vmblock-fuse.service "$W/vmware-vmblock-fuse.service"

echo "==> Removing archiso's interactive mirror-picker (we ship a working mirror already)..."
rm -f "$A/usr/local/bin/choose-mirror" \
      "$A/etc/systemd/system/choose-mirror.service" \
      "$A/etc/systemd/system/multi-user.target.wants/choose-mirror.service" 2>/dev/null || true

echo "==> Fixing ownership/exec bits archiso expects..."
chmod 755 "$A/usr/local/bin"/zach-* "$A/usr/lib/zachos"/zach-*
chmod 644 "$A/usr/lib/zachos"/*.py

echo "DONE"
