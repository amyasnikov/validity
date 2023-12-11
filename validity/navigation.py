from extras.plugins import PluginMenu, PluginMenuButton, PluginMenuItem
from utilities.choices import ButtonColorChoices


validity_menu_items = (
    PluginMenuItem(
        link="plugins:validity:complianceselector_list",
        link_text="Selectors",
        buttons=[
            PluginMenuButton(
                link="plugins:validity:complianceselector_add",
                title="Add",
                icon_class="mdi mdi-plus-thick",
                color=ButtonColorChoices.GREEN,
            ),
        ],
    ),
    PluginMenuItem(
        link="plugins:validity:compliancetest_list",
        link_text="Tests",
        buttons=[
            PluginMenuButton(
                link="plugins:validity:compliancetest_add",
                title="Add",
                icon_class="mdi mdi-plus-thick",
                color=ButtonColorChoices.GREEN,
            ),
        ],
    ),
    PluginMenuItem(
        link="plugins:validity:compliancetestresult_list",
        link_text="Test Results",
    ),
    PluginMenuItem(
        link="plugins:validity:compliancereport_list",
        link_text="Reports",
    ),
    PluginMenuItem(
        link="plugins:validity:configserializer_list",
        link_text="Config Serializers",
        buttons=[
            PluginMenuButton(
                link="plugins:validity:configserializer_add",
                title="Add",
                icon_class="mdi mdi-plus-thick",
                color=ButtonColorChoices.GREEN,
            ),
        ],
    ),
    PluginMenuItem(
        link="plugins:validity:nameset_list",
        link_text="Name Sets",
        buttons=[
            PluginMenuButton(
                link="plugins:validity:nameset_add",
                title="Add",
                icon_class="mdi mdi-plus-thick",
                color=ButtonColorChoices.GREEN,
            ),
        ],
    ),
)

polling_menu_items = (
    PluginMenuItem(
        link="plugins:validity:poller_list",
        link_text="Pollers",
        buttons=[
            PluginMenuButton(
                link="plugins:validity:poller_add",
                title="Add",
                icon_class="mdi mdi-plus-thick",
                color=ButtonColorChoices.GREEN,
            ),
        ],
    ),
    PluginMenuItem(
        link="plugins:validity:command_list",
        link_text="Commands",
        buttons=[
            PluginMenuButton(
                link="plugins:validity:command_add",
                title="Add",
                icon_class="mdi mdi-plus-thick",
                color=ButtonColorChoices.GREEN,
            ),
        ],
    ),
)

menu = PluginMenu(
    label="Validity",
    groups=(("main", validity_menu_items), ("polling", polling_menu_items)),
    icon_class="mdi mdi-checkbox-marked-circle-outline",
)
