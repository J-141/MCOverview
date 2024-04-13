import tkinter as tk
from tkinter import ttk, filedialog
import os
from MC.MCWorld import MCWorld
from Overview.DIMGridScreen import DIMGridScreen
from Overview.DIMView import DIMView
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame.locals import *
from Overview.GlobalEvents import register_draw_callback,send_draw_event, register_forced_draw_callback
from Overview.ChunkView import view_rules
frame_size = 800
DIMS = {"Overworld":0, "Nether":-1, "End":1}
SIZES = [8,16,32,64]

class int_entry(tk.Entry):
    def __init__(self, master=None, **kwargs):
        self.var = tk.StringVar()
        tk.Entry.__init__(self, master, textvariable=self.var, **kwargs)
        self.old_value = ''
        self.var.trace_add('write', self.check)
        self.get, self.set = self.var.get, self.var.set

    def get_int(self) ->int :
        return int(self.var.get())
    
    def set_int(self,var: int):
        self.var.set(str(var))

    def check(self, *args):
        try: 
            int(self.get())
            self.old_value = self.get()
            # the current value is only digits; allow this
        except ValueError:
            # there's non-digit characters in the input; reject this 
            self.set(self.old_value)


class DIMViewOption(tk.Frame):
    def __init__(self,master):
        super().__init__(master)
        self.DIMView = None

        ttk.Label(self,text="Size:").grid(row =0, column =0)
        size_option = ttk.Combobox(self, state="readonly", values= [str(x) for x in SIZES])
        size_option.grid(row =0, column =1)
        size_option.bind('<<ComboboxSelected>>', lambda evt, x = size_option: self.resize(int(x.get())))
        size_option.set("16")
        self.size_opt = 16

        ttk.Label(self,text="View:").grid(row =1, column =0)
        view_rule = ttk.Combobox(self, state="readonly", values= list(view_rules.keys()))
        view_rule.grid(row =1, column =1)
        view_rule.bind('<<ComboboxSelected>>', lambda evt, x = view_rule: self.set_view_option(x.get()))
        view_rule.set("InhabitedTime")
        self.view_rule = "InhabitedTime"

        xz_panal = ttk.Frame(self)
        ttk.Label(xz_panal,text="chunk (X, Z)").pack(side=tk.LEFT)
        x_entry = int_entry(xz_panal, width=10)
        x_entry.pack(side=tk.LEFT)
        z_entry = int_entry(xz_panal, width=10)
        z_entry.pack(side=tk.LEFT)

        xz_panal.grid(row =2, sticky="wens", columnspan=2)
        self.chunk_xz_entry= (x_entry,z_entry)

        x_entry.set_int(0)
        z_entry.set_int(0)


        y_panal = ttk.Frame(self)
        ttk.Label(y_panal,text="section Y (min, max)").pack(side=tk.LEFT)
        min_y_entry = int_entry(y_panal, width=10)
        min_y_entry.pack(side=tk.LEFT)
        max_y_entry = int_entry(y_panal, width=10)
        max_y_entry.pack(side=tk.LEFT)

        y_panal.grid(row =3, sticky="wens", columnspan=2)

        min_y_entry.set_int(-4)
        max_y_entry.set_int(20)
        self.section_Y_entry= (min_y_entry,max_y_entry)


        border_var = tk.BooleanVar()
        border_var.trace_add("write", lambda x,y,z, v = border_var: self.set_border(v.get()))
        border_option = ttk.Checkbutton(self, text="Border",variable=border_var)
        border_option.grid(row =4, column =0)
        self.border_opt = False

        move_button = ttk.Button(self,text="apply", command = lambda : self.apply_config())
        move_button.grid(row =4, column =1)
        
        ttk.Label(self,text="Use WASD to move").grid(row =5, column = 0, columnspan=2)

        master.bind("d",lambda x: self.move((1,0)))
        master.bind("a",lambda x: self.move((-1,0)))
        master.bind("w",lambda x: self.move((0,-1)))
        master.bind("s",lambda x: self.move((0,1)))

    
      


    def move(self, direction: tuple[int,int]):
        if self.DIMView:
            x,z = self.chunk_xz_entry
            xv,zv = x.get_int()+direction[0]*(self.size_opt//8),z.get_int()+direction[1]*(self.size_opt//8)
            x.set_int(xv)
            z.set_int(zv)
            self.apply_config()

    def resize(self, size: int):
        self.size_opt = size
        self.apply_config() 

    def set_view_option(self, option: str):
        self.view_rule = option
        self.apply_config() 

    def set_border(self, border: bool):
        self.border_opt = border
        self.apply_config()   


    def apply_config(self):
        chunkX, chunkZ = (v.get_int() for v in self.chunk_xz_entry)
        minY,maxY = (v.get_int() for v in self.section_Y_entry)
        if self.DIMView:
            self.DIMView.set_size(self.size_opt)
            self.DIMView.set_border(self.border_opt)
            self.DIMView.set_chunk_view_option((self.view_rule, minY, maxY))
            self.DIMView.set_origin(chunkX, chunkZ)
            send_draw_event() 

    def attach_to(self, dimview: DIMView):
        self.DIMView = dimview
        self.apply_config()
    
    
class Overview(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("MCOverview")
        self.data = None
        self.dim_frame = tk.Frame(self, width=frame_size, height=frame_size)
        self.dim_frame.pack(side="left",fill=tk.NONE, expand=False)
        self.dim_display = DIMGridScreen(self.dim_frame,frame_size)
        self.dims:dict[int, DIMView] = {}
        register_draw_callback(self.dim_display.update)
        register_forced_draw_callback(lambda: self.dim_display.update(True))
        ttk.Label(self,text="DIM").pack(side = "top")
        dim_option = ttk.Combobox(self, state="readonly", values= list(DIMS.keys()))
        dim_option.pack(side = "top")
        dim_option.bind('<<ComboboxSelected>>', lambda evt, x = dim_option: self.load_DIM(DIMS[x.get()]))

        self.DIMOptions = DIMViewOption(self)
        self.DIMOptions.pack(side = "top", pady= 20)

        menu_bar = tk.Menu(self)
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Open...",command=self.on_open_directory)
        menu_bar.add_cascade(label="File", menu=file_menu)
        self.config(menu=menu_bar)

    def on_open_directory(self):
        directory = filedialog.askdirectory(initialdir=os.path.join(os.path.expanduser('~'), "AppData\Roaming\.minecraft\saves"))
        if directory:
            self.load_world(directory)
        
    def load_world(self,path):
        self.data = MCWorld(path)
        
    def load_DIM(self, dim:int):
        if self.data:
            if dim not in self.dims:
                self.dims[dim] = DIMView(self.data.DIMs[dim])
            self.dim_display.load_data(self.dims[dim])
            self.dim_display.update()
            self.DIMOptions.attach_to(self.dims[dim])




