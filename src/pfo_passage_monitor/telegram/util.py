
from copy import deepcopy


def update_inline_keybord(ilkb, handler, *args, **kwargs):

    ilkb = deepcopy(ilkb)
    
    for i, row in enumerate(ilkb):
        for j, _ in enumerate(row):
            ilkb[i][j] = handler(ilkb[i][j], *args, **kwargs)
    
    return ilkb