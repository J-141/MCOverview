import os 
from MC.MCChunk import MCChunk
from MC.NBTReader import NBT
from MC.MCRegion import MCRegion
import threading



class MCDIM:
    def __init__(self,directory):
        region_dir=os.path.join(directory,'region')
        self.regions :  dict[tuple[int,int], MCRegion]  = {}
        for file in os.listdir(region_dir):
            coord = tuple(int(x) for x in file.split(".")[1:3]) # r.x.z
            self.regions[coord] = MCRegion(os.path.join(region_dir,file))
            
    def get_block_state(self,x,y,z):
        chunkX, chunkZ = x>>4, z>>4
        return self.get_chunk(chunkX,chunkZ).get_block_state(x%16, y, z%16)
    
    def remove_block(self,x,z):
        regionX, regionZ = x >> 5, z>>5
        if (regionX, regionZ) in self.regions:
            self.regions[(regionX, regionZ)].remove_chunk(x,z)

    def get_chunk_no_block(self,x,z):
        regionX, regionZ = x >> 5, z>>5
        if (regionX, regionZ) in self.regions:
            region = self.regions[(regionX, regionZ)]
            if not region.loaded:
                if not region.loading:
                    thread = threading.Thread(target=region.load_in_background)
                    thread.start()
            return region.get_chunk(x,z)
    
    def get_chunk(self,x,z) -> MCChunk:
        regionX, regionZ = x >> 5, z>>5
        if (regionX, regionZ) in self.regions:
            region = self.regions[(regionX, regionZ)]
            if not region.loaded:
                if not region.loading:
                    region.load()
            return region.get_chunk(x,z)
        
class MCWorld:
    def __init__(self,directory):
        overworld = MCDIM(directory)
        nether = MCDIM(os.path.join(directory,'DIM-1'))
        end= MCDIM(os.path.join(directory,'DIM1'))

        self.DIMs: dict[int, MCDIM]={
            0:overworld,
            1:end,
            -1:nether
        }
        self.level = NBT().load(os.path.join(directory,'level.dat'))