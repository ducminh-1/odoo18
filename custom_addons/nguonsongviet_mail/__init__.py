from . import models


def _pre_init_nguonsongviet_mail(env):
    env["mail.activity.type"].with_context(active_test=False).search([]).write(
        {"keep_done": True}
    )
