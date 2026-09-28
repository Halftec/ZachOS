#!/usr/bin/env bash
# shellcheck disable=SC2034

iso_name="zachos"
iso_label="ZACHOS_$(date --date="@${SOURCE_DATE_EPOCH:-$(date +%s)}" +%Y%m)"
iso_publisher="ZachOS <https://example.invalid>"
iso_application="ZachOS Live/Install Medium"
iso_version="$(date --date="@${SOURCE_DATE_EPOCH:-$(date +%s)}" +%Y.%m.%d)"
install_dir="zachos"
buildmodes=('iso')
bootmodes=('bios.syslinux' 'uefi.systemd-boot')
pacman_conf="pacman.conf"
airootfs_image_type="squashfs"
airootfs_image_tool_options=('-comp' 'xz' '-Xbcj' 'x86' '-b' '1M' '-Xdict-size' '1M')
bootstrap_tarball_compression=('zstd' '-c' '-T0' '--auto-threads=logical' '--long' '-19')
file_permissions=(
  ["/etc/shadow"]="0:0:400"
  ["/etc/sudoers.d"]="0:0:750"
  ["/etc/sudoers.d/liveuser"]="0:0:440"
  ["/root"]="0:0:750"
  ["/root/.automated_script.sh"]="0:0:755"
  ["/root/.gnupg"]="0:0:700"
  ["/home/liveuser/"]="1000:1000:750"
  ["/usr/local/bin/Installation_guide"]="0:0:755"
  ["/usr/local/bin/livecd-sound"]="0:0:755"
  ["/usr/local/bin/zach-update"]="0:0:755"
  ["/usr/local/bin/zach-driver-rollback"]="0:0:755"
  ["/usr/local/bin/zach-overlay"]="0:0:755"
  ["/usr/local/bin/zach-center"]="0:0:755"
  ["/usr/local/bin/zach-install"]="0:0:755"
  ["/usr/lib/zachos/zach-driver-rollback"]="0:0:755"
  ["/usr/lib/zachos/zach-update-apply"]="0:0:755"
)
