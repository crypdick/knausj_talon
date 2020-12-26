import os

from talon import Module, actions, app, clip, cron, ctrl, imgui, noise, ui
from talon_plugins import eye_mouse, eye_zoom_mouse
from talon_plugins.eye_mouse import config, toggle_camera_overlay, toggle_control

key = actions.key
self = actions.self
scroll_amount = 0
click_job = None
scroll_job = None
gaze_job = None
cancel_scroll_on_pop = True

# TODO wtf
default_cursor = {
    "AppStarting": r"%SystemRoot%\Cursors\aero_working.ani",
    "Arrow": r"%SystemRoot%\Cursors\aero_arrow.cur",
    "Hand": r"%SystemRoot%\Cursors\aero_link.cur",
    "Help": r"%SystemRoot%\Cursors\aero_helpsel.cur",
    "No": r"%SystemRoot%\Cursors\aero_unavail.cur",
    "NWPen": r"%SystemRoot%\Cursors\aero_pen.cur",
    "Person": r"%SystemRoot%\Cursors\aero_person.cur",
    "Pin": r"%SystemRoot%\Cursors\aero_pin.cur",
    "SizeAll": r"%SystemRoot%\Cursors\aero_move.cur",
    "SizeNESW": r"%SystemRoot%\Cursors\aero_nesw.cur",
    "SizeNS": r"%SystemRoot%\Cursors\aero_ns.cur",
    "SizeNWSE": r"%SystemRoot%\Cursors\aero_nwse.cur",
    "SizeWE": r"%SystemRoot%\Cursors\aero_ew.cur",
    "UpArrow": r"%SystemRoot%\Cursors\aero_up.cur",
    "Wait": r"%SystemRoot%\Cursors\aero_busy.ani",
    "Crosshair": "",
    "IBeam": "",
}

# todo figure out why notepad++ still shows the cursor sometimes.
hidden_cursor = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), r"Resources\HiddenCursor.cur"
)

mod = Module()
mod.list(
    "mouse_button", desc="List of mouse button words to mouse_click index parameter"
)
setting_mouse_enable_noise_control = mod.setting(
    "mouse_enable_noise_control",
    type=int,
    default=1,
    desc="Enable mouse noise control when control mouse is enabled.",
)
setting_mouse_enable_pop_stops_scroll = mod.setting(
    "mouse_enable_pop_stops_scroll",
    type=int,
    default=0,
    desc="When enabled, pop stops continuous scroll modes (wheel upper/downer/gaze)",
)
setting_mouse_wake_hides_cursor = mod.setting(
    "mouse_wake_hides_cursor",
    type=int,
    default=0,
    desc="When enabled, mouse wake will hide the cursor. mouse_wake enables  zoom "
    "mouse.",
)
setting_mouse_hide_mouse_gui = mod.setting(
    "mouse_hide_mouse_gui",
    type=int,
    default=0,
    desc="When enabled, the 'Scroll Mouse' GUI will not be shown.",
)
setting_mouse_continuous_scroll_amount = mod.setting(
    "mouse_continuous_scroll_amount",
    type=int,
    default=80,
    desc="The default amount used when scrolling continuously",
)
setting_mouse_wheel_down_amount = mod.setting(
    "mouse_wheel_down_amount",
    type=int,
    default=120,
    desc="The amount to scroll up/down (equivalent to mouse wheel on Windows by "
    "default)",
)

# TODO wtf
continuous_scoll_mode = ""


@imgui.open(x=700, y=0, software=False)
def gui_wheel(gui: imgui.GUI):
    gui.text("Scroll mode: {}".format(continuous_scoll_mode))
    gui.line()
    if gui.button("Wheel Stop [stop scrolling]"):
        actions.user.mouse_scroll_stop()


@mod.action_class
class Actions:
    """
    Contains definitions for mouse modes (such as sleep/wake/calibrate) and
    actions (such as scrolling up/down)

    The vocab to activate these modes are found in mouse.talon
    """

    def mouse_show_cursor():
        """
        Shows the cursor.
        """
        show_cursor_helper(True)

    def mouse_hide_cursor():
        """
        Hides the cursor.
        """
        show_cursor_helper(False)

    def mouse_wake():
        """
        Enable control mouse, zoom mouse, and disables cursor.
        """
        eye_zoom_mouse.toggle_zoom_mouse(True)
        # eye_mouse.control_mouse.enable()
        if setting_mouse_wake_hides_cursor.get() >= 1:
            show_cursor_helper(False)

    def mouse_calibrate():
        """
        Start calibration.
        """
        eye_mouse.calib_start()

    def mouse_toggle_control_mouse():
        """
        Toggles control mouse.
        """
        toggle_control(not config.control_mouse)

    def mouse_toggle_camera_overlay():
        """
        Toggles camera overlay.
        """
        toggle_camera_overlay(not config.show_camera)

    def mouse_toggle_zoom_mouse():
        """
        Toggles zoom mouse.
        """
        eye_zoom_mouse.toggle_zoom_mouse(not eye_zoom_mouse.zoom_mouse.enabled)

    def mouse_cancel_zoom_mouse():
        """
        Cancel zoom mouse if pending.
        """
        if (
            eye_zoom_mouse.zoom_mouse.enabled
            and eye_zoom_mouse.zoom_mouse.state != eye_zoom_mouse.STATE_IDLE
        ):
            eye_zoom_mouse.zoom_mouse.cancel()

    def mouse_trigger_zoom_mouse():
        """
        Trigger zoom mouse on pop if enabled.
        """
        if eye_zoom_mouse.zoom_mouse.enabled:
            eye_zoom_mouse.zoom_mouse.on_pop(eye_zoom_mouse.zoom_mouse.state)

    def mouse_drag():
        """
        (TEMPORARY) Press and hold/release button 0 depending on state for
        dragging.
        """
        if 1 not in ctrl.mouse_buttons_down():
            ctrl.mouse_click(button=0, down=True)  # start dragging
        else:  # end dragging
            ctrl.mouse_click(button=0, up=True)

    def mouse_sleep():
        """
        Disables control mouse, zoom mouse, and re-enables cursor.
        """
        eye_zoom_mouse.toggle_zoom_mouse(False)
        toggle_control(False)
        show_cursor_helper(True)
        stop_scroll()
        if 1 in ctrl.mouse_buttons_down():
            actions.user.mouse_drag()

    def mouse_scroll_down():
        """
        Scrolls down.
        """
        mouse_scroll(setting_mouse_wheel_down_amount.get())()

    def mouse_scroll_down_continuous():
        """
        Scrolls down continuously.
        """
        global continuous_scoll_mode
        continuous_scoll_mode = "scroll down continuous"
        mouse_scroll(setting_mouse_continuous_scroll_amount.get())()

        if scroll_job is None:
            start_scroll()

        if setting_mouse_hide_mouse_gui.get() == 0:
            gui_wheel.show()

    def mouse_scroll_up():
        """
        Scrolls up.
        """
        mouse_scroll(-setting_mouse_wheel_down_amount.get())()

    def mouse_scroll_up_continuous():
        """
        Scrolls up continuously.
        """
        global continuous_scoll_mode
        continuous_scoll_mode = "scroll up continuous"
        mouse_scroll(-setting_mouse_continuous_scroll_amount.get())()

        if scroll_job is None:
            start_scroll()
        if setting_mouse_hide_mouse_gui.get() == 0:
            gui_wheel.show()

    def mouse_scroll_stop():
        """
        Stops scrolling.
        """
        stop_scroll()

    def mouse_gaze_scroll():
        """
        Starts gaze scroll.
        """
        global continuous_scoll_mode
        continuous_scoll_mode = "gaze scroll"
        start_cursor_scrolling()
        if setting_mouse_hide_mouse_gui.get() == 0:
            gui_wheel.show()

    def copy_mouse_position():
        """
        Copy the current mouse position coordinates.
        """
        position = ctrl.mouse_pos()
        clip.set_text((repr(position)))

    def mouse_move_center_active_window():
        """
        move the mouse cursor to the center of the currently active window.
        """
        rect = ui.active_window().rect
        ctrl.mouse_move(rect.left + (rect.width / 2), rect.top + (rect.height / 2))


def show_cursor_helper(show):
    """
    Show/hide the cursor.
    """
    if app.platform == "windows":
        import ctypes
        import winreg

        import win32con

        try:
            Registrykey = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, r"Control Panel\Cursors", 0, winreg.KEY_WRITE
            )

            for value_name, value in default_cursor.items():
                if show:
                    winreg.SetValueEx(
                        Registrykey, value_name, 0, winreg.REG_EXPAND_SZ, value
                    )
                else:
                    winreg.SetValueEx(
                        Registrykey, value_name, 0, winreg.REG_EXPAND_SZ, hidden_cursor
                    )

            winreg.CloseKey(Registrykey)

            ctypes.windll.user32.SystemParametersInfoA(
                win32con.SPI_SETCURSORS, 0, None, 0
            )

        except WindowsError:
            print("Unable to show_cursor({})".format(str(show)))
    else:
        ctrl.cursor_visible(show)


def on_pop(active):
    """
    Defines behavior for pop noises.

    Currently, pop will left click wherever the cursor is if we are not in zoom
    mode. If we are scrolling or gaze scrolling, pop will stop scrolling.

    TODO: change pop to right click when zoom_mouse supports it
    """
    print("pop detected")
    if gaze_job or scroll_job:
        if setting_mouse_enable_pop_stops_scroll.get() >= 1:
            stop_scroll()
        elif (
            not eye_zoom_mouse.zoom_mouse.enabled
            and eye_mouse.mouse.attached_tracker is not None
            and setting_mouse_enable_noise_control.get() >= 1
        ):
            ctrl.mouse_click(button=0)  # button=1 == right click


def on_hiss(active):
    """
    Defines the behavior for hiss noises.

    Currently, presses the right button.

    TODO press and holds left mouse button while hissing once zoom mouse supports it

    Args:
        active: Whether hiss is active
    """
    ctrl.mouse_click(button=1)
    # if setting_mouse_enable_noise_control.get() >= 1:
    # ctrl.mouse_click(button=0, down=active, up=not active)


# Registers the on_pop and on_hiss functions
noise.register("pop", on_pop)
noise.register("hiss", on_hiss)


def mouse_scroll(amount):
    def scroll():
        global scroll_amount
        if (scroll_amount >= 0) == (amount >= 0):
            scroll_amount += amount
        else:
            scroll_amount = amount
        actions.mouse_scroll(y=int(amount))

    return scroll


def scroll_continuous_helper():
    global scroll_amount
    # print("scroll_continuous_helper")
    if scroll_amount and (
        eye_zoom_mouse.zoom_mouse.state == eye_zoom_mouse.STATE_IDLE
    ):  # or eye_zoom_mouse.zoom_mouse.state == eye_zoom_mouse.STATE_SLEEP):
        actions.mouse_scroll(by_lines=False, y=int(scroll_amount / 10))


def start_scroll():
    global scroll_job
    scroll_job = cron.interval("60ms", scroll_continuous_helper)
    # if eye_zoom_mouse.zoom_mouse.enabled  and eye_mouse.mouse.attached_tracker is
    # not None:
    #    eye_zoom_mouse.zoom_mouse.sleep(True)


def gaze_scroll():
    """
    TODO wtf.
    """
    if (
        eye_zoom_mouse.zoom_mouse.state == eye_zoom_mouse.STATE_IDLE
    ):  # or eye_zoom_mouse.zoom_mouse.state == eye_zoom_mouse.STATE_SLEEP:
        x, y = ctrl.mouse_pos()

        # the rect for the window containing the mouse
        rect = None

        # on windows, check the active_window first since ui.windows() is not z-ordered
        if app.platform == "windows" and ui.active_window().rect.contains(x, y):
            rect = ui.active_window().rect
        else:
            windows = ui.windows()
            for w in windows:
                if w.rect.contains(x, y):
                    rect = w.rect
                    break

        if rect is None:
            # print("no window found!")
            return

        midpoint = rect.y + rect.height / 2
        amount = int(((y - midpoint) / (rect.height / 10)) ** 3)
        actions.mouse_scroll(by_lines=False, y=amount)


def stop_scroll():
    """
    TODO wtf.
    """
    global scroll_amount, scroll_job, gaze_job
    scroll_amount = 0
    if scroll_job:
        cron.cancel(scroll_job)

    if gaze_job:
        cron.cancel(gaze_job)

    scroll_job = None
    gaze_job = None
    gui_wheel.hide()

    # if eye_zoom_mouse.zoom_mouse.enabled and eye_mouse.mouse.attached_tracker is
    # not  None:
    #    eye_zoom_mouse.zoom_mouse.sleep(False)


def start_cursor_scrolling():
    """
    TODO wtf.
    """
    global scroll_job, gaze_job
    stop_scroll()
    gaze_job = cron.interval("60ms", gaze_scroll)
    # if eye_zoom_mouse.zoom_mouse.enabled and eye_mouse.mouse.attached_tracker is
    # not None:
    #    eye_zoom_mouse.zoom_mouse.sleep(True)
