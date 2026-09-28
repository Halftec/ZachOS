#!/usr/bin/env bash
# Forces the ZachOS look-and-feel + panel layout onto a session once, the
# first time it logs in. Belt-and-suspenders alongside the LookAndFeelPackage
# default in kdeglobals - if Plasma's own first-run detection doesn't apply
# it for some reason, this makes sure it happens anyway.
set -u
MARKER="$HOME/.config/zachos/.first-run-done"
[[ -f "$MARKER" ]] && exit 0

# Give plasmashell a moment to finish starting before we touch it.
for _ in $(seq 1 20); do
    pgrep -x plasmashell >/dev/null && break
    sleep 0.5
done

lookandfeeltool -a org.zachos.desktop >/dev/null 2>&1
plasma-apply-layouttemplate org.zachos.desktop >/dev/null 2>&1

mkdir -p "$(dirname "$MARKER")"
touch "$MARKER"
