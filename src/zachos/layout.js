// ZachOS default panel: one slim bottom bar, minimal widgets, nothing extra.
// Applied on first login via the org.zachos.desktop look-and-feel package,
// and re-applied by /usr/lib/zachos/first-login.sh via `plasma-apply-layouttemplate`.

var panel = new Panel;
panel.location = "bottom";
panel.height = 44;
panel.alignment = "center";
panel.lengthMode = "fill";

var launcher = panel.addWidget("org.kde.plasma.kickoff");
launcher.currentConfigGroup = ["General"];
launcher.writeConfig("icon", "zachos-logo");

var tasks = panel.addWidget("org.kde.plasma.icontasks");
tasks.currentConfigGroup = ["General"];
tasks.writeConfig("launchers", [
    "applications:org.kde.dolphin.desktop",
    "applications:org.mozilla.firefox.desktop",
    "applications:org.kde.konsole.desktop",
    "applications:steam.desktop",
    "applications:zach-center.desktop"
]);
tasks.writeConfig("showOnlyCurrentDesktop", false);
tasks.writeConfig("showOnlyCurrentActivity", false);
tasks.writeConfig("groupingStrategy", 0);

panel.addWidget("org.kde.plasma.panelspacer");

var tray = panel.addWidget("org.kde.plasma.systemtray");

var clock = panel.addWidget("org.kde.plasma.digitalclock");
clock.currentConfigGroup = ["Appearance"];
clock.writeConfig("showSeconds", "false");
clock.writeConfig("dateFormat", "shortDate");

// Applying the layout template rebuilds containments, which can drop the
// wallpaper the look-and-feel defaults set - so set it here too, explicitly,
// on every desktop, rather than relying on that first-run-only mechanism.
var allDesktops = desktops();
for (var i = 0; i < allDesktops.length; i++) {
    var d = allDesktops[i];
    d.wallpaperPlugin = "org.kde.image";
    d.currentConfigGroup = ["Wallpaper", "org.kde.image", "General"];
    d.writeConfig("Image", "file:///usr/share/wallpapers/ZachOS/contents/images/1920x1080.png");
}
