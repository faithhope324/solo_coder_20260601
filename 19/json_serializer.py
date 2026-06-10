import json
import os
from datetime import datetime
from typing import Optional

from event_store import Macro, MacroEvent, EventType, MouseButton


class JsonSerializer:
    @staticmethod
    def macro_to_dict(macro: Macro) -> dict:
        return {
            "name": macro.name,
            "record_mouse": macro.record_mouse,
            "created_at": macro.created_at,
            "modified_at": macro.modified_at or datetime.now().isoformat(),
            "events": [JsonSerializer._event_to_dict(event) for event in macro.events],
        }

    @staticmethod
    def _event_to_dict(event: MacroEvent) -> dict:
        data = {
            "event_type": event.event_type.value,
            "delay_ms": event.delay_ms,
            "pressed": event.pressed,
        }
        if event.key is not None:
            data["key"] = event.key
        if event.is_combination:
            data["is_combination"] = True
            data["combination_keys"] = event.combination_keys
        if event.mouse_button is not None:
            data["mouse_button"] = event.mouse_button.value
        if event.mouse_position is not None:
            data["mouse_position"] = list(event.mouse_position)
        if event.event_type == EventType.MOUSE_SCROLL:
            data["scroll_dx"] = event.scroll_dx
            data["scroll_dy"] = event.scroll_dy
        return data

    @staticmethod
    def dict_to_macro(data: dict) -> Macro:
        macro = Macro(
            name=data.get("name", "未命名宏"),
            record_mouse=data.get("record_mouse", False),
            created_at=data.get("created_at"),
            modified_at=data.get("modified_at"),
        )
        for event_data in data.get("events", []):
            event = JsonSerializer._dict_to_event(event_data)
            if event:
                macro.events.append(event)
        return macro

    @staticmethod
    def _dict_to_event(data: dict) -> Optional[MacroEvent]:
        try:
            event_type = EventType(data.get("event_type", "key_press"))
            event = MacroEvent(
                event_type=event_type,
                delay_ms=data.get("delay_ms", 0),
                pressed=data.get("pressed", True),
            )
            if "key" in data:
                event.key = data["key"]
            if data.get("is_combination", False):
                event.is_combination = True
                event.combination_keys = data.get("combination_keys", [])
            if "mouse_button" in data:
                event.mouse_button = MouseButton(data["mouse_button"])
            if "mouse_position" in data:
                pos = data["mouse_position"]
                event.mouse_position = (pos[0], pos[1]) if pos else None
            if event_type == EventType.MOUSE_SCROLL:
                event.scroll_dx = data.get("scroll_dx", 0)
                event.scroll_dy = data.get("scroll_dy", 0)
            return event
        except (ValueError, KeyError, IndexError):
            return None

    @staticmethod
    def save_macro(macro: Macro, filepath: str) -> bool:
        try:
            macro.modified_at = datetime.now().isoformat()
            if not macro.created_at:
                macro.created_at = macro.modified_at
            data = JsonSerializer.macro_to_dict(macro)
            os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存宏失败: {e}")
            return False

    @staticmethod
    def load_macro(filepath: str) -> Optional[Macro]:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            return JsonSerializer.dict_to_macro(data)
        except Exception as e:
            print(f"加载宏失败: {e}")
            return None

    @staticmethod
    def get_macros_directory() -> str:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        macros_dir = os.path.join(base_dir, "macros")
        os.makedirs(macros_dir, exist_ok=True)
        return macros_dir

    @staticmethod
    def list_saved_macros() -> list:
        macros_dir = JsonSerializer.get_macros_directory()
        macros = []
        try:
            for filename in os.listdir(macros_dir):
                if filename.endswith(".json"):
                    filepath = os.path.join(macros_dir, filename)
                    macro = JsonSerializer.load_macro(filepath)
                    if macro:
                        macros.append((filename, macro))
        except Exception as e:
            print(f"列出宏失败: {e}")
        return macros
