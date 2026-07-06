"""Emit iconlist.txt: <PersistenceID><TAB><IconFile> for every catalog item
that declares an icon. Run from anywhere; paths are module-relative."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", ".."))
from data.item_ids import ITEM_LIST  # noqa: E402

out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "iconlist.txt")
count = 0
with open(out_path, "w", encoding="utf-8") as f:
    for item in ITEM_LIST:
        pid = item.get("PersistenceID")
        icon = item.get("IconFile")
        if pid and icon:
            f.write("{}\t{}\n".format(pid, icon))
            count += 1
print("wrote {} entries -> {}".format(count, out_path))
