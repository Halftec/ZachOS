#!/usr/bin/env bash
set -u
MARKER="$HOME/.config/zachos/.first-run-done"
[[ -f "$MARKER" ]] && exit 0

for _ in $(seq 1 20); do
    pgrep -x plasmashell >/dev/null && break
    sleep 0.5
done

lookandfeeltool -a org.zachos.desktop >/dev/null 2>&1
plasma-apply-layouttemplate org.zachos.desktop >/dev/null 2>&1
# wallpaper kept not sticking from the above alone, so set it directly too
plasma-apply-wallpaperimage /usr/share/wallpapers/ZachOS/contents/images/1920x1080.png >/dev/null 2>&1

mkdir -p "$(dirname "$MARKER")"
touch "$MARKER"
