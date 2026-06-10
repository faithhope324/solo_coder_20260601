import time
import threading
from typing import List, Callable, Optional, Set
from pynput import keyboard, mouse

from event_store import Macro, MacroEvent, EventType, MouseButton


class InputListener:
    def __init__(self):
        self._recording = False
        self._paused = False
        self._macro: Optional[Macro] = None
        self._last_event_time: float = 0
        self._pressed_keys: Set[str] = set()
        self._combination_keys: List[str] = []
        self._combination_start_time: float = 0
        self._combination_timeout: float = 0.3
        self._keyboard_listener: Optional[keyboard.Listener] = None
        self._mouse_listener: Optional[mouse.Listener] = None
        self._record_mouse: bool = False
        self._stop_event = threading.Event()
        self._event_callback: Optional[Callable[[MacroEvent], None]] = None

    def start_recording(self, macro_name: str = "新宏", record_mouse: bool = False) -> Macro:
        self._macro = Macro(name=macro_name, record_mouse=record_mouse)
        self._record_mouse = record_mouse
        self._recording = True
        self._paused = False
        self._last_event_time = time.time()
        self._pressed_keys.clear()
        self._combination_keys.clear()
        self._stop_event.clear()

        self._keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )
        self._keyboard_listener.daemon = True
        self._keyboard_listener.start()

        if record_mouse:
            self._mouse_listener = mouse.Listener(
                on_click=self._on_mouse_click,
                on_move=self._on_mouse_move,
                on_scroll=self._on_mouse_scroll
            )
            self._mouse_listener.daemon = True
            self._mouse_listener.start()

        return self._macro

    def stop_recording(self) -> Optional[Macro]:
        self._recording = False
        self._stop_event.set()

        if self._keyboard_listener:
            self._keyboard_listener.stop()
            self._keyboard_listener = None

        if self._mouse_listener:
            self._mouse_listener.stop()
            self._mouse_listener = None

        return self._macro

    def pause_recording(self):
        self._paused = True

    def resume_recording(self):
        self._paused = False
        self._last_event_time = time.time()

    def is_recording(self) -> bool:
        return self._recording and not self._paused

    def set_event_callback(self, callback: Callable[[MacroEvent], None]):
        self._event_callback = callback

    def _get_delay_ms(self) -> int:
        now = time.time()
        delay = int((now - self._last_event_time) * 1000)
        self._last_event_time = now
        return max(0, delay)

    def _key_to_string(self, key) -> str:
        try:
            if hasattr(key, 'char') and key.char is not None:
                return repr(key.char)
            return str(key)
        except Exception:
            return str(key)

    def _is_modifier_key(self, key_str: str) -> bool:
        modifiers = [
            "Key.ctrl", "Key.ctrl_l", "Key.ctrl_r",
            "Key.alt", "Key.alt_l", "Key.alt_r",
            "Key.shift", "Key.shift_l", "Key.shift_r",
            "Key.cmd", "Key.cmd_l", "Key.cmd_r"
        ]
        return key_str in modifiers

    def _on_key_press(self, key):
        if not self._recording or self._paused:
            return

        try:
            key_str = self._key_to_string(key)

            if key_str in self._pressed_keys:
                return

            self._pressed_keys.add(key_str)

            if self._is_modifier_key(key_str):
                if not self._combination_keys:
                    self._combination_start_time = time.time()
                self._combination_keys.append(key_str)
                return

            delay_ms = self._get_delay_ms()

            if self._combination_keys:
                time_since_comb_start = time.time() - self._combination_start_time
                if time_since_comb_start < self._combination_timeout:
                    self._combination_keys.append(key_str)
                    event = MacroEvent(
                        event_type=EventType.KEY_PRESS,
                        delay_ms=delay_ms,
                        is_combination=True,
                        combination_keys=list(self._combination_keys)
                    )
                    self._macro.add_event(event)
                    if self._event_callback:
                        self._event_callback(event)
                    self._combination_keys.clear()
                    return

            event = MacroEvent(
                event_type=EventType.KEY_PRESS,
                delay_ms=delay_ms,
                key=key_str
            )
            self._macro.add_event(event)
            if self._event_callback:
                self._event_callback(event)

        except Exception as e:
            print(f"按键按下处理错误: {e}")

    def _on_key_release(self, key):
        if not self._recording or self._paused:
            return

        try:
            key_str = self._key_to_string(key)
            if key_str in self._pressed_keys:
                self._pressed_keys.remove(key_str)

            if self._is_modifier_key(key_str):
                if key_str in self._combination_keys:
                    self._combination_keys.remove(key_str)

        except Exception as e:
            print(f"按键释放处理错误: {e}")

    def _on_mouse_click(self, x, y, button, pressed):
        if not self._recording or self._paused or not self._record_mouse:
            return

        try:
            delay_ms = self._get_delay_ms()
            button_map = {
                mouse.Button.left: MouseButton.LEFT,
                mouse.Button.right: MouseButton.RIGHT,
                mouse.Button.middle: MouseButton.MIDDLE,
            }
            btn = button_map.get(button)
            event = MacroEvent(
                event_type=EventType.MOUSE_CLICK,
                delay_ms=delay_ms,
                mouse_button=btn,
                mouse_position=(x, y),
                pressed=pressed
            )
            self._macro.add_event(event)
            if self._event_callback:
                self._event_callback(event)

        except Exception as e:
            print(f"鼠标点击处理错误: {e}")

    def _on_mouse_move(self, x, y):
        if not self._recording or self._paused or not self._record_mouse:
            return

        try:
            delay_ms = self._get_delay_ms()
            if delay_ms >= 50:
                event = MacroEvent(
                    event_type=EventType.MOUSE_MOVE,
                    delay_ms=delay_ms,
                    mouse_position=(x, y)
                )
                self._macro.add_event(event)
                if self._event_callback:
                    self._event_callback(event)
                self._last_event_time = time.time()

        except Exception as e:
            print(f"鼠标移动处理错误: {e}")

    def _on_mouse_scroll(self, x, y, dx, dy):
        if not self._recording or self._paused or not self._record_mouse:
            return

        try:
            delay_ms = self._get_delay_ms()
            event = MacroEvent(
                event_type=EventType.MOUSE_SCROLL,
                delay_ms=delay_ms,
                mouse_position=(x, y),
                scroll_dx=dx,
                scroll_dy=dy
            )
            self._macro.add_event(event)
            if self._event_callback:
                self._event_callback(event)

        except Exception as e:
            print(f"鼠标滚轮处理错误: {e}")
