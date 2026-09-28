import copy
import json
import os
import sys
from pathlib import Path

CONFIG_HOME = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
STATE_FILE = CONFIG_HOME / "zachos" / "overlay.json"
MANGO_DIR = CONFIG_HOME / "MangoHud"

METRICS = [
    ("fps", "FPS", "Performance"),
    ("lows", "1% / 0.1% lows", "Performance"),
    ("frametime", "Frametime (ms)", "Performance"),
    ("frame_timing", "Frametime graph", "Performance"),
    ("show_fps_limit", "FPS limit", "Performance"),
    ("cpu_stats", "CPU load", "CPU"),
    ("cpu_temp", "CPU temperature", "CPU"),
    ("cpu_power", "CPU power draw", "CPU"),
    ("cpu_mhz", "CPU clock", "CPU"),
    ("core_load", "Per-core load", "CPU"),
    ("gpu_name", "GPU name", "GPU"),
    ("gpu_stats", "GPU load", "GPU"),
    ("gpu_temp", "GPU temperature", "GPU"),
    ("gpu_junction_temp", "GPU hotspot temp", "GPU"),
    ("gpu_mem_temp", "VRAM temperature", "GPU"),
    ("gpu_power", "GPU power draw", "GPU"),
    ("gpu_core_clock", "GPU core clock", "GPU"),
    ("gpu_mem_clock", "GPU memory clock", "GPU"),
    ("gpu_fan", "GPU fan speed", "GPU"),
    ("vram", "VRAM usage", "Memory"),
    ("ram", "RAM usage", "Memory"),
    ("swap", "Swap usage", "Memory"),
    ("procmem", "Game memory", "Memory"),
    ("vulkan_driver", "Driver version", "System"),
    ("engine_version", "Graphics API / engine", "System"),
    ("wine", "Wine / Proton version", "System"),
    ("resolution", "Resolution", "System"),
    ("gamemode", "GameMode status", "System"),
    ("fsr", "FSR status", "System"),
    ("hdr", "HDR status", "System"),
    ("battery", "Battery", "System"),
    ("throttling_status", "Throttling warning", "System"),
    ("io_read", "Disk read", "System"),
    ("io_write", "Disk write", "System"),
    ("time", "Clock", "System"),
]
METRIC_KEYS = [m[0] for m in METRICS]
GROUPS = ["Performance", "CPU", "GPU", "Memory", "System"]

# these need the cpu/gpu row toggled on or they won't render
CPU_ROW = {"cpu_temp", "cpu_power", "cpu_mhz"}
GPU_ROW = {"gpu_temp", "gpu_junction_temp", "gpu_mem_temp", "gpu_power",
           "gpu_core_clock", "gpu_mem_clock", "gpu_fan"}

POSITIONS = [
    ("top-left", "Top left"), ("top-center", "Top center"), ("top-right", "Top right"),
    ("middle-left", "Middle left"), ("middle-right", "Middle right"),
    ("bottom-left", "Bottom left"), ("bottom-center", "Bottom center"),
    ("bottom-right", "Bottom right"),
]

LEVEL_DEFAULTS = {
    "name": "New level",
    "metrics": ["fps"],
    "position": "top-left",
    "horizontal": False,
    "compact": False,
    "font_size": 24,
    "background_alpha": 0.4,
    "text_color": "FFFFFF",
    "background_color": "020202",
    "offset_x": 0,
    "offset_y": 0,
}


def _level(**kw):
    lvl = copy.deepcopy(LEVEL_DEFAULTS)
    lvl.update(kw)
    return lvl


DEFAULT_STATE = {
    "version": 1,
    "start_level": 0,
    "toggle_hud": "Shift_R+F12",
    "toggle_preset": "Shift_R+F10",
    "fps_limit": 0,
    "levels": {
        "1": _level(name="FPS only", metrics=["fps"], compact=True, font_size=22),
        "2": _level(name="Horizontal bar", position="top-center", horizontal=True,
                    metrics=["fps", "frametime", "cpu_stats", "gpu_stats", "ram", "vram"]),
        "3": _level(name="Detailed", metrics=[
            "fps", "lows", "frametime", "frame_timing", "cpu_stats", "cpu_temp",
            "gpu_stats", "gpu_temp", "gpu_power", "vram", "ram"]),
        "4": _level(name="Full (Afterburner style)", font_size=20, metrics=[
            "fps", "lows", "frametime", "frame_timing", "show_fps_limit",
            "cpu_stats", "cpu_temp", "cpu_power", "cpu_mhz", "core_load",
            "gpu_name", "gpu_stats", "gpu_temp", "gpu_junction_temp", "gpu_power",
            "gpu_core_clock", "gpu_mem_clock", "gpu_fan", "vram", "ram", "swap",
            "procmem", "vulkan_driver", "engine_version", "wine", "resolution",
            "gamemode", "fsr", "throttling_status", "time"]),
    },
}


def default_state():
    return copy.deepcopy(DEFAULT_STATE)


def load():
    try:
        state = json.loads(STATE_FILE.read_text())
    except (OSError, ValueError):
        return default_state()
    merged = default_state()
    merged.update({k: v for k, v in state.items() if k != "levels"})
    if isinstance(state.get("levels"), dict) and state["levels"]:
        merged["levels"] = {k: {**LEVEL_DEFAULTS, **v} for k, v in state["levels"].items()}
    return merged


def level_ids(state):
    return sorted(state["levels"], key=int)


def level_cycle(state):
    ids = ["0"] + level_ids(state)
    start = str(state.get("start_level", 0))
    if start not in ids:
        start = "0"
    i = ids.index(start)
    return ids[i:] + ids[:i]


def render_preset(lvl):
    on = set(lvl.get("metrics", []))
    if on & GPU_ROW:
        on.add("gpu_stats")
    if on & CPU_ROW:
        on.add("cpu_stats")
    lines = ["legacy_layout=0"]
    lines += [f"{key}={int(key in on)}" for key in METRIC_KEYS if key != "lows"]
    if "lows" in on:
        lines.append("fps_metrics=avg,0.01,0.001")
    lines.append(f"position={lvl['position']}")
    if lvl.get("horizontal"):
        lines += ["horizontal", "table_columns=20"]
    else:
        lines.append("table_columns=3")
    if lvl.get("compact"):
        lines.append("hud_compact")
    lines += [
        f"font_size={int(lvl['font_size'])}",
        f"background_alpha={float(lvl['background_alpha']):.2f}",
        f"text_color={lvl['text_color']}",
        f"background_color={lvl['background_color']}",
        f"offset_x={int(lvl['offset_x'])}",
        f"offset_y={int(lvl['offset_y'])}",
        "round_corners=8",
    ]
    return lines


def write_mangohud(state):
    MANGO_DIR.mkdir(parents=True, exist_ok=True)
    presets = ["# Managed by Zach Center (ZachOS). Edit levels with `zach-center`."]
    for lid in level_ids(state):
        lvl = state["levels"][lid]
        presets.append(f"\n# Level {lid}: {lvl['name']}\n[preset {lid}]")
        presets += render_preset(lvl)
    (MANGO_DIR / "presets.conf").write_text("\n".join(presets) + "\n")

    conf = [
        "# Managed by Zach Center (ZachOS). Edit with `zach-center` or `zach-overlay`.",
        f"preset={','.join(level_cycle(state))}",
        f"toggle_hud={state['toggle_hud']}",
        f"toggle_preset={state['toggle_preset']}",
        "reload_cfg=Shift_L+F4",
        f"fps_limit={int(state['fps_limit'])}",
    ]
    # write this one last, mangohud reloads when it changes
    (MANGO_DIR / "MangoHud.conf").write_text("\n".join(conf) + "\n")


def save(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2) + "\n")
    write_mangohud(state)


def level_name(state, lid):
    lid = str(lid)
    return "Off" if lid == "0" else state["levels"][lid]["name"]


USAGE = """usage: zach-overlay [status | list | level <N|off> | next | reset]

  status        show the current overlay level and hotkeys
  list          list every overlay level
  level N       show level N in games (0 or "off" hides the overlay); applies live
  next          switch to the next level
  reset         restore the default ZachOS levels
"""


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    state = load()
    cmd = argv[0] if argv else "status"
    if cmd in ("-h", "--help", "help"):
        print(USAGE, end="")
    elif cmd == "status":
        s = state["start_level"]
        print(f"Overlay level: {s} ({level_name(state, s)})")
        print(f"Show/hide hotkey:  {state['toggle_hud']}")
        print(f"Next level hotkey: {state['toggle_preset']}")
        print(f"FPS limit: {state['fps_limit'] or 'unlimited'}")
    elif cmd == "list":
        print("  0  Off")
        for lid in level_ids(state):
            print(f"  {lid}  {state['levels'][lid]['name']}")
    elif cmd == "level" and len(argv) == 2:
        lid = "0" if argv[1].lower() == "off" else argv[1]
        if lid != "0" and lid not in state["levels"]:
            sys.exit(f"zach-overlay: no level {lid} (try `zach-overlay list`)")
        state["start_level"] = int(lid)
        save(state)
        print(f"Overlay level set to {lid} ({level_name(state, lid)})")
    elif cmd == "next":
        cycle = level_cycle(state)
        nxt = cycle[1 % len(cycle)]
        state["start_level"] = int(nxt)
        save(state)
        print(f"Overlay level set to {nxt} ({level_name(state, nxt)})")
    elif cmd == "reset":
        save(default_state())
        print("Overlay levels reset to ZachOS defaults")
    else:
        sys.exit(USAGE)


if __name__ == "__main__":
    main()
