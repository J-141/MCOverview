
update_callbacks = []
force_update_callbacks = []

def log(msg: str):
    print(msg)

def send_draw_event():
    for i in update_callbacks:
        i()
        
def send_force_draw_event():
    for i in force_update_callbacks:
        i()

def register_draw_callback(draw_callback):
    update_callbacks.append(draw_callback) 
    
def register_forced_draw_callback(draw_callback):
    force_update_callbacks.append(draw_callback) 
