#!/usr/bin/env python3
"""Generates the ZachOS User Guide PDF."""

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, ListFlowable, ListItem, KeepTogether,
)

RED = colors.HexColor("#E31E24")
DARK = colors.HexColor("#141414")
GREY = colors.HexColor("#555555")
LIGHTBG = colors.HexColor("#F4F4F4")

styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    "ZTitle", parent=styles["Title"], fontSize=34, leading=38,
    textColor=DARK, alignment=TA_CENTER, spaceAfter=4,
)
subtitle_style = ParagraphStyle(
    "ZSubtitle", parent=styles["Normal"], fontSize=13, leading=16,
    textColor=GREY, alignment=TA_CENTER, spaceAfter=0,
)
h1 = ParagraphStyle(
    "ZH1", parent=styles["Heading1"], fontSize=19, leading=23,
    textColor=RED, spaceBefore=22, spaceAfter=10,
    borderColor=RED, borderWidth=0,
)
h2 = ParagraphStyle(
    "ZH2", parent=styles["Heading2"], fontSize=13.5, leading=17,
    textColor=DARK, spaceBefore=14, spaceAfter=6,
)
body = ParagraphStyle(
    "ZBody", parent=styles["Normal"], fontSize=10.5, leading=15.5,
    textColor=DARK, spaceAfter=6,
)
bullet = ParagraphStyle(
    "ZBullet", parent=body, leftIndent=14, spaceAfter=4,
)
code = ParagraphStyle(
    "ZCode", parent=styles["Code"], fontSize=9.7, leading=13.5,
    backColor=LIGHTBG, borderPadding=(6, 8, 6, 8), textColor=DARK,
    spaceBefore=4, spaceAfter=10,
)
caption = ParagraphStyle(
    "ZCaption", parent=styles["Normal"], fontSize=8.5, leading=11,
    textColor=GREY,
)

story = []

# ---------------------------------------------------------------- cover
story.append(Spacer(1, 2.1 * inch))
story.append(Paragraph('<font color="#E31E24">ZACH</font>OS', ParagraphStyle(
    "CoverTitle", parent=title_style, fontSize=54, leading=58)))
story.append(Paragraph("USER GUIDE", subtitle_style))
story.append(Spacer(1, 0.35 * inch))
story.append(HRFlowable(width="40%", thickness=1.4, color=RED, hAlign="CENTER"))
story.append(Spacer(1, 0.35 * inch))
story.append(Paragraph(
    "A gaming &amp; streaming desktop, ready out of the box.<br/>"
    "This guide walks through everything you'll actually use.",
    ParagraphStyle("CoverBody", parent=body, alignment=TA_CENTER, fontSize=11)))
story.append(PageBreak())

# ---------------------------------------------------------------- 1. welcome
story.append(Paragraph("1. Welcome", h1))
story.append(Paragraph(
    "ZachOS is a ready-to-go desktop for gaming and content creation. Steam, OBS, "
    "graphics drivers for AMD/Intel/Nvidia, and a full performance overlay are already "
    "installed and working - there's nothing to set up before you can play or start "
    "recording.", body))
story.append(Paragraph(
    "Everything ZachOS-specific lives in one app: <b>Zach Center</b>. It's on the taskbar "
    "and in the app launcher. The rest of this guide is basically a tour of its five tabs, "
    "plus a few keyboard shortcuts worth knowing.", body))

# ---------------------------------------------------------------- 2. desktop
story.append(Paragraph("2. The Desktop", h1))
story.append(Paragraph(
    "The bar along the bottom of the screen is the only thing you really need to know:", body))
desktop_items = [
    ("Launcher (far left)", "opens the app menu - everything installed lives here."),
    ("Pinned apps", "Files, Firefox, a terminal, Steam, and Zach Center, one click away."),
    ("System tray (right side)", "volume, network, and display icons."),
    ("Clock (far right)", "date and time."),
]
rows = [[Paragraph(f"<b>{a}</b>", body), Paragraph(b, body)] for a, b in desktop_items]
t = Table(rows, colWidths=[1.7 * inch, 4.3 * inch])
t.setStyle(TableStyle([
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ("TOPPADDING", (0, 0), (-1, -1), 0),
]))
story.append(t)

# ---------------------------------------------------------------- 3. zach center
story.append(Paragraph("3. Zach Center - Your Control Panel", h1))
story.append(Paragraph(
    "Open it from the taskbar, or run <font face=\"Courier\">zach-center</font> in a terminal. "
    "It has five tabs:", body))

story.append(Paragraph("Overlay", h2))
story.append(Paragraph(
    "The in-game performance overlay - FPS, CPU/GPU load, temperatures, and more, shown "
    "over the top of any game. Works like MSI Afterburner + RivaTuner, but built in.", body))
story.append(ListFlowable([
    ListItem(Paragraph("<b>Shift (right) + F12</b> - show or hide the overlay", bullet)),
    ListItem(Paragraph("<b>Shift (right) + F10</b> - switch to the next level", bullet)),
    ListItem(Paragraph("Pick which level a game starts on, or turn it off entirely", bullet)),
    ListItem(Paragraph("Add, duplicate, rename or delete levels - choose exactly what's shown, "
                        "where it sits on screen, the font size, and the colors", bullet)),
], bulletType="bullet", start="circle", leftIndent=14))
story.append(Paragraph(
    "Changes apply instantly, even while a game is already running - no restart needed.", body))

story.append(Paragraph("Apps", h2))
story.append(Paragraph(
    "ZachOS ships lean on purpose. Anything else - Discord, Lutris, Bottles, Blender, VLC, "
    "and more - is one click away here, or search all of Flathub directly from the search box. "
    "Apps install for your account only, need no password, and only update when you tell "
    "them to.", body))

story.append(Paragraph("Updates", h2))
story.append(Paragraph(
    "Nothing updates on its own. No surprise restarts, no background downloads. When you "
    "want to update, press <b>“Update everything now”</b> - a driver restore point is saved "
    "automatically first, just in case.", body))

story.append(Paragraph("Drivers", h2))
story.append(Paragraph(
    "Shows your graphics card and the driver currently in use. If a driver update ever causes "
    "a problem, <b>“One-click driver rollback”</b> restores the versions you had before your "
    "last update. You can also “hold” drivers so future updates skip them.", body))

story.append(Paragraph("System", h2))
story.append(Paragraph(
    "Basic info about the install, and - only when running from the USB/ISO - the "
    "<b>“Install ZachOS to disk”</b> button (see section 5).", body))

# ---------------------------------------------------------------- 4. cli
story.append(Paragraph("4. Command Line, If You Prefer", h1))
story.append(Paragraph(
    "Everything in Zach Center is also a terminal command:", body))
cli_rows = [
    [Paragraph("<font face=\"Courier\"><b>zach-center</b></font>", body), Paragraph("open the app", body)],
    [Paragraph("<font face=\"Courier\"><b>zach-overlay list</b></font>", body), Paragraph("list overlay levels", body)],
    [Paragraph("<font face=\"Courier\"><b>zach-overlay level 3</b></font>", body), Paragraph("switch to level 3 (0 = off)", body)],
    [Paragraph("<font face=\"Courier\"><b>zach-overlay next</b></font>", body), Paragraph("cycle to the next level", body)],
    [Paragraph("<font face=\"Courier\"><b>zach-update check</b></font>", body), Paragraph("see what's available, installs nothing", body)],
    [Paragraph("<font face=\"Courier\"><b>zach-update apply</b></font>", body), Paragraph("update everything (asks for your password)", body)],
    [Paragraph("<font face=\"Courier\"><b>sudo pacman -Syu</b></font>", body), Paragraph("the plain Arch way to update, if you'd rather", body)],
    [Paragraph("<font face=\"Courier\"><b>zach-driver-rollback --previous</b></font>", body), Paragraph("undo the last driver update", body)],
]
ct = Table(cli_rows, colWidths=[2.6 * inch, 3.4 * inch])
ct.setStyle(TableStyle([
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ("TOPPADDING", (0, 0), (-1, -1), 0),
    ("LINEBELOW", (0, 0), (-1, -2), 0.4, colors.HexColor("#DDDDDD")),
]))
story.append(ct)

# ---------------------------------------------------------------- 5. install
story.append(Paragraph("5. Installing ZachOS to a Real Drive", h1))
story.append(Paragraph(
    "Booting the USB/ISO gives you a fully working test drive - nothing is saved when you "
    "restart. To make it permanent:", body))
story.append(ListFlowable([
    ListItem(Paragraph("Open <b>Zach Center → System</b> and click <b>“Install ZachOS to disk.”</b> "
                        "This opens a terminal and walks you through it.", bullet)),
    ListItem(Paragraph("Pick the disk to install to. <b>Everything on it will be erased</b> - "
                        "double check you've chosen the right one.", bullet)),
    ListItem(Paragraph("Type <font face=\"Courier\">ERASE</font> to confirm, then set a hostname, "
                        "username, and password.", bullet)),
    ListItem(Paragraph("Wait for it to finish installing (this takes a while - it's downloading "
                        "and setting up the whole system).", bullet)),
    ListItem(Paragraph("When it says it's done, remove the USB and restart.", bullet)),
], bulletType="1", leftIndent=14))
story.append(Paragraph(
    "The installed system asks for your password to log in and to run anything as "
    "administrator - unlike the test USB, which skips both for convenience.", body))

# ---------------------------------------------------------------- 6. gaming/streaming
story.append(Paragraph("6. Gaming &amp; Streaming", h1))
story.append(ListFlowable([
    ListItem(Paragraph("<b>Steam</b> is already installed and on the taskbar - sign in and play. "
                        "Proton (for Windows games) works out of the box.", bullet)),
    ListItem(Paragraph("<b>OBS Studio</b> is installed for recording or streaming.", bullet)),
    ListItem(Paragraph("The performance overlay (section 3) works automatically with any game - "
                        "nothing to configure per-game.", bullet)),
    ListItem(Paragraph("Need something not already installed? Check the <b>Apps</b> tab first, "
                        "or search Flathub directly from there.", bullet)),
], bulletType="bullet", leftIndent=14))

# ---------------------------------------------------------------- 7. good to know
story.append(Paragraph("7. Good to Know", h1))
story.append(ListFlowable([
    ListItem(Paragraph("Nothing updates, installs, or restarts without you asking it to. "
                        "That's the whole point of the Updates tab.", bullet)),
    ListItem(Paragraph("A driver restore point is saved automatically before every update, so "
                        "a bad driver is always one click away from being undone.", bullet)),
    ListItem(Paragraph("Apps from the Apps tab are sandboxed - they can't affect the base system, "
                        "and removing one is as clean as installing it.", bullet)),
    ListItem(Paragraph("If something ever looks wrong, open a terminal (Konsole, on the taskbar) "
                        "and run the app by name to see what it prints - that's almost always "
                        "the fastest way to figure out what happened.", bullet)),
], bulletType="bullet", leftIndent=14))

story.append(Spacer(1, 0.4 * inch))
story.append(HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#DDDDDD")))
story.append(Spacer(1, 0.15 * inch))
story.append(Paragraph("ZachOS - built on Arch Linux, tuned for gaming and streaming.", caption))


def build(path):
    doc = SimpleDocTemplate(
        path, pagesize=letter,
        leftMargin=0.85 * inch, rightMargin=0.85 * inch,
        topMargin=0.8 * inch, bottomMargin=0.8 * inch,
        title="ZachOS User Guide",
    )
    doc.build(story)


if __name__ == "__main__":
    build("ZachOS-User-Guide.pdf")
    print("done")
