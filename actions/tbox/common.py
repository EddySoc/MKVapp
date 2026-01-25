#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      EddyS
#
# Created:     04/08/2025
# Copyright:   (c) EddyS 2025
# Licence:     <your licence>
#-------------------------------------------------------------------------------
# project_root/actions/common/common.py
from decorators.decorators import menu_tag

@menu_tag(label="Clear Textbox",icon="🧹",group=["tbox"])
def clear_this_textbox():
    from shared_data import get_shared
    s = get_shared()
    widget = getattr(s, "last_right_clicked_widget", None)
    if widget is None:
        print("⚠️ No widget was right-clicked.")
        return

    tb_name = getattr(widget, "custom_name", widget.winfo_name())
    from widgets.base_textbox import BaseTBox
    BaseTBox.clear_text(tb_name)
    print(f"✅ Cleared textbox: {tb_name}")