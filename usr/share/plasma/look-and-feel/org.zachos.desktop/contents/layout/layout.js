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

// wallpaper kept getting dropped on reapply, just set it directly here too
var allDesktops = desktops();
for (var i = 0; i < allDesktops.length; i++) {
    var d = allDesktops[i];
    d.wallpaperPlugin = "org.kde.image";
    d.currentConfigGroup = ["Wallpaper", "org.kde.image", "General"];
    d.writeConfig("Image", "file:///usr/share/wallpapers/ZachOS/contents/images/1920x1080.png");
}
