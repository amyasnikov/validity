from extras.plugins import PluginMenu, PluginMenuButton, PluginMenuItem
from utilities.choices import ButtonColorChoices


def model_add_button(entity):
    return PluginMenuButton(
        link=f"plugins:validity:{entity}_add",
        title="Add",
        icon_class="mdi mdi-plus-thick",
        color=ButtonColorChoices.GREEN,
        permissions=[f"validity.add_{entity}"],
    )


def model_menu_item(entity, title, buttons=()):
    buttons = [btn(entity) if callable(btn) else btn for btn in buttons]
    return PluginMenuItem(
        link=f"plugins:validity:{entity}_list",
        link_text=title,
        buttons=buttons or [],
        permissions=[f"validity.view_{entity}"],
    )


run_tests_button = PluginMenuButton(
    link="plugins:validity:compliancetest_run",
    title="Run",
    icon_class="mdi mdi-rocket-launch",
    color=ButtonColorChoices.CYAN,
)

validity_menu_items = (
    model_menu_item("complianceselector", "Selectors", [model_add_button]),
    model_menu_item("compliancetest", "Tests", [run_tests_button, model_add_button]),
    model_menu_item("compliancetestresult", "Test Results"),
    model_menu_item("compliancereport", "Reports"),
    model_menu_item("serializer", "Serializers", [model_add_button]),
    model_menu_item("nameset", "Name Sets", [model_add_button]),
)

polling_menu_items = (
    model_menu_item("command", "Commands", [model_add_button]),
    model_menu_item("poller", "Pollers", [model_add_button]),
)

menu = PluginMenu(
    label="Validity",
    groups=(("main", validity_menu_items), ("polling", polling_menu_items)),
    icon_class="mdi mdi-checkbox-marked-circle-outline",
)
