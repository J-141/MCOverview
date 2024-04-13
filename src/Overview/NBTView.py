import tkinter as tk
from tkinter import ttk, simpledialog
from MC.NBTReader import NBT



class NBTTreeView(tk.Frame):
    def __init__(self, parent, nbt: NBT, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.tree = ttk.Treeview(self,columns=("tag"))
        self.lookup = {} # from node to nbt
        self.load_tree(nbt)
        self.tree.pack(side='top', expand=True, fill='both')
        self.edit_button = ttk.Button(self, text="Edit", command=self.edit_item)
        self.edit_button.pack(side='left', fill='x')
        self.add_button = ttk.Button(self, text="Add Key", command=self.add_key)
        self.add_button.pack(side='left', fill='x')

    def load_tree(self, nbt, parent='', max_list_length = 2048):
        self.nbt = nbt
        if isinstance(nbt.data, dict):
            for key, value in nbt.data.items():
                node = self.tree.insert(parent, 'end', text=key, values=(value.tag))
                self.lookup[node] = nbt
                self.load_tree(value, node)
        elif isinstance(nbt.data, list):
            if len(nbt.data)> max_list_length:
                node = self.tree.insert(parent, 'end', text=f'<{len(nbt.data)}> Items', values=(nbt.tag))
            else:
                for i, item in enumerate(nbt.data):
                    node = self.tree.insert(parent, 'end', text=f'Item {i}', values=(nbt.tag))
                    self.lookup[node] = nbt
                    if isinstance(item, NBT):   # this is a list
                        self.load_tree(item, node)
                    else:                       # this is an array
                        self.tree.item(node, text = f"[{i}]: {item}")

        else:
            self.tree.insert(parent, 'end', text=str(nbt.data), values=(nbt.tag))

#TODO
    def edit_item(self):
        selected_item = self.tree.selection()
        if selected_item:
            current_value = self.tree.item(selected_item[0], 'text')
            new_value = simpledialog.askstring("Edit Item", "Enter new value:", initialvalue=current_value)
            if new_value is not None:
                self.tree.item(selected_item[0], text=new_value)
                pass #TODO
#TODO
    def add_key(self):
        selected_item = self.tree.selection()
        if selected_item:
            key = simpledialog.askstring("Add Key", "Enter key name:")
            if key is not None:
                self.tree.insert(selected_item[0], 'end', text=key, values=("[Value]",))
                pass #TODO

        