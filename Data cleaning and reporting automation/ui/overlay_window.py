"""
Transparent Desktop Overlay Window for Marvel Avengers Hanging Animations.
Handles 60 FPS animation loop, Win32 mouse passthrough hit-testing,
drag and drop physics, particles, special click effects, and System Tray icon.
"""

import sys
import ctypes
import math
import random
from PyQt6.QtCore import Qt, QTimer, QPoint, QRectF, QPointF
from PyQt6.QtGui import QPainter, QColor, QKeySequence, QShortcut, QIcon, QPixmap, QCursor
from PyQt6.QtWidgets import QWidget, QApplication, QSystemTrayIcon, QMenu

from animations.physics import PendulumPhysics
from animations.renderers import VectorRenderer
from animations.particles import ParticleSystem
from animations.effects import EffectEngine
from animations.preset_manager import PresetManager

# Win32 API Constants for Transparent Overlay Mouse Passthrough
GWL_EXSTYLE = -20
WS_EX_TRANSPARENT = 0x00000020
WS_EX_LAYERED = 0x00080000


class HangingObject:
    def __init__(self, preset, anchor_x, screen_height):
        self.preset = preset
        self.physics = PendulumPhysics(
            anchor_x=anchor_x,
            anchor_y=0,
            length=preset.get("length", 240),
            mass=preset.get("mass", 1.0),
            damping=preset.get("damping", 0.015)
        )
        self.size = 64.0
        self.hovered = False

    def get_bounds(self):
        bx, by = self.physics.get_bob_position()
        r = self.size * 0.7
        return QRectF(bx - r, by - r, r * 2, r * 2)

    def contains_point(self, px, py):
        bx, by = self.physics.get_bob_position()
        dist = math.hypot(px - bx, py - by)
        return dist <= (self.size * 0.8)


class TransparentOverlayWindow(QWidget):
    def __init__(self, preset_manager: PresetManager):
        super().__init__()
        self.preset_manager = preset_manager
        
        # Overlay options
        self.is_running = True
        self.speed_multiplier = 1.0
        self.overlay_opacity = 1.0
        self.desktop_mode = True
        self.passthrough_mode = False  # Track current Win32 transparent status
        
        # Engines
        self.renderer = VectorRenderer()
        self.particle_system = ParticleSystem()
        self.effect_engine = EffectEngine()
        
        # Active hanging items
        self.hanging_objects = []
        self.dragged_object = None

        self.init_window_flags()
        self.init_system_tray()
        self.init_shortcuts()
        
        # 60 FPS Render Timer (~16 ms)
        self.timer = QTimer(self)
        self.timer.setInterval(16)
        self.timer.timeout.connect(self.game_loop)
        self.timer.start()

        # Initial default preset spawn
        self.load_default_presets(8)

    def init_window_flags(self):
        # Frameless, translucent background, stays on top, tool window (no taskbar item)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setMouseTracking(True)
        
        self.update_geometry()

    def update_geometry(self):
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.geometry()
            self.setGeometry(geo)

    def set_always_on_top(self, always_top):
        flags = self.windowFlags()
        if always_top:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.show()

    def load_default_presets(self, count=8):
        presets = self.preset_manager.get_all_presets()
        selected = random.sample(presets, min(count, len(presets)))
        self.set_active_presets(selected)

    def set_active_presets(self, presets_list):
        screen_w = self.width() if self.width() > 0 else 1920
        spacing = screen_w / (len(presets_list) + 1)
        
        new_objects = []
        for i, preset in enumerate(presets_list):
            anchor_x = spacing * (i + 1) + random.uniform(-20, 20)
            obj = HangingObject(preset, anchor_x, self.height())
            new_objects.append(obj)
            
        self.hanging_objects = new_objects

    def add_preset(self, preset):
        anchor_x = random.uniform(100, self.width() - 100) if self.width() > 200 else 400
        obj = HangingObject(preset, anchor_x, self.height())
        self.hanging_objects.append(obj)

    def remove_preset_by_id(self, preset_id):
        self.hanging_objects = [o for o in self.hanging_objects if o.preset["id"] != preset_id]

    def randomize_objects(self):
        count = len(self.hanging_objects) if self.hanging_objects else 8
        self.load_default_presets(count)

    def init_system_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        pix = QPixmap(32, 32)
        pix.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pix)
        self.renderer.draw_object(painter, 16, 16, size=24, render_type="avengers_logo", primary_color="#00E5FF", secondary_color="#FF1744")
        painter.end()
        
        self.tray_icon.setIcon(QIcon(pix))
        self.tray_icon.setToolTip("Marvel Avengers Hanging Animations")
        
        tray_menu = QMenu()
        control_act = tray_menu.addAction("Control Panel")
        control_act.triggered.connect(self.show_control_panel_requested)
        
        pause_act = tray_menu.addAction("Pause / Resume Animations")
        pause_act.triggered.connect(self.toggle_pause)
        
        rand_act = tray_menu.addAction("Randomize Presets")
        rand_act.triggered.connect(self.randomize_objects)
        
        tray_menu.addSeparator()
        exit_act = tray_menu.addAction("Exit App")
        exit_act.triggered.connect(QApplication.quit)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def show_control_panel_requested(self):
        if hasattr(self, 'control_panel') and self.control_panel:
            self.control_panel.show()
            self.control_panel.activateWindow()

    def init_shortcuts(self):
        esc_shortcut = QShortcut(QKeySequence("Esc"), self)
        esc_shortcut.activated.connect(self.on_esc_pressed)

    def on_esc_pressed(self):
        self.show_control_panel_requested()

    def toggle_pause(self):
        self.is_running = not self.is_running

    def _update_win32_mouse_passthrough(self, cursor_x, cursor_y):
        """
        Win32 Hit-Testing:
        If cursor is over any hanging item, clear WS_EX_TRANSPARENT so PyQt receives hover/clicks.
        If cursor is over empty desktop, set WS_EX_TRANSPARENT so mouse clicks pass to background apps!
        """
        if sys.platform != "win32":
            return

        is_hovering_any = any(obj.contains_point(cursor_x, cursor_y) for obj in self.hanging_objects)
        if self.dragged_object is not None:
            is_hovering_any = True

        hwnd = int(self.winId())
        if is_hovering_any and self.passthrough_mode:
            # Disable passthrough so window gets mouse events
            ex_style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex_style & ~WS_EX_TRANSPARENT)
            self.passthrough_mode = False
        elif not is_hovering_any and not self.passthrough_mode:
            # Enable passthrough so clicks go through to desktop
            ex_style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex_style | WS_EX_TRANSPARENT)
            self.passthrough_mode = True

    def game_loop(self):
        if not self.is_running:
            self.update()
            return

        dt = 0.016
        cursor_pos = QCursor.pos()
        local_pos = self.mapFromGlobal(cursor_pos)
        
        # Check Win32 passthrough state
        self._update_win32_mouse_passthrough(local_pos.x(), local_pos.y())

        # Update Hanging Objects Physics
        for obj in self.hanging_objects:
            obj.physics.update(dt, speed_multiplier=self.speed_multiplier)
            
            # Hover check
            is_hover = obj.contains_point(local_pos.x(), local_pos.y())
            if is_hover and not obj.hovered:
                obj.hovered = True
                obj.physics.apply_hover_excite()
                bx, by = obj.physics.get_bob_position()
                self.particle_system.spawn_burst(
                    bx, by, count=10, p_type=obj.preset["particle_type"],
                    base_color=obj.preset["particle_color"], speed=80.0
                )
            elif not is_hover:
                obj.hovered = False

            # Spawn subtle ambient particles around active objects
            if random.random() < 0.08:
                bx, by = obj.physics.get_bob_position()
                self.particle_system.spawn_burst(
                    bx, by, count=1, p_type=obj.preset["particle_type"],
                    base_color=obj.preset["particle_color"], speed=30.0
                )

        # Update ambient dust particles
        self.particle_system.spawn_ambient(self.width(), self.height(), count=1)
        self.particle_system.update(dt)
        self.effect_engine.update(dt)

        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position()
            for obj in self.hanging_objects:
                if obj.contains_point(pos.x(), pos.y()):
                    self.dragged_object = obj
                    obj.physics.start_drag(pos.x(), pos.y())
                    
                    # Trigger Click Special Effect!
                    bx, by = obj.physics.get_bob_position()
                    self.effect_engine.trigger_effect(
                        obj.preset["effect_type"], bx, by,
                        primary_color=obj.preset["primary_color"],
                        secondary_color=obj.preset["secondary_color"]
                    )
                    self.particle_system.spawn_burst(
                        bx, by, count=35, p_type=obj.preset["particle_type"],
                        base_color=obj.preset["particle_color"], speed=220.0
                    )
                    obj.physics.apply_impulse(random.choice([-8.0, 8.0]))
                    break

    def mouseMoveEvent(self, event):
        pos = event.position()
        if self.dragged_object:
            self.dragged_object.physics.update_drag(pos.x(), pos.y())

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.dragged_object:
            self.dragged_object.physics.stop_drag()
            self.dragged_object = None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self.overlay_opacity < 1.0:
            painter.setOpacity(self.overlay_opacity)

        # 1. Draw Active Visual Special Effects (Lightning, Portals, Shockwaves)
        self.effect_engine.draw(painter)

        # 2. Draw Floating Particles
        self.particle_system.draw(painter)

        # 3. Draw Hanging Objects & Tethers
        for obj in self.hanging_objects:
            phys = obj.physics
            bx, by = phys.get_bob_position()
            
            # Draw Tether (String, Chain, Web, Laser, Bifrost)
            self.renderer.draw_tether(
                painter, phys.anchor_x, phys.anchor_y, bx, by,
                tether_type=obj.preset["tether_type"],
                tether_color=obj.preset["tether_color"]
            )
            
            # Draw Object Graphic
            self.renderer.draw_object(
                painter, bx, by, size=obj.size,
                render_type=obj.preset["render_type"],
                primary_color=obj.preset["primary_color"],
                secondary_color=obj.preset["secondary_color"],
                accent_color=obj.preset["accent_color"],
                glow_intensity=phys.glow_intensity,
                scale=phys.scale_pulse
            )
