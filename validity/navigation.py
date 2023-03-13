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
        link="plugins:validity:gitrepo_list",
        link_text="Git Repositories",
        buttons=[
            PluginMenuButton(
                link="plugins:validity:gitrepo_add",
                title="Add",
                icon_class="mdi mdi-plus-thick",
                color=ButtonColorChoices.GREEN,
            ),
        ],
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

menu = PluginMenu(
    label="Validity",
    groups=(("Validity", validity_menu_items),),
    icon_class="mdi mdi-checkbox-marked-circle-outline",
)
