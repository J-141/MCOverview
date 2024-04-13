from MC.NBTReader import NBT


def require_full_status(func):
    def wrapper(chunk, *args, **kwargs):
        if chunk.get_status() != "minecraft:full":
                return None
        return func(chunk, *args, **kwargs)
    return wrapper

HEIGHTMAP_TYPES = [
    "OCEAN_FLOOR",
    "MOTION_BLOCKING_NO_LEAVES",
    "MOTION_BLOCKING",
    "WORLD_SURFACE"
]

class MCChunk():
    def __init__(self,nbt: NBT, timestamp: int, region):
        self.region = region
        self.timestamp = timestamp
        self.max_non_air_Ys : dict[int, list[int]] = {} # secY: xz => Ys 
        self.load_nbt(nbt)

    def load_nbt(self, nbt):
        self.nbt : NBT = nbt
        self.first_section_Y = self.nbt.data["sections"].data[0].data["Y"].data

    def get_xz(self) -> tuple[int,int]:
        return (self.nbt.data["xPos"].data,self.nbt.data["zPos"].data)
    
    def get_status(self):
        return self.nbt.data["Status"].data
    
    def get_inhabited_time(self):
        return self.nbt.data["InhabitedTime"].data
    
    
    @require_full_status
    def _get_section(self, sectionY:int):
        # each chunk contains 24 sections
        # sectionY is from -4 ~ 19, corresponding y from -64~320
        if sectionY < self.first_section_Y or sectionY >= len(self.nbt.data["sections"].data) + self.first_section_Y:
            return None
        return self.nbt.data["sections"].data[sectionY - self.first_section_Y]
    
    @require_full_status
    def get_blocks_in_heightmap(self, heightmap_option):
        ys = self.get_heightmap_Ys(heightmap_option)
        if not ys:
            return None
        blocks= [self.get_block_state(i%16, y, i//16) for i,y in enumerate(ys)]
        return blocks
    
    @require_full_status
    def get_heightmap_Ys(self, heightmap_option) -> list[int]:
        if heightmap_option not in HEIGHTMAP_TYPES:
            raise Exception("Invalid heightmap option.")
        if "Heightmaps" not in self.nbt.data:
            return None
        hmap = self.nbt.data["Heightmaps"].data[heightmap_option].data
        def bit_9_section(long:int):
            while(long):
                long, rem = long // (2**9), long % (2**9)
                yield rem
        ys = [j-65 for x in hmap for j in reversed(list(bit_9_section(x)))] # heightmap contains the absolute height from -64
        return ys
    
    @require_full_status
    def get_highest_non_air_Ys_for_section (self, section_Y: int): # return absolute Y
        sec = self._get_section(section_Y)
        if not sec or "block_states" not in sec.data:
            return None
        
        palette = sec.data["block_states"].data["palette"].data
        if not any(x.data["Name"].data == "minecraft:air" for x in palette): # no air
            return [section_Y*16+15] * 256
        
        if len(palette) ==1: # all air
            return [None] * 256
        
        air_ind  =  next(i for i,v in enumerate(palette) if v.data["Name"].data == "minecraft:air")
        ys=[None] * 256
        data = sec.data["block_states"].data["data"].data
        for y in range(15,-1,-1):
            for ind in range(256):
                    if ys[ind]!=None:
                        continue
                    data_ind = y * 256 + ind
                    bit_len = max((len(palette)-1).bit_length(),4)   # important!!
                    pack_number =  64//bit_len
                    data_i, data_r = data_ind // pack_number, data_ind % pack_number
                    palette_ind = ((data[data_i] & 0xFFFFFFFFFFFFFFFF) >> (bit_len * data_r))  & (2**bit_len-1)
                    if palette_ind !=air_ind:
                        ys[ind] = y + section_Y*16
            if None not in ys:
                break
        return ys

        
    @require_full_status
    def get_highest_non_air_Ys(self,  min_section_Y:  int = -65535, max_section_Y: int = 65565) -> list[int]: #
        '''get highest Y that is not air block. if section_Y specified, the sections outside of section_Y would be ignored.'''
        ys=[None] * 256

        min_section_Y = max(min_section_Y, self.first_section_Y)
        max_section_Y = min(max_section_Y, self.nbt.data["sections"].data[-1].data["Y"].data)

        for seci in range(max_section_Y, min_section_Y - 1, -1):
            if new_ys := self.get_highest_non_air_Ys_for_section(seci):
                ys = [ys[i] if ys[i]!=None else new_ys[i] for i in range(256)]
                if None not in ys:
                    break
        return ys
                

    @require_full_status
    def get_block_state(self,x,y,z) -> NBT:
        '''
        x, z are coord within the chunk.
        data order in multidimentional array: y-z-x 
        '''
        try:
            section = self. _get_section(y//16)
            if section == None or "block_states" not in section.data:
                return None
            palette = section.data["block_states"].data["palette"].data
            if len(palette) == 1:
                return palette[0]
            bit_len = max((len(palette)-1).bit_length(),4)   # important!!
            pack_number =  64//bit_len
            data = section.data["block_states"].data["data"].data

            data_ind = (((y %16) * 16 + z) * 16 + x)
            data_i, data_r = data_ind // pack_number, data_ind % pack_number

            palette_ind = ((data[data_i] & 0xFFFFFFFFFFFFFFFF) >> (bit_len * data_r))  & (2**bit_len-1)
            return palette[palette_ind]
        
        except:
            print(x,y,z,self.get_xz())
            raise

