import os
import re
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import QProcess, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen, QLinearGradient
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QColorDialog, QComboBox, QDoubleSpinBox, QFormLayout,
    QGridLayout, QGroupBox, QHBoxLayout, QHeaderView, QInputDialog, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QMainWindow, QMessageBox, QPlainTextEdit, QPushButton,
    QSpinBox, QSplitter, QTabWidget, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import overlay  # noqa: E402

LIB = "/usr/lib/zachos"
STATE_DIR = Path("/var/lib/zachos")
HISTORY_DIR = STATE_DIR / "driver-history"
HOLD_CONF = Path("/etc/pacman.d/zachos-hold.conf")
DRIVER_LIST = Path("/usr/share/zachos/driver-packages.list")
IS_LIVE = Path("/run/archiso").exists()

ACCENT = "#e31e24"
STYLE = f"""
QWidget {{ background: #12141a; color: #e6e9ef; font-size: 10.5pt; }}
QTabWidget::pane {{ border: 1px solid #262a35; border-radius: 6px; top: -1px; }}
QTabBar::tab {{ background: #1a1d25; padding: 9px 22px; margin-right: 2px;
               border-top-left-radius: 6px; border-top-right-radius: 6px; }}
QTabBar::tab:selected {{ background: #232734; color: {ACCENT}; font-weight: bold; }}
QGroupBox {{ border: 1px solid #262a35; border-radius: 6px; margin-top: 14px; padding-top: 8px; }}
QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 4px; color: {ACCENT}; }}
QPushButton {{ background: #232734; border: 1px solid #323848; border-radius: 5px; padding: 6px 14px; }}
QPushButton:hover {{ border-color: {ACCENT}; }}
QPushButton:disabled {{ color: #5c6273; }}
QPushButton#primary {{ background: {ACCENT}; color: #06121a; font-weight: bold; border: none; }}
QPushButton#danger {{ background: #ff4d6a; color: #1a0508; font-weight: bold; border: none; }}
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QPlainTextEdit, QListWidget, QTreeWidget {{
    background: #1a1d25; border: 1px solid #2c3140; border-radius: 4px; padding: 3px; }}
QListWidget::item:selected, QTreeWidget::item:selected {{ background: #5c1418; }}
QHeaderView::section {{ background: #1a1d25; border: none; padding: 5px; color: #9aa3b5; }}
QLabel#banner {{ font-size: 13pt; font-weight: bold; padding: 10px; border-radius: 6px; }}
QLabel#muted {{ color: #8a92a6; }}
"""


def run(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=30).stdout
    except (OSError, subprocess.TimeoutExpired):
        return ""


def driver_packages():
    try:
        lines = DRIVER_LIST.read_text().splitlines()
    except OSError:
        return []
    return [l.strip() for l in lines if l.strip() and not l.startswith("#")]


def installed_versions(pkgs):
    out = run(["pacman", "-Q", *pkgs]) if pkgs else ""
    return dict(line.split(None, 1) for line in out.splitlines() if " " in line)


class ProcessLog(QPlainTextEdit):
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.setFont(QFont("monospace", 9))
        self.proc = None
        self.on_done = None

    def start(self, program, args, on_done=None):
        if self.proc and self.proc.state() != QProcess.NotRunning:
            QMessageBox.information(self, "Busy", "Another task is still running.")
            return False
        self.clear()
        self.on_done = on_done
        self.proc = QProcess(self)
        self.proc.setProcessChannelMode(QProcess.MergedChannels)
        self.proc.readyReadStandardOutput.connect(self._read)
        self.proc.finished.connect(self._finished)
        self.proc.start(program, args)
        return True

    def busy(self):
        return self.proc is not None and self.proc.state() != QProcess.NotRunning

    def _read(self):
        text = bytes(self.proc.readAllStandardOutput()).decode(errors="replace")
        self.moveCursor(self.textCursor().MoveOperation.End)
        self.insertPlainText(text)
        self.ensureCursorVisible()

    def _finished(self, code, _status):
        if code == 126 or code == 127:
            self.appendPlainText("\n(cancelled - administrator password was not given)")
        if self.on_done:
            self.on_done(code)



SAMPLE = {
    "gpu_stats": "87%", "gpu_temp": "71C", "gpu_junction_temp": "84C", "gpu_mem_temp": "76C",
    "gpu_power": "212W", "gpu_core_clock": "2610MHz", "gpu_mem_clock": "1250MHz",
    "gpu_fan": "46%", "cpu_stats": "32%", "cpu_temp": "61C", "cpu_power": "68W",
    "cpu_mhz": "4850MHz",
}


def preview_rows(lvl):
    on = set(lvl["metrics"])
    rows = []
    if "gpu_name" in on:
        rows.append(("", "Radeon RX 7800 XT"))
    gpu = [SAMPLE[k] for k in ("gpu_stats", *sorted(overlay.GPU_ROW, key=list(SAMPLE).index)) if k in on]
    if gpu:
        rows.append(("GPU", " ".join(gpu)))
    cpu = [SAMPLE[k] for k in ("cpu_stats", "cpu_temp", "cpu_power", "cpu_mhz") if k in on]
    if cpu:
        rows.append(("CPU", " ".join(cpu)))
    if "core_load" in on:
        rows += [(f"CPU{i}", f"{p}% 4.8GHz") for i, p in enumerate((41, 27, 63, 18))]
    for key, label, value in (
        ("vram", "VRAM", "6.2 GiB"), ("ram", "RAM", "11.4 GiB"), ("swap", "SWAP", "0.3 GiB"),
        ("procmem", "MEM", "3.1 GiB"), ("io_read", "READ", "12 MiB/s"),
        ("io_write", "WRITE", "3 MiB/s"), ("battery", "BATT", "84%"),
    ):
        if key in on:
            rows.append((label, value))
    fps = []
    if "fps" in on:
        fps.append("144 FPS")
    if "frametime" in on:
        fps.append("6.9 ms")
    if fps:
        rows.append(("", "  ".join(fps)))
    if "lows" in on:
        rows.append(("LOWS", "1% 118  0.1% 96"))
    for key, label, value in (
        ("show_fps_limit", "LIMIT", "165"), ("vulkan_driver", "DRIVER", "Mesa 26.1"),
        ("engine_version", "API", "DXVK 2.7"), ("wine", "WINE", "Proton 10.0"),
        ("resolution", "RES", "2560x1440"), ("gamemode", "GAMEMODE", "ON"),
        ("fsr", "FSR", "OFF"), ("hdr", "HDR", "OFF"), ("throttling_status", "THROTTLE", "none"),
        ("time", "TIME", "21:37"),
    ):
        if key in on:
            rows.append((label, value))
    return rows


class OverlayPreview(QWidget):
    def __init__(self):
        super().__init__()
        self.level = None
        self.setMinimumHeight(220)

    def show_level(self, lvl):
        self.level = lvl
        self.update()

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w = self.width()
        h = min(self.height(), int(w * 9 / 16))
        w = int(h * 16 / 9)
        x0 = (self.width() - w) // 2
        screen = QRectF(x0, 0, w, h)
        grad = QLinearGradient(screen.topLeft(), screen.bottomRight())
        grad.setColorAt(0, QColor("#2a1013"))
        grad.setColorAt(1, QColor("#1a1a1a"))
        p.fillRect(screen, grad)
        p.setPen(QColor(255, 255, 255, 40))
        p.drawText(screen, Qt.AlignCenter, "your game")
        if not self.level:
            return
        lvl = self.level
        scale = w / 1920
        font = QFont("Noto Sans Mono", max(5, int(lvl["font_size"] * scale * 1.1)))
        font.setBold(True)
        p.setFont(font)
        fm = p.fontMetrics()
        rows = preview_rows(lvl)
        graph = "frame_timing" in lvl["metrics"]
        pad = 6 * scale * 3
        if lvl["horizontal"]:
            text = "   ".join(f"{a} {b}".strip() for a, b in rows)
            bw = fm.horizontalAdvance(text) + 2 * pad + (80 * scale * 3 if graph else 0)
            bh = fm.height() + 2 * pad
        else:
            label_w = max([fm.horizontalAdvance(a) for a, _ in rows] + [0])
            val_w = max([fm.horizontalAdvance(b) for _, b in rows] + [0])
            bw = label_w + val_w + fm.horizontalAdvance("  ") + 2 * pad
            bh = fm.height() * len(rows) + 2 * pad + (fm.height() * 2 if graph else 0)
        bw = min(bw, w - 4)
        pos = lvl["position"]
        ox, oy = lvl["offset_x"] * scale, lvl["offset_y"] * scale
        if pos.endswith("left"):
            bx = screen.left() + 4 + ox
        elif pos.endswith("right"):
            bx = screen.right() - bw - 4 - ox
        else:
            bx = screen.center().x() - bw / 2 + ox
        if pos.startswith("top"):
            by = screen.top() + 4 + oy
        elif pos.startswith("bottom"):
            by = screen.bottom() - bh - 4 - oy
        else:
            by = screen.center().y() - bh / 2 + oy
        box = QRectF(bx, by, bw, bh)
        bg = QColor("#" + lvl["background_color"])
        bg.setAlphaF(float(lvl["background_alpha"]))
        path = QPainterPath()
        path.addRoundedRect(box, 5, 5)
        p.fillPath(path, bg)
        p.setClipRect(screen)
        text_color = QColor("#" + lvl["text_color"])
        accent = QColor(ACCENT)
        y = box.top() + pad + fm.ascent()
        if lvl["horizontal"]:
            x = box.left() + pad
            for a, b in rows:
                if a:
                    p.setPen(accent)
                    p.drawText(int(x), int(y), a)
                    x += fm.horizontalAdvance(a + " ")
                p.setPen(text_color)
                p.drawText(int(x), int(y), b)
                x += fm.horizontalAdvance(b + "   ")
            if graph:
                self._graph(p, QRectF(x, box.top() + pad, 80 * scale * 3, fm.height()), accent)
        else:
            vx = box.left() + pad + label_w + fm.horizontalAdvance("  ")
            for a, b in rows:
                p.setPen(accent)
                p.drawText(int(box.left() + pad), int(y), a)
                p.setPen(text_color)
                p.drawText(int(vx), int(y), b)
                y += fm.height()
            if graph:
                self._graph(p, QRectF(box.left() + pad, y - fm.ascent() + 2,
                                      bw - 2 * pad, fm.height() * 2 - 4), accent)

    @staticmethod
    def _graph(p, r, color):
        pts = [0.5, 0.45, 0.55, 0.5, 0.4, 0.9, 0.5, 0.48, 0.52, 0.5, 0.47, 0.5, 0.6, 0.5]
        p.setPen(QPen(color, 1.5))
        step = r.width() / (len(pts) - 1)
        for i in range(len(pts) - 1):
            p.drawLine(int(r.left() + i * step), int(r.bottom() - pts[i] * r.height()),
                       int(r.left() + (i + 1) * step), int(r.bottom() - pts[i + 1] * r.height()))


class ColorButton(QPushButton):
    def __init__(self, on_change):
        super().__init__()
        self.color = "FFFFFF"
        self.on_change = on_change
        self.clicked.connect(self._pick)

    def set_color(self, hexcolor):
        self.color = hexcolor.upper()
        self.setText("#" + self.color)
        self.setStyleSheet(f"background: #{self.color}; color: {'#000' if QColor('#' + self.color).lightness() > 128 else '#fff'};")

    def _pick(self):
        c = QColorDialog.getColor(QColor("#" + self.color), self, "Pick a color")
        if c.isValid():
            self.set_color(c.name()[1:])
            self.on_change()


class OverlayTab(QWidget):
    def __init__(self):
        super().__init__()
        self.state = overlay.load()
        self.current = None
        self.loading = False

        top = QGroupBox("In-game overlay")
        tl = QGridLayout(top)
        self.start = QComboBox()
        self.start.currentIndexChanged.connect(self._start_changed)
        self.toggle_hud = QLineEdit()
        self.toggle_preset = QLineEdit()
        self.fps_limit = QSpinBox()
        self.fps_limit.setRange(0, 1000)
        self.fps_limit.setSpecialValueText("Unlimited")
        for wdg in (self.toggle_hud, self.toggle_preset):
            wdg.editingFinished.connect(self._globals_changed)
        self.fps_limit.valueChanged.connect(self._globals_changed)
        tl.addWidget(QLabel("<b>Overlay level</b>"), 0, 0)
        tl.addWidget(self.start, 0, 1)
        tl.addWidget(QLabel("FPS limit"), 0, 2)
        tl.addWidget(self.fps_limit, 0, 3)
        tl.addWidget(QLabel("Show / hide hotkey"), 1, 0)
        tl.addWidget(self.toggle_hud, 1, 1)
        tl.addWidget(QLabel("Next level hotkey"), 1, 2)
        tl.addWidget(self.toggle_preset, 1, 3)
        hint = QLabel("Changes apply instantly, even to games that are already running.")
        hint.setObjectName("muted")
        tl.addWidget(hint, 2, 0, 1, 4)

        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(0, 0, 0, 0)
        ll.addWidget(QLabel("<b>Levels</b>"))
        self.levels = QListWidget()
        self.levels.currentItemChanged.connect(self._select)
        ll.addWidget(self.levels)
        row = QHBoxLayout()
        for text, slot in (("Add", self._add), ("Duplicate", self._dup), ("Rename", self._rename), ("Delete", self._delete)):
            b = QPushButton(text)
            b.clicked.connect(slot)
            row.addWidget(b)
        ll.addLayout(row)

        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        self.preview = OverlayPreview()
        rl.addWidget(self.preview, 3)

        look = QGroupBox("Where it goes and how it looks")
        fl = QGridLayout(look)
        self.position = QComboBox()
        for key, label in overlay.POSITIONS:
            self.position.addItem(label, key)
        self.layout_combo = QComboBox()
        self.layout_combo.addItems(["Vertical list", "Horizontal bar"])
        self.compact = QCheckBox("Compact")
        self.font_size = QSpinBox()
        self.font_size.setRange(10, 64)
        self.alpha = QDoubleSpinBox()
        self.alpha.setRange(0, 1)
        self.alpha.setSingleStep(0.05)
        self.text_color = ColorButton(self._edited)
        self.bg_color = ColorButton(self._edited)
        self.off_x = QSpinBox()
        self.off_y = QSpinBox()
        for s in (self.off_x, self.off_y):
            s.setRange(0, 2000)
            s.setSuffix(" px")
        fl.addWidget(QLabel("Position"), 0, 0)
        fl.addWidget(self.position, 0, 1)
        fl.addWidget(QLabel("Layout"), 0, 2)
        fl.addWidget(self.layout_combo, 0, 3)
        fl.addWidget(self.compact, 0, 4)
        fl.addWidget(QLabel("Font size"), 1, 0)
        fl.addWidget(self.font_size, 1, 1)
        fl.addWidget(QLabel("Background opacity"), 1, 2)
        fl.addWidget(self.alpha, 1, 3)
        fl.addWidget(QLabel("Text"), 2, 0)
        fl.addWidget(self.text_color, 2, 1)
        fl.addWidget(QLabel("Background"), 2, 2)
        fl.addWidget(self.bg_color, 2, 3)
        fl.addWidget(QLabel("Offset X"), 3, 0)
        fl.addWidget(self.off_x, 3, 1)
        fl.addWidget(QLabel("Offset Y"), 3, 2)
        fl.addWidget(self.off_y, 3, 3)
        for sig in (self.position.currentIndexChanged, self.layout_combo.currentIndexChanged,
                    self.compact.toggled, self.font_size.valueChanged, self.alpha.valueChanged,
                    self.off_x.valueChanged, self.off_y.valueChanged):
            sig.connect(self._edited)
        rl.addWidget(look)

        shown = QGroupBox("What it shows")
        gl = QGridLayout(shown)
        self.checks = {}
        for col, group in enumerate(overlay.GROUPS):
            head = QLabel(f"<b>{group}</b>")
            gl.addWidget(head, 0, col)
            r = 1
            for key, label, g in overlay.METRICS:
                if g != group:
                    continue
                cb = QCheckBox(label)
                if key in overlay.GPU_ROW:
                    cb.setToolTip("Shown on the GPU row (turns GPU load on too)")
                if key in overlay.CPU_ROW:
                    cb.setToolTip("Shown on the CPU row (turns CPU load on too)")
                cb.toggled.connect(self._edited)
                self.checks[key] = cb
                gl.addWidget(cb, r, col)
                r += 1
        rl.addWidget(shown)

        split = QSplitter()
        split.addWidget(left)
        split.addWidget(right)
        split.setStretchFactor(1, 4)

        bottom = QHBoxLayout()
        test = QPushButton("Test overlay (spinning cube)")
        test.clicked.connect(self._test)
        reset = QPushButton("Reset to ZachOS defaults")
        reset.clicked.connect(self._reset)
        self.saved = QLabel("")
        self.saved.setObjectName("muted")
        bottom.addWidget(test)
        bottom.addWidget(reset)
        bottom.addStretch()
        bottom.addWidget(self.saved)

        lay = QVBoxLayout(self)
        lay.addWidget(top)
        lay.addWidget(split, 1)
        lay.addLayout(bottom)

        self.save_timer = QTimer(self)
        self.save_timer.setSingleShot(True)
        self.save_timer.timeout.connect(self._save)
        self._refresh(select=overlay.level_ids(self.state)[0])

    def _refresh(self, select=None):
        self.loading = True
        self.toggle_hud.setText(self.state["toggle_hud"])
        self.toggle_preset.setText(self.state["toggle_preset"])
        self.fps_limit.setValue(int(self.state["fps_limit"]))
        self.start.clear()
        self.start.addItem("0 - Off", "0")
        self.levels.clear()
        for lid in overlay.level_ids(self.state):
            name = self.state["levels"][lid]["name"]
            self.start.addItem(f"{lid} - {name}", lid)
            item = QListWidgetItem(f"{lid}   {name}")
            item.setData(Qt.UserRole, lid)
            self.levels.addItem(item)
        self.start.setCurrentIndex(max(0, self.start.findData(str(self.state["start_level"]))))
        self.loading = False
        for i in range(self.levels.count()):
            if self.levels.item(i).data(Qt.UserRole) == select:
                self.levels.setCurrentRow(i)
                return
        if self.levels.count():
            self.levels.setCurrentRow(0)

    def _select(self, item, _prev=None):
        if not item:
            return
        self.current = item.data(Qt.UserRole)
        lvl = self.state["levels"][self.current]
        self.loading = True
        self.position.setCurrentIndex(max(0, self.position.findData(lvl["position"])))
        self.layout_combo.setCurrentIndex(1 if lvl["horizontal"] else 0)
        self.compact.setChecked(bool(lvl["compact"]))
        self.font_size.setValue(int(lvl["font_size"]))
        self.alpha.setValue(float(lvl["background_alpha"]))
        self.text_color.set_color(lvl["text_color"])
        self.bg_color.set_color(lvl["background_color"])
        self.off_x.setValue(int(lvl["offset_x"]))
        self.off_y.setValue(int(lvl["offset_y"]))
        for key, cb in self.checks.items():
            cb.setChecked(key in lvl["metrics"])
        self.loading = False
        self.preview.show_level(lvl)

    def _edited(self, *_):
        if self.loading or self.current is None:
            return
        lvl = self.state["levels"][self.current]
        lvl.update(
            position=self.position.currentData(),
            horizontal=self.layout_combo.currentIndex() == 1,
            compact=self.compact.isChecked(),
            font_size=self.font_size.value(),
            background_alpha=round(self.alpha.value(), 2),
            text_color=self.text_color.color,
            background_color=self.bg_color.color,
            offset_x=self.off_x.value(),
            offset_y=self.off_y.value(),
            metrics=[k for k in overlay.METRIC_KEYS if self.checks[k].isChecked()],
        )
        self.preview.show_level(lvl)
        self.save_timer.start(300)

    def _globals_changed(self, *_):
        if self.loading:
            return
        self.state["toggle_hud"] = self.toggle_hud.text().strip() or "Shift_R+F12"
        self.state["toggle_preset"] = self.toggle_preset.text().strip() or "Shift_R+F10"
        self.state["fps_limit"] = self.fps_limit.value()
        self.save_timer.start(300)

    def _start_changed(self, _i):
        if self.loading or self.start.currentData() is None:
            return
        self.state["start_level"] = int(self.start.currentData())
        self._save()

    def _save(self):
        try:
            overlay.save(self.state)
            self.saved.setText("Saved and applied")
        except OSError as e:
            self.saved.setText(f"Could not save: {e}")

    def _next_id(self):
        return str(max([int(i) for i in self.state["levels"]] + [0]) + 1)

    def _add(self):
        name, ok = QInputDialog.getText(self, "New level", "Name for the new level:")
        if ok and name.strip():
            lid = self._next_id()
            self.state["levels"][lid] = {**overlay.LEVEL_DEFAULTS, "name": name.strip(), "metrics": ["fps"]}
            self._save()
            self._refresh(select=lid)

    def _dup(self):
        if self.current is None:
            return
        lid = self._next_id()
        src = self.state["levels"][self.current]
        self.state["levels"][lid] = {**src, "metrics": list(src["metrics"]), "name": src["name"] + " copy"}
        self._save()
        self._refresh(select=lid)

    def _rename(self):
        if self.current is None:
            return
        lvl = self.state["levels"][self.current]
        name, ok = QInputDialog.getText(self, "Rename level", "Name:", text=lvl["name"])
        if ok and name.strip():
            lvl["name"] = name.strip()
            self._save()
            self._refresh(select=self.current)

    def _delete(self):
        if self.current is None or len(self.state["levels"]) <= 1:
            return
        if QMessageBox.question(self, "Delete level", f"Delete level {self.current}?") != QMessageBox.Yes:
            return
        del self.state["levels"][self.current]
        if str(self.state["start_level"]) == self.current:
            self.state["start_level"] = 0
        self._save()
        self._refresh()

    def _reset(self):
        if QMessageBox.question(self, "Reset", "Replace all levels with the ZachOS defaults?") == QMessageBox.Yes:
            self.state = overlay.default_state()
            self._save()
            self._refresh(select="1")

    def _test(self):
        self._save()
        env = dict(os.environ, MANGOHUD="1", MANGOHUD_CONFIG=f"preset={self.current or 1}")
        try:
            subprocess.Popen(["vkcube"], env=env)
        except OSError:
            QMessageBox.warning(self, "Test", "vkcube is not installed.")



FLATHUB = "https://dl.flathub.org/repo/flathub.flatpakrepo"

CATALOG = {
    "Gaming": [
        ("com.heroicgameslauncher.hgl", "Heroic", "Epic, GOG and Amazon games"),
        ("net.lutris.Lutris", "Lutris", "Battle.net, EA, Ubisoft and emulators in one launcher"),
        ("net.davidotek.pupgui2", "ProtonUp-Qt", "Install Proton-GE and other compatibility tools"),
        ("com.usebottles.bottles", "Bottles", "Run Windows apps with Wine"),
        ("org.prismlauncher.PrismLauncher", "Prism Launcher", "Minecraft with mods and multiple instances"),
        ("org.libretro.RetroArch", "RetroArch", "Retro console emulation"),
    ],
    "Chat & streaming": [
        ("com.discordapp.Discord", "Discord", "Voice and text chat"),
        ("dev.vencord.Vesktop", "Vesktop", "Discord with working screen share audio on Linux"),
        ("com.github.wwmm.easyeffects", "EasyEffects", "Mic noise removal, EQ and compressor"),
        ("com.spotify.Client", "Spotify", "Music"),
        ("org.telegram.desktop", "Telegram", "Messaging"),
    ],
    "Video & creative": [
        ("org.kde.kdenlive", "Kdenlive", "Video editor for YouTube videos"),
        ("org.shotcut.Shotcut", "Shotcut", "Simple video editor"),
        ("fr.handbrake.ghb", "HandBrake", "Compress and convert videos"),
        ("org.audacityteam.Audacity", "Audacity", "Audio recording and editing"),
        ("org.gimp.GIMP", "GIMP", "Image editing and thumbnails"),
        ("org.kde.krita", "Krita", "Digital painting"),
        ("org.inkscape.Inkscape", "Inkscape", "Vector graphics and logos"),
        ("org.blender.Blender", "Blender", "3D, animation and VFX"),
    ],
    "Everyday": [
        ("com.google.Chrome", "Google Chrome", "Web browser"),
        ("com.brave.Browser", "Brave", "Web browser"),
        ("org.videolan.VLC", "VLC", "Plays any video"),
        ("org.qbittorrent.qBittorrent", "qBittorrent", "Torrent client"),
        ("com.visualstudio.code", "VS Code", "Code editor"),
        ("com.github.tchx84.Flatseal", "Flatseal", "Change what installed apps can access"),
    ],
}


class AppRow(QWidget):
    def __init__(self, app_id, name, desc, on_click):
        super().__init__()
        self.app_id = app_id
        lay = QHBoxLayout(self)
        lay.setContentsMargins(8, 4, 8, 4)
        text = QLabel(f"<b>{name}</b><br><span style='color:#8a92a6'>{desc}</span>")
        text.setTextInteractionFlags(Qt.NoTextInteraction)
        self.button = QPushButton()
        self.button.setFixedWidth(110)
        self.button.clicked.connect(lambda: on_click(self))
        lay.addWidget(text, 1)
        lay.addWidget(self.button)

    def set_installed(self, installed):
        self.installed = installed
        self.button.setText("Remove" if installed else "Install")
        self.button.setObjectName("" if installed else "primary")
        self.button.setStyleSheet(self.button.styleSheet())  # re-polish for the objectName change


class AppsTab(QWidget):
    def __init__(self):
        super().__init__()
        intro = QLabel("ZachOS ships lean. Grab anything else here - apps install just for you "
                       "(no password), run sandboxed, and only update when you press Update.")
        intro.setWordWrap(True)
        intro.setObjectName("muted")
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search all of Flathub (press Enter)...")
        self.search.returnPressed.connect(self.search_flathub)
        self.search.textChanged.connect(self._filter)

        self.list = QListWidget()
        self.list.setSpacing(1)
        self.rows = []
        self.log = ProcessLog()
        self.log.setMaximumHeight(170)
        self.pending = None

        lay = QVBoxLayout(self)
        lay.addWidget(intro)
        lay.addWidget(self.search)
        lay.addWidget(self.list, 1)
        lay.addWidget(self.log)
        self._show_catalog()

    def _installed(self):
        out = run(["flatpak", "list", "--app", "--columns=application"])
        return set(out.split())

    def _add_header(self, text):
        item = QListWidgetItem(text)
        item.setFlags(Qt.NoItemFlags)
        f = item.font()
        f.setBold(True)
        f.setPointSize(f.pointSize() + 1)
        item.setFont(f)
        item.setForeground(QColor(ACCENT))
        self.list.addItem(item)

    def _add_row(self, app_id, name, desc, installed):
        row = AppRow(app_id, name, desc, self._clicked)
        row.set_installed(app_id in installed)
        item = QListWidgetItem()
        item.setSizeHint(row.sizeHint())
        item.setData(Qt.UserRole, f"{app_id} {name} {desc}".lower())
        self.list.addItem(item)
        self.list.setItemWidget(item, row)
        self.rows.append(row)

    def _show_catalog(self):
        self.list.clear()
        self.rows = []
        installed = self._installed()
        for cat, apps in CATALOG.items():
            self._add_header(cat)
            for app in apps:
                self._add_row(*app, installed)

    def _filter(self, text):
        if not text:
            self._show_catalog()
            return
        text = text.lower()
        for i in range(self.list.count()):
            item = self.list.item(i)
            key = item.data(Qt.UserRole)
            item.setHidden(key is None or text not in key)

    def search_flathub(self):
        term = self.search.text().strip()
        if not term:
            return
        self.pending = ("search", term)
        self.log.start("/usr/bin/bash", ["-c", self._setup_cmd()], self._after_setup)

    def _setup_cmd(self):
        return (f"flatpak remote-add --user --if-not-exists flathub {FLATHUB} && "
                "flatpak update --user --appstream flathub >/dev/null 2>&1; true")

    def _after_setup(self, _code):
        kind, term = self.pending
        if kind != "search":
            return
        out = run(["flatpak", "search", "--columns=name,description,application", term])
        self.list.clear()
        self.rows = []
        installed = self._installed()
        self._add_header(f"Flathub results for \"{term}\"")
        found = 0
        for line in out.splitlines():
            parts = line.split("\t")
            if len(parts) >= 3 and "." in parts[2]:
                self._add_row(parts[2], parts[0], parts[1], installed)
                found += 1
        self.log.appendPlainText(f"{found} result(s). Clear the search box to go back to the catalog.")

    def _clicked(self, row):
        if self.log.busy():
            QMessageBox.information(self, "Busy", "Wait for the current install to finish.")
            return
        if row.installed:
            if QMessageBox.question(self, "Remove", f"Remove {row.app_id}?") != QMessageBox.Yes:
                return
            cmd = f"flatpak uninstall -y --noninteractive {row.app_id}"
        else:
            cmd = (f"{self._setup_cmd()} ; flatpak install --user -y --noninteractive flathub {row.app_id}")
        row.button.setEnabled(False)
        row.button.setText("Working...")
        self.log.start("/usr/bin/bash", ["-c", cmd], lambda code, r=row: self._done(r, code))

    def _done(self, row, code):
        row.button.setEnabled(True)
        row.set_installed(row.app_id in self._installed())
        if code != 0:
            self.log.appendPlainText("\nThat didn't work - check your internet connection.")



class UpdatesTab(QWidget):
    def __init__(self):
        super().__init__()
        banner = QLabel("Update lock is ON - nothing updates, installs a new driver or restarts "
                        "your PC unless you press the button below.")
        banner.setObjectName("banner")
        banner.setWordWrap(True)
        banner.setStyleSheet("background: #3d1013; color: #ffd9db;")
        self.last = QLabel()
        self.last.setObjectName("muted")

        self.check_btn = QPushButton("Check for updates")
        self.check_btn.clicked.connect(self.check)
        self.update_btn = QPushButton("Update everything now")
        self.update_btn.setObjectName("primary")
        self.update_btn.clicked.connect(self.apply)
        row = QHBoxLayout()
        row.addWidget(self.check_btn)
        row.addWidget(self.update_btn)
        row.addStretch()

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Package", "Installed", "Available", ""])
        self.tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.log = ProcessLog()
        split = QSplitter(Qt.Vertical)
        split.addWidget(self.tree)
        split.addWidget(self.log)

        lay = QVBoxLayout(self)
        lay.addWidget(banner)
        lay.addWidget(self.last)
        lay.addLayout(row)
        lay.addWidget(split, 1)
        self._last()

    def _last(self):
        try:
            when = (STATE_DIR / "last-update").read_text().strip()
        except OSError:
            when = "never (since install)"
        self.last.setText(f"Last update you ran: {when}.  A driver restore point is saved "
                          "automatically before every update.")

    def check(self):
        self.tree.clear()
        self.check_btn.setEnabled(False)
        self.log.start("/usr/bin/bash", ["-c", "checkupdates 2>&1; echo \"__rc=$?\"; "
                                         "command -v flatpak >/dev/null && flatpak remote-ls --updates "
                                         "--columns=application,version 2>/dev/null | sed 's/^/flatpak /'"],
                       self._checked)

    def _checked(self, _code):
        self.check_btn.setEnabled(True)
        drivers = set(driver_packages())
        count = 0
        for line in self.log.toPlainText().splitlines():
            m = re.match(r"^(\S+) (\S+) -> (\S+)$", line)
            f = re.match(r"^flatpak (\S+)\s*(\S*)", line)
            if m:
                item = QTreeWidgetItem([m[1], m[2], m[3], "driver" if m[1] in drivers else ""])
                if m[1] in drivers:
                    item.setForeground(3, QColor("#ffb347"))
            elif f:
                item = QTreeWidgetItem([f[1], "", f[2], "flatpak"])
            else:
                continue
            self.tree.addTopLevelItem(item)
            count += 1
        rc = re.search(r"__rc=(\d+)", self.log.toPlainText())
        if rc and rc[1] == "1":
            self.log.appendPlainText("\nCould not check for updates - are you connected to the internet?")
        else:
            self.log.appendPlainText(f"\n{count} update(s) available." if count else "\nYou're up to date.")

    def apply(self):
        msg = ("Update ZachOS now?\n\nA driver restore point is saved first, so you can undo a bad "
               "driver update from the Drivers tab. Your PC will NOT restart by itself.")
        if QMessageBox.question(self, "Update", msg) != QMessageBox.Yes:
            return
        self.update_btn.setEnabled(False)
        self.log.start("/usr/bin/bash", ["-c", f"pkexec {LIB}/zach-update-apply && "
                                         "{ command -v flatpak >/dev/null || exit 0; "
                                         "echo '==> Updating your apps (Flatpak)'; "
                                         "flatpak update --user -y --noninteractive; }"], self._applied)

    def _applied(self, code):
        self.update_btn.setEnabled(True)
        self._last()
        if code == 0:
            QMessageBox.information(self, "Update", "Update finished.\nRestart whenever you're ready.")



def gpus():
    out = run(["lspci", "-nnk"])
    found, cur = [], None
    for line in out.splitlines():
        if not line.startswith(("\t", " ")):
            cur = None
            m = re.match(r"^\S+ (VGA compatible controller|3D controller|Display controller) \[\w+\]: (.*)", line)
            if m:
                cur = {"name": re.sub(r"\s*\[[0-9a-f]{4}:[0-9a-f]{4}\].*$", "", m[2]), "driver": "none"}
                found.append(cur)
        elif cur and "Kernel driver in use:" in line:
            cur["driver"] = line.split(":", 1)[1].strip()
    return found


def read_history():
    entries = []
    for f in sorted(HISTORY_DIR.glob("*.list"), reverse=True):
        try:
            lines = f.read_text().splitlines()
        except OSError:
            continue
        header = lines[0].lstrip("# ") if lines and lines[0].startswith("#") else f.stem
        pkgs = dict(l.split(None, 1) for l in lines if l and not l.startswith("#") and " " in l)
        entries.append((f, header, pkgs))
    return entries


class DriversTab(QWidget):
    def __init__(self):
        super().__init__()
        gpu_box = QGroupBox("Graphics cards")
        self.gpu_label = QLabel()
        self.gpu_label.setWordWrap(True)
        QVBoxLayout(gpu_box).addWidget(self.gpu_label)

        self.rollback_btn = QPushButton("One-click driver rollback")
        self.rollback_btn.setObjectName("danger")
        self.rollback_btn.clicked.connect(self.rollback_previous)
        self.restore_btn = QPushButton("Restore selected point")
        self.restore_btn.clicked.connect(self.restore_selected)
        self.snap_btn = QPushButton("Save restore point now")
        self.snap_btn.clicked.connect(lambda: self._root(["--snapshot"]))
        self.hold = QCheckBox("Hold drivers (updates skip them)")
        self.hold.clicked.connect(self._hold)
        row = QHBoxLayout()
        for w in (self.rollback_btn, self.restore_btn, self.snap_btn):
            row.addWidget(w)
        row.addStretch()
        row.addWidget(self.hold)

        self.current = QTreeWidget()
        self.current.setHeaderLabels(["Driver package", "Installed version"])
        self.current.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.history = QTreeWidget()
        self.history.setHeaderLabels(["Restore point", "Differences from now"])
        self.history.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hist_box = QGroupBox("Restore points")
        QVBoxLayout(hist_box).addWidget(self.history)
        cur_box = QGroupBox("Installed drivers")
        QVBoxLayout(cur_box).addWidget(self.current)
        tables = QSplitter()
        tables.addWidget(cur_box)
        tables.addWidget(hist_box)
        self.log = ProcessLog()
        split = QSplitter(Qt.Vertical)
        split.addWidget(tables)
        split.addWidget(self.log)

        lay = QVBoxLayout(self)
        lay.addWidget(gpu_box)
        lay.addLayout(row)
        lay.addWidget(split, 1)
        self.refresh()

    def refresh(self, *_):
        cards = gpus()
        self.gpu_label.setText("<br>".join(
            f"<b>{g['name']}</b> &nbsp; <span style='color:#8a92a6'>driver in use: {g['driver']}</span>"
            for g in cards) or "No graphics card detected.")
        now = installed_versions(driver_packages())
        self.current.clear()
        for name, ver in now.items():
            self.current.addTopLevelItem(QTreeWidgetItem([name, ver]))
        self.history.clear()
        for f, header, pkgs in read_history():
            diff = [f"{n} {v}" for n, v in pkgs.items() if n in now and now[n] != v]
            item = QTreeWidgetItem([header, ", ".join(diff) or "same as now"])
            item.setData(0, Qt.UserRole, str(f))
            self.history.addTopLevelItem(item)
        try:
            held = any(l.startswith("IgnorePkg") for l in HOLD_CONF.read_text().splitlines())
        except OSError:
            held = False
        self.hold.setChecked(held)

    def _root(self, args):
        for b in (self.rollback_btn, self.restore_btn, self.snap_btn):
            b.setEnabled(False)
        self.log.start("pkexec", [f"{LIB}/zach-driver-rollback", *args], self._done)

    def _done(self, code):
        for b in (self.rollback_btn, self.restore_btn, self.snap_btn):
            b.setEnabled(True)
        self.refresh()
        if code == 0 and "restart" in self.log.toPlainText().lower():
            QMessageBox.information(self, "Drivers", "Drivers restored.\nRestart when you're ready to use them.")

    def rollback_previous(self):
        msg = ("Roll your graphics drivers (and the kernel they belong to) back to the versions "
               "you had before your last update?")
        if QMessageBox.question(self, "Driver rollback", msg) == QMessageBox.Yes:
            self._root(["--previous"])

    def restore_selected(self):
        item = self.history.currentItem()
        if not item:
            QMessageBox.information(self, "Restore", "Pick a restore point from the list first.")
            return
        if QMessageBox.question(self, "Restore", f"Restore drivers from:\n{item.text(0)}?") == QMessageBox.Yes:
            self._root(["--to", item.data(0, Qt.UserRole)])

    def _hold(self, checked):
        self._root(["--hold", "on" if checked else "off"])



def os_info():
    info = {}
    try:
        for line in Path("/etc/os-release").read_text().splitlines():
            k, _, v = line.partition("=")
            info[k] = v.strip('"')
    except OSError:
        pass
    return info


class SystemTab(QWidget):
    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)
        logo = QLabel(f"<span style='font-size:34pt;font-weight:900;color:{ACCENT}'>ZACH</span>"
                      "<span style='font-size:34pt;font-weight:300'>OS</span>")
        lay.addWidget(logo)
        osr = os_info()
        form = QFormLayout()
        form.addRow("System", QLabel(osr.get("PRETTY_NAME", "ZachOS") + ("  (live USB / ISO)" if IS_LIVE else "")))
        form.addRow("Based on", QLabel("Arch Linux (rolling release)"))
        form.addRow("Kernel", QLabel(run(["uname", "-r"]).strip()))
        form.addRow("Desktop", QLabel("KDE Plasma"))
        form.addRow("Graphics", QLabel(", ".join(g["name"] for g in gpus()) or "-"))
        lay.addLayout(form)
        if IS_LIVE:
            box = QGroupBox("Install")
            bl = QVBoxLayout(box)
            bl.addWidget(QLabel("You're running ZachOS from the ISO. Install it to a disk to keep your "
                                "games, settings and updates.\nThis erases the disk you pick."))
            b = QPushButton("Install ZachOS to disk")
            b.setObjectName("primary")
            b.clicked.connect(lambda: subprocess.Popen(["konsole", "-e", "sudo", "/usr/bin/zach-install"]))
            bl.addWidget(b)
            lay.addWidget(box)
        tips = QLabel(
            "<b>Hotkeys in games</b><br>"
            "Shift (right) + F12 - show / hide the overlay<br>"
            "Shift (right) + F10 - next overlay level<br><br>"
            "<b>Command line</b><br>"
            "<code>zach-overlay level 3</code> &nbsp; <code>zach-update</code> &nbsp; "
            "<code>zach-driver-rollback --previous</code>")
        tips.setObjectName("muted")
        lay.addWidget(tips)
        lay.addStretch()


class Main(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Zach Center")
        self.resize(1180, 820)
        tabs = QTabWidget()
        tabs.addTab(OverlayTab(), "Overlay")
        tabs.addTab(AppsTab(), "Apps")
        tabs.addTab(UpdatesTab(), "Updates")
        tabs.addTab(DriversTab(), "Drivers")
        tabs.addTab(SystemTab(), "System")
        names = {"overlay": 0, "apps": 1, "updates": 2, "drivers": 3, "system": 4}
        if len(sys.argv) > 1 and sys.argv[1] in names:
            tabs.setCurrentIndex(names[sys.argv[1]])
        self.setCentralWidget(tabs)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Zach Center")
    app.setDesktopFileName("zach-center")
    app.setStyleSheet(STYLE)
    w = Main()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
