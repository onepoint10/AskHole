"""
Keyboard Shortcuts Module
Optimized cross-platform keyboard layout-independent shortcuts for Tkinter Text widgets
"""

import tkinter as tk
import sys
from typing import Dict, Set, Callable, Optional, Tuple


class KeyboardShortcuts:
    """Cross-platform keyboard layout-independent shortcuts for Tkinter Text widgets"""

    def __init__(self, text_widget: tk.Text):
        self.text_widget = text_widget
        self.root = text_widget.winfo_toplevel()

        # Platform detection
        self.is_macos = sys.platform == "darwin"

        # Event handling state
        self.event_handled = False

        # Keycode mappings for layout independence
        self.keycode_mappings: Dict[str, Set[int]] = {}
        self.layout_mappings: Dict[str, str] = {}

        # Action mappings
        self.actions: Dict[str, Callable[[], bool]] = {
            'c': self.copy,
            'v': self.paste,
            'x': self.cut,
            'a': self.select_all,
            'z': self.undo,
            'y': self.redo,
            'send': lambda: self.send_callback() if self.send_callback else False
        }

        self._setup_shortcuts()
        self._setup_layout_mappings()

    def set_send_callback(self, callback: Callable[[], None]):
        """Set callback function for send action"""
        self.send_callback = callback
        # Also update the action mapping
        self.actions['send'] = lambda: callback() or True

    def _setup_shortcuts(self) -> None:
        """Setup the shortcut system with proper event handling hierarchy"""
        # Primary event handler
        self.text_widget.bind("<KeyPress>", self._handle_keypress, "+")

        # Disable default shortcuts to prevent conflicts
        self._disable_default_shortcuts()

        # Special key combinations - use proper modifier for platform
        modifier = "Command" if self.is_macos else "Control"
        self.text_widget.bind(f"<{modifier}-Return>", lambda e: self._handle_special("send"))
        self.text_widget.bind("<Shift-Return>", lambda e: self._handle_special("newline"))

        # Virtual events as fallback
        self._setup_virtual_events()

    def _disable_default_shortcuts(self) -> None:
        """Setup fallback bindings instead of disabling defaults"""
        modifier = "Command" if self.is_macos else "Control"
        fallback_shortcuts = ['c', 'v', 'x', 'a', 'z', 'y']

        for key in fallback_shortcuts:
            binding = f"<{modifier}-{key}>"
            try:
                self.text_widget.bind(binding,
                                    lambda e, k=key: self._fallback_handler(k), "+")
            except tk.TclError:
                pass

    def _setup_layout_mappings(self) -> None:
        """Setup mappings for different keyboard layouts"""
        if self.is_macos:
            self.layout_mappings.update({
                'cyrillic_es': 'c',  # с -> c
                'cyrillic_em': 'v',  # м -> v
                'cyrillic_che': 'x', # ч -> x
                'cyrillic_ef': 'a',  # ф -> a
                'cyrillic_ya': 'z',  # я -> z
                'cyrillic_en': 'y',  # н -> y
            })
            self.expected_keycodes = {
                'c': [8, 9], 'v': [9, 47], 'x': [7, 6],
                'a': [0, 1], 'z': [6, 7], 'y': [16, 17]
            }
        else:
            self.layout_mappings.update({
                'Cyrillic_es': 'c', 'Cyrillic_em': 'v', 'Cyrillic_che': 'x',
                'Cyrillic_ef': 'a', 'Cyrillic_ya': 'z', 'Cyrillic_en': 'y',
            })
            self.expected_keycodes = {
                'c': [67], 'v': [86], 'x': [88],
                'a': [65], 'z': [90], 'y': [89]
            }

    def _setup_virtual_events(self) -> None:
        """Setup virtual events as fallback"""
        virtual_events = [
            ("<<Copy>>", self.copy), ("<<Paste>>", self.paste), ("<<Cut>>", self.cut),
            ("<<SelectAll>>", self.select_all), ("<<Undo>>", self.undo), ("<<Redo>>", self.redo)
        ]

        for event, action in virtual_events:
            self.text_widget.bind(event, lambda e, a=action: a() and "break")

    def _handle_keypress(self, event) -> Optional[str]:
        """Main keypress handler with duplicate prevention - requires modifier keys"""
        if self.text_widget.focus_get() != self.text_widget:
            return None

        # CRITICAL FIX: Validate modifier is actually pressed using direct state check
        if not self._validate_modifier_pressed(event):
            return None

        if event.keysym.lower() in ['meta_l', 'meta_r', 'control_l', 'control_r', 'alt_l', 'alt_r']:
            return None

        action_key = self._resolve_action_key(event.keysym.lower(), event.keycode)
        if action_key and action_key in self.actions:
            self.event_handled = True

            try:
                success = self.actions[action_key]()
                return "break" if success else None
            finally:
                self.root.after(50, self._reset_event_handled)

        return None

    def _get_modifiers(self, event) -> Tuple[bool, bool]:
        """Get primary and secondary modifier states"""
        if self.is_macos:
            primary = bool(event.state & 0x8)    # Command
            secondary = bool(event.state & 0x4)  # Control
        else:
            primary = bool(event.state & 0x4)    # Control
            secondary = bool(event.state & 0x8)  # Alt

        return primary, secondary

    def _resolve_action_key(self, keysym: str, keycode: int) -> Optional[str]:
        """Resolve keysym/keycode to action key"""
        # Direct English keysym
        if keysym in self.actions:
            self._learn_keycode(keysym, keycode)
            return keysym

        # Layout mapping
        if keysym in self.layout_mappings:
            mapped_key = self.layout_mappings[keysym]
            self._learn_keycode(mapped_key, keycode)
            return mapped_key

        # Learned keycode
        for action_key, keycodes in self.keycode_mappings.items():
            if keycode in keycodes:
                return action_key

        # Expected keycode ranges
        for action_key, expected_codes in self.expected_keycodes.items():
            if keycode in expected_codes:
                self._learn_keycode(action_key, keycode)
                return action_key

        return None

    def _learn_keycode(self, action_key: str, keycode: int) -> None:
        """Learn keycode for future reference"""
        if action_key not in self.keycode_mappings:
            self.keycode_mappings[action_key] = set()
        self.keycode_mappings[action_key].add(keycode)

    def _fallback_handler(self, action_key: str) -> Optional[str]:
        """Fallback handler for when primary handler doesn't catch the event - requires modifiers"""
        if self.event_handled:
            return "break"

        # For fallback, we assume the modifier was pressed since we got here via Control+key or Cmd+key binding
        if action_key in self.actions:
            success = self.actions[action_key]()
            return "break" if success else None

        return None

    def _validate_modifier_pressed(self, event) -> bool:
        """Validate that the correct modifier key is actually pressed"""
        if self.is_macos:
            # On macOS, we need Command key (Meta/Cmd)
            return bool(event.state & 0x8)  # Command key
        else:
            # On Windows/Linux, we need Control key
            return bool(event.state & 0x4)  # Control key

    def _reset_event_handled(self) -> None:
        """Reset event handling flag"""
        self.event_handled = False

    def _handle_special(self, action: str) -> str:
        """Handle special key combinations"""
        if action == "send":
            if hasattr(self, 'send_callback') and self.send_callback:
                self.send_callback()
        elif action == "newline":
            self.text_widget.insert(tk.INSERT, '\n')
        return "break"

    # Action methods
    def copy(self) -> bool:
        """Copy selected text to clipboard"""
        try:
            if self.text_widget.tag_ranges(tk.SEL):
                selected_text = self.text_widget.get(tk.SEL_FIRST, tk.SEL_LAST)
                self.text_widget.clipboard_clear()
                self.text_widget.clipboard_append(selected_text)
                return True
            return False
        except Exception:
            return False

    def paste(self) -> bool:
        """Paste clipboard content"""
        try:
            clipboard_content = self.text_widget.clipboard_get()
            if clipboard_content:
                if self.text_widget.tag_ranges(tk.SEL):
                    self.text_widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
                self.text_widget.insert(tk.INSERT, clipboard_content)
                return True
            return False
        except (tk.TclError, Exception):
            return False

    def cut(self) -> bool:
        """Cut selected text to clipboard"""
        try:
            if self.text_widget.tag_ranges(tk.SEL):
                selected_text = self.text_widget.get(tk.SEL_FIRST, tk.SEL_LAST)
                self.text_widget.clipboard_clear()
                self.text_widget.clipboard_append(selected_text)
                self.text_widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
                return True
            return False
        except Exception:
            return False

    def select_all(self) -> bool:
        """Select all text"""
        try:
            self.text_widget.tag_remove(tk.SEL, "1.0", tk.END)
            self.text_widget.tag_add(tk.SEL, "1.0", "end-1c")
            self.text_widget.mark_set(tk.INSERT, "1.0")
            self.text_widget.see(tk.INSERT)
            return True
        except Exception:
            return False

    def undo(self) -> bool:
        """Undo last action"""
        try:
            self.text_widget.edit_undo()
            return True
        except tk.TclError:
            return False

    def redo(self) -> bool:
        """Redo last undone action"""
        try:
            self.text_widget.edit_redo()
            return True
        except tk.TclError:
            return False

    def add_custom_action(self, key: str, action: Callable[[], bool]) -> None:
        """Add custom action for a key"""
        self.actions[key] = action

    def remove_action(self, key: str) -> None:
        """Remove action for a key"""
        if key in self.actions:
            del self.actions[key]