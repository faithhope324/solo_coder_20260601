from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


class EventType(Enum):
    KEY_PRESS = "key_press"
    KEY_RELEASE = "key_release"
    MOUSE_CLICK = "mouse_click"
    MOUSE_MOVE = "mouse_move"
    MOUSE_SCROLL = "mouse_scroll"


class MouseButton(Enum):
    LEFT = "left"
    RIGHT = "right"
    MIDDLE = "middle"


@dataclass
class MacroEvent:
    event_type: EventType
    delay_ms: int = 0
    key: Optional[str] = None
    is_combination: bool = False
    combination_keys: List[str] = field(default_factory=list)
    mouse_button: Optional[MouseButton] = None
    mouse_position: Optional[Tuple[int, int]] = None
    pressed: bool = True
    scroll_dx: int = 0
    scroll_dy: int = 0

    def get_display_name(self) -> str:
        if self.event_type == EventType.KEY_PRESS:
            if self.is_combination:
                return f"[组合键] {'+'.join(self.combination_keys)}"
            return f"[按键] {self._format_key(self.key)}"
        elif self.event_type == EventType.KEY_RELEASE:
            return f"[释放] {self._format_key(self.key)}"
        elif self.event_type == EventType.MOUSE_CLICK:
            btn = self.mouse_button.value if self.mouse_button else "unknown"
            action = "按下" if self.pressed else "释放"
            pos = f" ({self.mouse_position[0]}, {self.mouse_position[1]})" if self.mouse_position else ""
            return f"[鼠标] {action} {btn}{pos}"
        elif self.event_type == EventType.MOUSE_MOVE:
            return f"[移动] ({self.mouse_position[0]}, {self.mouse_position[1]})"
        elif self.event_type == EventType.MOUSE_SCROLL:
            return f"[滚轮] dx={self.scroll_dx}, dy={self.scroll_dy}"
        return "未知事件"

    def _format_key(self, key: Optional[str]) -> str:
        if not key:
            return ""
        key_map = {
            "Key.ctrl": "Ctrl",
            "Key.ctrl_l": "Ctrl (左)",
            "Key.ctrl_r": "Ctrl (右)",
            "Key.alt": "Alt",
            "Key.alt_l": "Alt (左)",
            "Key.alt_r": "Alt (右)",
            "Key.shift": "Shift",
            "Key.shift_l": "Shift (左)",
            "Key.shift_r": "Shift (右)",
            "Key.enter": "Enter",
            "Key.space": "Space",
            "Key.backspace": "Backspace",
            "Key.tab": "Tab",
            "Key.esc": "Esc",
            "Key.up": "↑",
            "Key.down": "↓",
            "Key.left": "←",
            "Key.right": "→",
            "Key.caps_lock": "CapsLock",
            "Key.num_lock": "NumLock",
            "Key.insert": "Insert",
            "Key.delete": "Delete",
            "Key.home": "Home",
            "Key.end": "End",
            "Key.page_up": "PageUp",
            "Key.page_down": "PageDown",
            "Key.f1": "F1",
            "Key.f2": "F2",
            "Key.f3": "F3",
            "Key.f4": "F4",
            "Key.f5": "F5",
            "Key.f6": "F6",
            "Key.f7": "F7",
            "Key.f8": "F8",
            "Key.f9": "F9",
            "Key.f10": "F10",
            "Key.f11": "F11",
            "Key.f12": "F12",
        }
        if key.startswith("'") and key.endswith("'"):
            return key[1:-1]
        if key.startswith('"') and key.endswith('"'):
            return key[1:-1]
        return key_map.get(key, key)


@dataclass
class Macro:
    name: str
    events: List[MacroEvent] = field(default_factory=list)
    record_mouse: bool = False
    created_at: Optional[str] = None
    modified_at: Optional[str] = None

    def add_event(self, event: MacroEvent):
        self.events.append(event)

    def insert_event(self, index: int, event: MacroEvent):
        if 0 <= index <= len(self.events):
            self.events.insert(index, event)

    def remove_event(self, index: int) -> Optional[MacroEvent]:
        if 0 <= index < len(self.events):
            return self.events.pop(index)
        return None

    def update_event_delay(self, index: int, delay_ms: int) -> bool:
        if 0 <= index < len(self.events):
            self.events[index].delay_ms = max(0, delay_ms)
            return True
        return False

    def get_total_duration_ms(self) -> int:
        return sum(event.delay_ms for event in self.events)

    def clear(self):
        self.events.clear()

    def clone(self) -> "Macro":
        from copy import deepcopy
        return deepcopy(self)
