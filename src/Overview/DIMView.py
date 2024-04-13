
import pygame
from Overview.ChunkView import ChunkView
from MC.MCWorld import MCDIM


class DIMView():
    def __init__(self, data):
        self.data: MCDIM = data
        self.chunk_views: dict[tuple[int,int],ChunkView] = {}
        self.origin=(0,0)
        self.size = 16
        self.view_option = ("InhabitedTime", None)
        self.border = False
        self.viewable_section = (-100, 100)

    def set_size(self,size):
        self.size = size

    def set_border(self,border):
        self.border = border
    
    def set_viewable_section(self, min_section_Y, max_section_Y):
        self.viewable_section = (min_section_Y, max_section_Y)

    def get_chunk_view(self,x,z, force_reload = False):
        if (x,z) not in self.chunk_views:
            self.chunk_views[(x,z)] = ChunkView()
        if force_reload or (not self.chunk_views[(x,z)].chunk):
            self.chunk_views[(x,z)].load_data(self.data.get_chunk_no_block(x,z))
        return self.chunk_views[(x,z)]
    
    def set_chunk_view_option(self,view_option):
        self.view_option = view_option

    def set_origin(self,x,z):
        self.origin = (x,z)

    def draw(self, size, force_reload = False):
        canvas = pygame.Surface((self.size * 16, self.size * 16))
        x,z = self.origin
        imgs=[]
        for i in range(self.size):
            for j in range(self.size):
                chunk = self.get_chunk_view(i+(x-self.size//2), j+(z-self.size//2),force_reload)
                imgs.append((chunk.get_view(self.view_option, self.border), (i*16, j*16)))
        canvas.blits(imgs)
        canvas = pygame.transform.scale(canvas, (size-25,size-25))

        res = pygame.Surface((size,size))
        res.fill((200,200,200))
        res.blit(canvas, (25,25))

        font = pygame.font.SysFont(None, 24)

        min_x, min_z = x-self.size//2, z-self.size//2
        max_x, max_z = min_x + self.size, min_z + self.size

        for i, val in enumerate([str(max_x), "x="+str(x), str(min_x)]):
            text_surf = font.render(val, True, (0,0,0))
            res.blit(text_surf, (size - 25 - i * (size - 50) / 2 - text_surf.get_height() / 2, 0))

        for i, val in enumerate([str(max_z), "z="+str(z), str(min_z)]):
            text_surf = font.render(val, True, (0,0,0))
            res.blit(text_surf, (0, size - 25 - i * (size - 50) / 2 - text_surf.get_height() / 2))
           
        return res
        
    
    
