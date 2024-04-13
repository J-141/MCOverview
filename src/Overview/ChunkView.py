from MC.MCChunk import MCChunk
from MC import ResourceManager
import pygame


class ChuckViewRule:
    def IsCompleted(chunk: MCChunk, opt):
        if chunk == None: 
            color = (100,100,100)
        elif chunk.get_status() == "minecraft:full":
            color = (148,207,80)
        else:
            color = (23,69,27)
        bitmap = pygame.Surface((16, 16))
        bitmap.fill(color)
        return bitmap
    
    def InhabitedTime(chunk: MCChunk, opt):
        if chunk == None:
            color = (255,255,255)
        else:
            time = chunk.get_inhabited_time()
            color = _linear_int_to_color(time)
        bitmap = pygame.Surface((16, 16))
        bitmap.fill(color)
        return bitmap
    
    
    def Heightmap(chunk: MCChunk, opt):
        ''' Not used. the heightmap in game is not good for view'''
        heightmap_option = opt[0]
        bitmap = pygame.Surface((16, 16))
        if chunk == None or chunk.get_status() != "minecraft:full":
            bitmap.fill((0,0,0))
            return bitmap
        block_states = chunk.get_blocks_in_heightmap(heightmap_option)
        if not block_states:
            bitmap.fill((0,0,0))
            return bitmap
        colors = [ResourceManager.get_thumb_color(x.data["Name"].data) for x in block_states]
        for index, color in enumerate(colors):
            x ,z = index % 16, index // 16
            bitmap.set_at((x, z), color)
        return bitmap
    
    def highest_opaque(chunk: MCChunk, opt):
        minY, maxY = opt
        bitmap = pygame.Surface((16, 16))
        if chunk == None or chunk.get_status() != "minecraft:full":
            bitmap.fill((0,0,0))
            return bitmap
        ys = chunk.get_highest_non_air_Ys(minY, maxY)
        for index, y in enumerate(ys):
            x ,z = index % 16, index // 16
            color = [0,0,0,0]
            if y!=None:
                while color[3] == 0 and y>=16*minY:
                    bs = chunk.get_block_state(x,y,z)
                    if bs ==None:
                        break
                    color = ResourceManager.get_thumb_color(bs.data["Name"].data)
                    y-=1
            bitmap.set_at((x, z), color)
        return bitmap
    
    def highest_non_air(chunk: MCChunk, opt):
        minY, maxY = opt
        bitmap = pygame.Surface((16, 16))
        if chunk == None or chunk.get_status() != "minecraft:full":
            bitmap.fill((0,0,0))
            return bitmap
        ys = chunk.get_highest_non_air_Ys(minY,maxY)
        for index, y in enumerate(ys):
            x ,z = index % 16, index // 16
            color = [0,0,0,0]
            if y!=None:
                bs = chunk.get_block_state(x,y,z)
                color = ResourceManager.get_thumb_color(bs.data["Name"].data)
            bitmap.set_at((x, z), color)
        return bitmap


view_rules = {
"IsCompleted": ChuckViewRule.IsCompleted,
"InhabitedTime": ChuckViewRule.InhabitedTime,
"Highest Opaque": ChuckViewRule.highest_opaque,
"Highest Non Air" : ChuckViewRule.highest_non_air
}

class ChunkView:
    def __init__(self):
        self.chunk :MCChunk | None = None
        self.views={}

    def load_data(self,chunk: MCChunk | None):
        self.chunk = chunk
        self.views = {}

    def render(self, view_option):
        view_rule, option = view_option[0], view_option[1:]
        bitmap = view_rules[view_rule](self.chunk, option)
        self.views[view_option]=bitmap

    def get_view(self, view_option: tuple[str, ...], border = False):
        if view_option not in self.views:
            self.render(view_option)
        view = self.views[view_option].copy()
        if border:
            pygame.draw.line(view,(200,200,200),(0,0),(0,16),1)
            pygame.draw.line(view,(200,200,200),(0,0),(16,0),1)
        return view
        


def _linear_int_to_color(value, lo = 0, hi = 3600000, lo_color = (255, 255, 255), hi_color = (0, 0, 139)):
    if value <= lo:
        return lo_color
    elif value >= hi:
        return hi_color
    else:
        ratio = value / (hi-lo)
        r = int(lo_color[0] + ratio * (hi_color[0] - lo_color[0]))
        g = int(lo_color[1] + ratio * (hi_color[1] - lo_color[1]))
        b = int(lo_color[2] + ratio * (hi_color[2] - lo_color[2]))
        return (r,g,b)