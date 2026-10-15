"""
Control Panel Window for Marvel Avengers Hanging Animations.
Modern dark futuristic Avengers themed GUI using PyQt6.
"""

import math
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QColor, QFont, QIcon, QPixmap, QPainter, QBrush, QPen
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSlider, QCheckBox, QLineEdit, QComboBox, QScrollArea, QGridLayout,
    QFrame, QGroupBox, QSplitter
)

from animations.preset_manager import PresetManager
from animations.renderers import VectorRenderer


class PresetCard(QFrame):
    toggled_preset = pyqtSignal(dict, bool)  # preset, active state

    def __init__(self, preset, is_active=False, parent=None):
        super().__init__(parent)
        self.preset = preset
        self.is_active = is_active
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(self._get_style())
        self.init_ui()

    def _get_style(self):
        if self.is_active:
            return """
            PresetCard {
                background-color: rgba(0, 229, 255, 0.15);
                border: 2px solid #00E5FF;
                border-radius: 8px;
            }
            """
        else:
            return """
            PresetCard {
                background-color: rgba(30, 35, 45, 0.85);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
            }
            PresetCard:hover {
                border: 1px solid #00E5FF;
                background-color: rgba(0, 229, 255, 0.08);
            }
            """

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Icon Thumbnail Widget
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(48, 48)
        self.icon_label.setPixmap(self._generate_thumbnail())
        layout.addWidget(self.icon_label)

        # Info VBox
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        title_label = QLabel(self.preset["name"])
        title_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #FFFFFF;")
        info_layout.addWidget(title_label)

        cat_label = QLabel(f"Category: {self.preset['category']} | Effect: {self.preset['effect_type']}")
        cat_label.setFont(QFont("Segoe UI", 8))
        cat_label.setStyleSheet("color: #8A9BA8;")
        info_layout.addWidget(cat_label)

        layout.addLayout(info_layout)
        layout.addStretch()

        # Toggle Button
        self.toggle_btn = QPushButton("Active" if self.is_active else "Add")
        self.toggle_btn.setFixedSize(70, 30)
        self.toggle_btn.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.toggle_btn.setStyleSheet(self._get_btn_style())
        self.toggle_btn.clicked.connect(self._on_toggle)
        layout.addWidget(self.toggle_btn)

    def _get_btn_style(self):
        if self.is_active:
            return """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FF1744, stop:1 #D50000);
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: #FF5252;
            }
            """
        else:
            return """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00E5FF, stop:1 #0288D1);
                color: #050B14;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: #80D8FF;
            }
            """

    def set_active_state(self, active):
        self.is_active = active
        self.setStyleSheet(self._get_style())
        self.toggle_btn.setText("Active" if self.is_active else "Add")
        self.toggle_btn.setStyleSheet(self._get_btn_style())

    def _on_toggle(self):
        self.is_active = not self.is_active
        self.set_active_state(self.is_active)
        self.toggled_preset.emit(self.preset, self.is_active)

    def _generate_thumbnail(self):
        pix = QPixmap(48, 48)
        pix.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pix)
        renderer = VectorRenderer()
        renderer.draw_object(
            painter, 24, 24, size=32,
            render_type=self.preset["render_type"],
            primary_color=self.preset["primary_color"],
            secondary_color=self.preset["secondary_color"],
            accent_color=self.preset["accent_color"]
        )
        painter.end()
        return pix


class ControlPanelWindow(QMainWindow):
    # Signals to overlay
    start_stop_toggled = pyqtSignal(bool)
    speed_changed = pyqtSignal(float)
    count_changed = pyqtSignal(int)
    randomize_requested = pyqtSignal()
    reset_requested = pyqtSignal()
    transparency_changed = pyqtSignal(float)
    always_on_top_toggled = pyqtSignal(bool)
    desktop_mode_toggled = pyqtSignal(bool)
    preset_activated = pyqtSignal(dict)
    preset_deactivated = pyqtSignal(str)  # preset id

    def __init__(self, preset_manager: PresetManager, parent=None):
        super().__init__(parent)
        self.preset_manager = preset_manager
        self.active_preset_ids = set()
        self.is_running = True
        
        self.setWindowTitle("Marvel Avengers Hanging Animations - Control Panel")
        self.resize(900, 650)
        self.setStyleSheet(self._get_main_style())
        
        self.init_ui()

    def _get_main_style(self):
        return """
        QMainWindow {
            background-color: #0A0E17;
        }
        QWidget {
            color: #E1E6ED;
            font-family: 'Segoe UI', Tahoma, sans-serif;
        }
        QGroupBox {
            background-color: #121824;
            border: 1px solid #1E293B;
            border-radius: 8px;
            margin-top: 12px;
            font-weight: bold;
            font-size: 11px;
            color: #00E5FF;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
        }
        QLabel {
            color: #94A3B8;
            font-size: 12px;
        }
        QSlider::groove:horizontal {
            height: 6px;
            background: #1E293B;
            border-radius: 3px;
        }
        QSlider::sub-page:horizontal {
            background: #00E5FF;
            border-radius: 3px;
        }
        QSlider::handle:horizontal {
            background: #FFFFFF;
            width: 16px;
            margin-top: -5px;
            margin-bottom: -5px;
            border-radius: 8px;
        }
        QLineEdit, QComboBox {
            background-color: #1E293B;
            border: 1px solid #334155;
            border-radius: 6px;
            padding: 6px 12px;
            color: #F8FAFC;
        }
        QLineEdit:focus, QComboBox:focus {
            border: 1px solid #00E5FF;
        }
        QCheckBox {
            color: #E2E8F0;
            font-size: 12px;
        }
        QCheckBox::indicator {
            width: 18px;
            height: 18px;
            border-radius: 4px;
            border: 1px solid #334155;
            background-color: #1E293B;
        }
        QCheckBox::indicator:checked {
            background-color: #00E5FF;
            border-color: #00E5FF;
        }
        """

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Header Title
        header_layout = QHBoxLayout()
        title = QLabel("MARVEL AVENGERS HANGING ANIMATIONS")
        title.setFont(QFont("Impact", 18))
        title.setStyleSheet("color: #00E5FF; letter-spacing: 1px;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        self.start_btn = QPushButton("PAUSE ANIMATIONS" if self.is_running else "START ANIMATIONS")
        self.start_btn.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.start_btn.setFixedHeight(36)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FF1744, stop:1 #D50000);
                color: white; border: none; border-radius: 6px; padding: 0 16px;
            }
            QPushButton:hover { background: #FF5252; }
        """)
        self.start_btn.clicked.connect(self._toggle_start_stop)
        header_layout.addWidget(self.start_btn)
        
        main_layout.addLayout(header_layout)

        # Splitter Layout (Left: Controls Panel, Right: Presets Gallery)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left Panel Controls
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 8, 0)
        left_layout.setSpacing(10)

        # Group 1: Global Settings
        settings_group = QGroupBox("GLOBAL ANIMATION CONTROLS")
        sg_layout = QVBoxLayout(settings_group)
        
        # Speed Slider
        speed_box = QHBoxLayout()
        speed_label = QLabel("Animation Speed:")
        self.speed_val_lbl = QLabel("1.0x")
        self.speed_val_lbl.setStyleSheet("color: #00E5FF; font-weight: bold;")
        speed_box.addWidget(speed_label)
        speed_box.addStretch()
        speed_box.addWidget(self.speed_val_lbl)
        sg_layout.addLayout(speed_box)
        
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(2, 30)  # 0.2x to 3.0x
        self.speed_slider.setValue(10)
        self.speed_slider.valueChanged.connect(self._on_speed_changed)
        sg_layout.addWidget(self.speed_slider)

        # Number of Objects Slider
        count_box = QHBoxLayout()
        count_label = QLabel("Active Objects Count:")
        self.count_val_lbl = QLabel("8")
        self.count_val_lbl.setStyleSheet("color: #00E5FF; font-weight: bold;")
        count_box.addWidget(count_label)
        count_box.addStretch()
        count_box.addWidget(self.count_val_lbl)
        sg_layout.addLayout(count_box)

        self.count_slider = QSlider(Qt.Orientation.Horizontal)
        self.count_slider.setRange(1, 30)
        self.count_slider.setValue(8)
        self.count_slider.valueChanged.connect(self._on_count_changed)
        sg_layout.addWidget(self.count_slider)

        # Transparency Slider
        trans_box = QHBoxLayout()
        trans_label = QLabel("Overlay Transparency:")
        self.trans_val_lbl = QLabel("100%")
        self.trans_val_lbl.setStyleSheet("color: #00E5FF; font-weight: bold;")
        trans_box.addWidget(trans_label)
        trans_box.addStretch()
        trans_box.addWidget(self.trans_val_lbl)
        sg_layout.addLayout(trans_box)

        self.trans_slider = QSlider(Qt.Orientation.Horizontal)
        self.trans_slider.setRange(20, 100)
        self.trans_slider.setValue(100)
        self.trans_slider.valueChanged.connect(self._on_transparency_changed)
        sg_layout.addWidget(self.trans_slider)

        left_layout.addWidget(settings_group)

        # Group 2: Mode & Display Toggles
        mode_group = QGroupBox("WINDOW & DISPLAY OPTIONS")
        mg_layout = QVBoxLayout(mode_group)
        
        self.always_top_cb = QCheckBox("Always On Top")
        self.always_top_cb.setChecked(True)
        self.always_top_cb.toggled.connect(self.always_on_top_toggled.emit)
        mg_layout.addWidget(self.always_top_cb)

        self.desktop_mode_cb = QCheckBox("Fullscreen Desktop Span")
        self.desktop_mode_cb.setChecked(True)
        self.desktop_mode_cb.toggled.connect(self.desktop_mode_toggled.emit)
        mg_layout.addWidget(self.desktop_mode_cb)

        left_layout.addWidget(mode_group)

        # Group 3: Quick Action Buttons
        actions_group = QGroupBox("QUICK ACTIONS")
        ag_layout = QVBoxLayout(actions_group)

        self.rand_btn = QPushButton("🎲 Randomize Active Items")
        self.rand_btn.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.rand_btn.setStyleSheet("background-color: #1E293B; border: 1px solid #00E5FF; padding: 8px; border-radius: 6px;")
        self.rand_btn.clicked.connect(self.randomize_requested.emit)
        ag_layout.addWidget(self.rand_btn)

        self.reset_btn = QPushButton("🔄 Reset Default Overlay")
        self.reset_btn.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.reset_btn.setStyleSheet("background-color: #1E293B; border: 1px solid #64748B; padding: 8px; border-radius: 6px;")
        self.reset_btn.clicked.connect(self.reset_requested.emit)
        ag_layout.addWidget(self.reset_btn)

        left_layout.addWidget(actions_group)
        left_layout.addStretch()

        splitter.addWidget(left_widget)

        # Right Panel: Presets Gallery & Search/Filter
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(8, 0, 0, 0)

        # Search and Category Filters
        filter_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search 100+ animations (e.g. Iron Man, Shield, Stone)...")
        self.search_input.textChanged.connect(self._filter_presets)
        filter_layout.addWidget(self.search_input)

        self.category_combo = QComboBox()
        categories = ["All", "Avengers Core", "Cosmic & Infinity", "Spider-Verse", "Mystic & Magic", "Wakanda & Asgard", "Villains & Artifacts", "Guardians & Galactic"]
        self.category_combo.addItems(categories)
        self.category_combo.currentTextChanged.connect(self._filter_presets)
        filter_layout.addWidget(self.category_combo)

        right_layout.addLayout(filter_layout)

        # Scrollable Preset Gallery
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { background-color: transparent; border: none; }")

        self.gallery_container = QWidget()
        self.gallery_layout = QVBoxLayout(self.gallery_container)
        self.gallery_layout.setContentsMargins(0, 8, 0, 0)
        self.gallery_layout.setSpacing(8)

        self.scroll_area.setWidget(self.gallery_container)
        right_layout.addWidget(self.scroll_area)

        splitter.addWidget(right_widget)
        splitter.setSizes([320, 580])

        main_layout.addWidget(splitter)

        # Initial Load of Presets Gallery
        self._populate_gallery()

    def set_active_presets(self, preset_id_list):
        self.active_preset_ids = set(preset_id_list)
        self.count_val_lbl.setText(str(len(preset_id_list)))
        self.count_slider.blockSignals(True)
        self.count_slider.setValue(len(preset_id_list))
        self.count_slider.blockSignals(False)
        self._update_card_states()

    def _populate_gallery(self):
        # Clear existing cards
        while self.gallery_layout.count():
            child = self.gallery_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        all_presets = self.preset_manager.get_all_presets()
        self.cards = []

        for p in all_presets:
            is_act = p["id"] in self.active_preset_ids
            card = PresetCard(p, is_active=is_act)
            card.toggled_preset.connect(self._on_preset_toggled)
            self.cards.append(card)
            self.gallery_layout.addWidget(card)

        self.gallery_layout.addStretch()

    def _filter_presets(self):
        query = self.search_input.text()
        category = self.category_combo.currentText()
        filtered = self.preset_manager.search_presets(query, category)
        filtered_ids = {p["id"] for p in filtered}

        for card in self.cards:
            if card.preset["id"] in filtered_ids:
                card.show()
            else:
                card.hide()

    def _update_card_states(self):
        for card in self.cards:
            is_act = card.preset["id"] in self.active_preset_ids
            card.set_active_state(is_act)

    def _on_preset_toggled(self, preset, active):
        if active:
            self.active_preset_ids.add(preset["id"])
            self.preset_activated.emit(preset)
        else:
            self.active_preset_ids.discard(preset["id"])
            self.preset_deactivated.emit(preset["id"])
        self.count_val_lbl.setText(str(len(self.active_preset_ids)))

    def _toggle_start_stop(self):
        self.is_running = not self.is_running
        self.start_btn.setText("PAUSE ANIMATIONS" if self.is_running else "START ANIMATIONS")
        self.start_btn.setStyleSheet(
            """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FF1744, stop:1 #D50000);
                color: white; border: none; border-radius: 6px; padding: 0 16px;
            }
            QPushButton:hover { background: #FF5252; }
            """ if self.is_running else
            """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00E5FF, stop:1 #0288D1);
                color: #050B14; border: none; border-radius: 6px; padding: 0 16px;
            }
            QPushButton:hover { background: #80D8FF; }
            """
        )
        self.start_stop_toggled.emit(self.is_running)

    def _on_speed_changed(self, value):
        spd = value / 10.0
        self.speed_val_lbl.setText(f"{spd:.1f}x")
        self.speed_changed.emit(spd)

    def _on_count_changed(self, value):
        self.count_val_lbl.setText(str(value))
        self.count_changed.emit(value)

    def _on_transparency_changed(self, value):
        trans = value / 100.0
        self.trans_val_lbl.setText(f"{value}%")
        self.transparency_changed.emit(trans)

    def closeEvent(self, event):
        # Minimize to system tray on close instead of exiting application completely
        self.hide()
        event.ignore()
