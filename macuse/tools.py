"""Tool profiles. Default exposes the desktop only; shell and filesystem are opt-in."""

DESKTOP = {
    "computer_screenshot", "computer_get_screen_size", "computer_get_cursor_position",
    "computer_get_desktop_state",
    "computer_click", "computer_double_click", "computer_move", "computer_drag", "computer_scroll",
    "computer_mouse_down", "computer_mouse_up",
    "computer_type", "computer_press_key", "computer_hotkey", "computer_key_down", "computer_key_up",
    "computer_clipboard_get", "computer_clipboard_set",
    "computer_open", "computer_launch_app",
    "computer_get_active_window", "computer_get_window_name", "computer_get_window_size",
    "computer_get_window_position", "computer_set_window_size", "computer_set_window_position",
    "computer_activate_window", "computer_minimize_window", "computer_maximize_window",
    "computer_close_window", "computer_get_app_windows", "computer_get_desktop_environment",
    "computer_get_accessibility_tree", "computer_find_element",
}

SHELL = {"computer_run_command"}

FILES = {
    "computer_file_read", "computer_file_write", "computer_file_exists", "computer_directory_exists",
    "computer_list_directory", "computer_create_directory", "computer_delete_file",
    "computer_delete_directory", "computer_get_file_size",
}


def allowed(shell: bool = False, files: bool = False) -> set[str]:
    names = set(DESKTOP)
    if shell:
        names |= SHELL
    if files:
        names |= FILES
    return names
