from talon import Context, Module, actions, app, clip, ctrl, ui

ctx = Context()
mod = Module()
apps = mod.apps
apps.safari = """
os: mac
and app.name: Safari
"""
ctx.matches = r"""
app: safari
"""


@ctx.action_class("user")
class user_actions:
    def tab_jump(number: int):
        if number < 9:
            actions.key("cmd-{}".format(number))

    def tab_final():
        actions.key("cmd-9")
