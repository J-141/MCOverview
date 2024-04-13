import os
import sys
import pygame
from Overview.DIMView import DIMView
import time

min_draw_interval = 0.02

class DIMGridScreen():
    def __init__(self, master, size: int = 1024):
        os.environ['SDL_WINDOWID'] = str(master.winfo_id())
        self.last_draw_time = time.time()
        if sys.platform == "win32":
            os.environ['SDL_VIDEODRIVER'] = 'windib'
        pygame.init()
        self.size = size
        self.window = pygame.display.set_mode((size,size))

    def load_data(self, data:DIMView):
        self.data = data
    
    def update(self, force_reload = False): 
        t = time.time()
        if t - self.last_draw_time < min_draw_interval:
            return
        self.last_draw_time = t
        img = self.data.draw(self.size, force_reload)
        self.window.blit(img, (0,0))
        pygame.display.flip()


    


    

