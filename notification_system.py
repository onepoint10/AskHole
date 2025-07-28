"""
Notification System Module
Provides a modern notification system for user feedback
"""

import tkinter as tk
from tkinter import ttk
import threading
from typing import Optional, Callable


class NotificationManager:
    """Manages application notifications"""
    
    def __init__(self, parent_window):
        self.parent = parent_window
        self.notifications = []
        self.notification_frame = None
        self.setup_notification_area()

    def setup_notification_area(self):
        """Setup the notification display area"""
        # Create a frame at the top of the parent window for notifications
        self.notification_frame = tk.Frame(self.parent, height=0)
        # Pack at the top without specifying 'before' parameter to avoid children access issues
        self.notification_frame.pack(side=tk.TOP, fill=tk.X)
        self.notification_frame.pack_propagate(False)
    
    def show_notification(self, message: str, notification_type: str = "info", duration: int = 5000, action_text: str = None, action_callback: Callable = None):
        """
        Show a notification
        
        Args:
            message: The notification message
            notification_type: Type of notification ('info', 'success', 'warning', 'error')
            duration: How long to show the notification in milliseconds (0 for permanent)
            action_text: Optional action button text
            action_callback: Optional action button callback
        """
        notification = Notification(
            self.notification_frame, 
            message, 
            notification_type, 
            duration,
            action_text,
            action_callback,
            self._remove_notification
        )
        
        self.notifications.append(notification)
        self._update_notification_area()
        
        return notification
    
    def _remove_notification(self, notification):
        """Remove a notification"""
        if notification in self.notifications:
            self.notifications.remove(notification)
            notification.destroy()
            self._update_notification_area()
    
    def _update_notification_area(self):
        """Update the notification area size"""
        if self.notifications:
            # Calculate total height needed
            total_height = len(self.notifications) * 50  # 50px per notification
            self.notification_frame.configure(height=total_height)
        else:
            self.notification_frame.configure(height=0)
    
    def clear_all(self):
        """Clear all notifications"""
        for notification in self.notifications[:]:
            self._remove_notification(notification)
    
    def show_error(self, message: str, duration: int = 8000):
        """Show an error notification"""
        return self.show_notification(message, "error", duration)
    
    def show_warning(self, message: str, duration: int = 6000):
        """Show a warning notification"""
        return self.show_notification(message, "warning", duration)
    
    def show_success(self, message: str, duration: int = 4000):
        """Show a success notification"""
        return self.show_notification(message, "success", duration)
    
    def show_info(self, message: str, duration: int = 5000):
        """Show an info notification"""
        return self.show_notification(message, "info", duration)


class Notification(tk.Frame):
    """Individual notification widget"""
    
    def __init__(self, parent, message: str, notification_type: str, duration: int, 
                 action_text: str = None, action_callback: Callable = None, 
                 remove_callback: Callable = None):
        super().__init__(parent)
        
        self.message = message
        self.notification_type = notification_type
        self.duration = duration
        self.action_text = action_text
        self.action_callback = action_callback
        self.remove_callback = remove_callback
        self.timer_id = None
        
        self.setup_ui()
        self.pack(fill=tk.X, padx=5, pady=2)
        
        # Start auto-dismiss timer if duration > 0
        if duration > 0:
            self.timer_id = self.after(duration, self.dismiss)
    
    def setup_ui(self):
        """Setup the notification UI"""
        # Configure colors based on type
        colors = self.get_colors()
        
        self.configure(bg=colors['bg'], relief=tk.RAISED, bd=1)
        
        # Icon
        icon_label = tk.Label(self, text=colors['icon'], font=('Segoe UI', 12), 
                             bg=colors['bg'], fg=colors['fg'])
        icon_label.pack(side=tk.LEFT, padx=(10, 5), pady=10)
        
        # Message
        message_label = tk.Label(self, text=self.message, font=('Segoe UI', 10), 
                                bg=colors['bg'], fg=colors['fg'], wraplength=400)
        message_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=10)
        
        # Action button (if provided)
        if self.action_text and self.action_callback:
            action_btn = tk.Button(self, text=self.action_text, 
                                  command=self.action_callback,
                                  bg=colors['button_bg'], fg=colors['button_fg'],
                                  font=('Segoe UI', 9), relief=tk.FLAT)
            action_btn.pack(side=tk.RIGHT, padx=5, pady=10)
        
        # Close button
        close_btn = tk.Button(self, text="×", command=self.dismiss,
                             bg=colors['bg'], fg=colors['fg'],
                             font=('Segoe UI', 12, 'bold'), relief=tk.FLAT,
                             width=2, height=1)
        close_btn.pack(side=tk.RIGHT, padx=(5, 10), pady=10)
    
    def get_colors(self):
        """Get colors based on notification type"""
        if self.notification_type == "error":
            return {
                'bg': '#ffebee',
                'fg': '#c62828',
                'icon': '⚠',
                'button_bg': '#c62828',
                'button_fg': '#ffffff'
            }
        elif self.notification_type == "warning":
            return {
                'bg': '#fff3e0',
                'fg': '#ef6c00',
                'icon': '⚠',
                'button_bg': '#ef6c00',
                'button_fg': '#ffffff'
            }
        elif self.notification_type == "success":
            return {
                'bg': '#e8f5e8',
                'fg': '#2e7d32',
                'icon': '✓',
                'button_bg': '#2e7d32',
                'button_fg': '#ffffff'
            }
        else:  # info
            return {
                'bg': '#e3f2fd',
                'fg': '#1976d2',
                'icon': 'ℹ',
                'button_bg': '#1976d2',
                'button_fg': '#ffffff'
            }
    
    def dismiss(self):
        """Dismiss the notification"""
        if self.timer_id:
            self.after_cancel(self.timer_id)
        
        if self.remove_callback:
            self.remove_callback(self)


class StatusBarNotification:
    """Simple status bar notification system"""
    
    def __init__(self, status_bar):
        self.status_bar = status_bar
        self.original_status = ""
        self.timer_id = None
    
    def show_temporary_status(self, message: str, duration: int = 3000):
        """Show a temporary status message"""
        # Cancel any existing timer
        if self.timer_id:
            self.status_bar.after_cancel(self.timer_id)
        
        # Save original status if this is the first temporary message
        if not self.timer_id:
            self.original_status = self.status_bar.status_var.get()
        
        # Set new status
        self.status_bar.set_status(message)
        
        # Set timer to restore original status
        self.timer_id = self.status_bar.after(duration, self._restore_status)
    
    def _restore_status(self):
        """Restore the original status"""
        self.status_bar.set_status(self.original_status)
        self.timer_id = None
        self.original_status = ""

