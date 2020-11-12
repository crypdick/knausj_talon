from talon import Context, Module, actions, app

ctx = Context()
mod = Module()
apps = mod.apps
apps.firefox = "app.name: Firefox"
apps.firefox = "app.name: firefox"
apps.firefox = "app.name: firefox.exe"

ctx.matches = r"""
app: firefox
"""


@ctx.action_class("user")
class user_actions:
    """
    Defines actions for Firefox.

    See default keybindings here:
    https://support.mozilla.org/en-US/kb/keyboard-shortcuts-perform-firefox-tasks-quickly
    """

    def tab_jump(number: int):
        if number < 9:
            if app.platform == "mac":
                actions.key("cmd-{}".format(number))
            else:
                actions.key("alt-{}".format(number))

    def tab_final():
        if app.platform == "mac":
            actions.key("cmd-9")
        else:
            actions.key("alt-9")
