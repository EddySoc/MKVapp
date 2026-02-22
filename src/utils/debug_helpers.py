#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      EddyS
#
# Created:     01/07/2025
# Copyright:   (c) EddyS 2025
# Licence:     <your licence>
#-------------------------------------------------------------------------------
__all__ = ["test_scandir_lists"]

def test_scandir_lists():
    s = get_shared()
    # 📋 Print each one with a header for readability
    print("📂 subfol_lst:", s.subfol_lst)
    print("🌳 dirtree_lst:", s.dirtree_lst)
    print("📄 files_lst:", s.files_lst)
    print("🎬 vids_lst:", s.vids_lst)
    print("📝 subs_lst:", s.subs_lst)
    print("🔁 upd_lst:", s.upd_lst)
