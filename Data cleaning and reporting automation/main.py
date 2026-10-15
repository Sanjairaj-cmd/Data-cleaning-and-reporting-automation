"""
Marvel Avengers Hanging Animations - Main Application Entry Point.
Transparent Desktop Overlay for Windows 10/11 with 100+ Presets & Low CPU usage.
"""

import sys
import os
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from animations.preset_manager import PresetManager
from ui.overlay_window import TransparentOverlayWindow
from ui.control_panel import ControlPanelWindow


def main():
    # Enable High DPI Scaling & Hardware Acceleration
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    app.setApplicationName("Marvel Avengers Hanging Animations")
    app.setQuitOnLastWindowClosed(False)

    # Initialize Preset Manager (100+ Marvel presets)
    preset_manager = PresetManager()

    # Create Overlay Window
    overlay = TransparentOverlayWindow(preset_manager)
    overlay.show()

    # Create Control Panel Window
    control_panel = ControlPanelWindow(preset_manager)
    overlay.control_panel = control_panel

    # Connect Control Panel signals to Overlay Window
    control_panel.start_stop_toggled.connect(lambda running: setattr(overlay, 'is_running', running))
    control_panel.speed_changed.connect(lambda spd: setattr(overlay, 'speed_multiplier', spd))
    control_panel.transparency_changed.connect(lambda trans: setattr(overlay, 'overlay_opacity', trans))
    control_panel.always_on_top_toggled.connect(overlay.set_always_on_top)
    control_panel.randomize_requested.connect(overlay.randomize_objects)
    
    def on_count_changed(count):
        all_p = preset_manager.get_all_presets()
        import random
        selected = random.sample(all_p, min(count, len(all_p)))
        overlay.set_active_presets(selected)
        control_panel.set_active_presets([p["id"] for p in selected])

    def on_reset_requested():
        overlay.load_default_presets(8)
        act_ids = [o.preset["id"] for o in overlay.hanging_objects]
        control_panel.set_active_presets(act_ids)

    def on_preset_activated(preset):
        overlay.add_preset(preset)

    def on_preset_deactivated(preset_id):
        overlay.remove_preset_by_id(preset_id)

    control_panel.count_changed.connect(on_count_changed)
    control_panel.reset_requested.connect(on_reset_requested)
    control_panel.preset_activated.connect(on_preset_activated)
    control_panel.preset_deactivated.connect(on_preset_deactivated)

    # Sync initial active presets to Control Panel UI
    initial_ids = [o.preset["id"] for o in overlay.hanging_objects]
    control_panel.set_active_presets(initial_ids)

    # Show Control Panel on Startup
    control_panel.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
