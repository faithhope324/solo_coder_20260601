import time
import threading
from typing import Optional, Callable
from pynput import keyboard, mouse
from pynput.keyboard import Controller as KeyboardController, Key
from pynput.mouse import Controller as MouseController, Button

from event_store import Macro, MacroEvent, EventType, MouseButton


class MacroPlayer:
    def __init__(self):
        self._playing = False
        self._paused = False
        self._stop_requested = False
        self._play_thread: Optional[threading.Thread] = None
        self._keyboard_ctrl = KeyboardController()
        self._mouse_ctrl = MouseController()
        self._stop_hotkey_listener: Optional[keyboard.GlobalHotKeys] = None
        self._stop_callback: Optional[Callable[[], None]] = None
        self._progress_callback: Optional[Callable[[int, int, int], None]] = None
        self._current_loop: int = 0
        self._total_loops: int = 1
        self._current_event_index: int = 0

    def play(self, macro: Macro, loops: int = 1, speed_multiplier: float = 1.0):
        if self._playing:
            return

        self._playing = True
        self._paused = False
        self._stop_requested = False
        self._current_loop = 0
        self._total_loops = max(1, loops) if loops > 0 else -1
        self._current_event_index = 0

        self._play_thread = threading.Thread(
            target=self._play_worker,
            args=(macro, speed_multiplier),
            daemon=True
        )
        self._play_thread.start()

    def stop(self):
        self._stop_requested = True
        self._paused = False
        if self._stop_hotkey_listener:
            self._stop_hotkey_listener.stop()
            self._stop_hotkey_listener = None

    def pause(self):
        self._paused = True

    def resume(self):
        self._paused = False

    def is_playing(self) -> bool:
        return self._playing

    def is_paused(self) -> bool:
        return self._paused

    def set_stop_callback(self, callback: Callable[[], None]):
        self._stop_callback = callback

    def set_progress_callback(self, callback: Callable[[int, int, int], None]):
        self._progress_callback = callback

    def set_stop_hotkey(self, hotkey: str):
        if self._stop_hotkey_listener:
            self._stop_hotkey_listener.stop()

        def on_stop():
            self.stop()
            if self._stop_callback:
                self._stop_callback()

        try:
            self._stop_hotkey_listener = keyboard.GlobalHotKeys({
                hotkey: on_stop
            })
            self._stop_hotkey_listener.daemon = True
            self._stop_hotkey_listener.start()
        except Exception as e:
            print(f"设置停止热键失败: {e}")

    def _play_worker(self, macro: Macro, speed_multiplier: float):
        try:
            loop_count = 0
            while not self._stop_requested:
                if self._total_loops > 0 and loop_count >= self._total_loops:
                    break

                self._current_loop = loop_count + 1
                self._current_event_index = 0

                for i, event in enumerate(macro.events):
                    if self._stop_requested:
                        break

                    while self._paused and not self._stop_requested:
                        time.sleep(0.1)

                    if self._stop_requested:
                        break

                    self._current_event_index = i

                    delay_ms = event.delay_ms
                    if speed_multiplier > 0:
                        delay_ms = int(delay_ms / speed_multiplier)

                    if delay_ms > 0:
                        time.sleep(delay_ms / 1000.0)

                    self._execute_event(event)

                    if self._progress_callback:
                        self._progress_callback(
                            loop_count + 1,
                            i + 1,
                            len(macro.events)
                        )

                loop_count += 1

        except Exception as e:
            print(f"播放宏时出错: {e}")
        finally:
            self._playing = False
            self._paused = False
            if self._stop_hotkey_listener:
                self._stop_hotkey_listener.stop()
                self._stop_hotkey_listener = None
            if self._stop_callback:
                self._stop_callback()

    def _execute_event(self, event: MacroEvent):
        try:
            if event.event_type == EventType.KEY_PRESS:
                self._execute_key_press(event)
            elif event.event_type == EventType.KEY_RELEASE:
                self._execute_key_release(event)
            elif event.event_type == EventType.MOUSE_CLICK:
                self._execute_mouse_click(event)
            elif event.event_type == EventType.MOUSE_MOVE:
                self._execute_mouse_move(event)
            elif event.event_type == EventType.MOUSE_SCROLL:
                self._execute_mouse_scroll(event)
        except Exception as e:
            print(f"执行事件出错: {e}")

    def _string_to_key(self, key_str: str):
        if not key_str:
            return None

        try:
            key_map = {
                "Key.ctrl": Key.ctrl,
                "Key.ctrl_l": Key.ctrl_l,
                "Key.ctrl_r": Key.ctrl_r,
                "Key.alt": Key.alt,
                "Key.alt_l": Key.alt_l,
                "Key.alt_r": Key.alt_r,
                "Key.shift": Key.shift,
                "Key.shift_l": Key.shift_l,
                "Key.shift_r": Key.shift_r,
                "Key.enter": Key.enter,
                "Key.space": Key.space,
                "Key.backspace": Key.backspace,
                "Key.tab": Key.tab,
                "Key.esc": Key.esc,
                "Key.up": Key.up,
                "Key.down": Key.down,
                "Key.left": Key.left,
                "Key.right": Key.right,
                "Key.caps_lock": Key.caps_lock,
                "Key.num_lock": Key.num_lock,
                "Key.insert": Key.insert,
                "Key.delete": Key.delete,
                "Key.home": Key.home,
                "Key.end": Key.end,
                "Key.page_up": Key.page_up,
                "Key.page_down": Key.page_down,
                "Key.f1": Key.f1,
                "Key.f2": Key.f2,
                "Key.f3": Key.f3,
                "Key.f4": Key.f4,
                "Key.f5": Key.f5,
                "Key.f6": Key.f6,
                "Key.f7": Key.f7,
                "Key.f8": Key.f8,
                "Key.f9": Key.f9,
                "Key.f10": Key.f10,
                "Key.f11": Key.f11,
                "Key.f12": Key.f12,
            }

            if key_str in key_map:
                return key_map[key_str]

            if key_str.startswith("'") and key_str.endswith("'") and len(key_str) >= 3:
                return key_str[1:-1]
            if key_str.startswith('"') and key_str.endswith('"') and len(key_str) >= 3:
                return key_str[1:-1]

            return key_str

        except Exception:
            return key_str

    def _mouse_button_to_pynput(self, button: Optional[MouseButton]):
        if button == MouseButton.LEFT:
            return Button.left
        elif button == MouseButton.RIGHT:
            return Button.right
        elif button == MouseButton.MIDDLE:
            return Button.middle
        return Button.left

    def _execute_key_press(self, event: MacroEvent):
        if event.is_combination and event.combination_keys:
            keys = [self._string_to_key(k) for k in event.combination_keys]
            keys = [k for k in keys if k is not None]

            for k in keys:
                self._keyboard_ctrl.press(k)

            for k in reversed(keys):
                self._keyboard_ctrl.release(k)
        elif event.key:
            key = self._string_to_key(event.key)
            if key:
                self._keyboard_ctrl.press(key)
                self._keyboard_ctrl.release(key)

    def _execute_key_release(self, event: MacroEvent):
        if event.key:
            key = self._string_to_key(event.key)
            if key:
                self._keyboard_ctrl.release(key)

    def _execute_mouse_click(self, event: MacroEvent):
        if event.mouse_position:
            self._mouse_ctrl.position = event.mouse_position

        button = self._mouse_button_to_pynput(event.mouse_button)
        if event.pressed:
            self._mouse_ctrl.press(button)
        else:
            self._mouse_ctrl.release(button)

    def _execute_mouse_move(self, event: MacroEvent):
        if event.mouse_position:
            self._mouse_ctrl.position = event.mouse_position

    def _execute_mouse_scroll(self, event: MacroEvent):
        if event.mouse_position:
            self._mouse_ctrl.position = event.mouse_position
        self._mouse_ctrl.scroll(event.scroll_dx, event.scroll_dy)
