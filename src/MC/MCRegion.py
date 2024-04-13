from concurrent.futures import ProcessPoolExecutor,as_completed
from MC.NBTReader import NBT
from MC.MCChunk import MCChunk
import zlib
from Overview.GlobalEvents import log, send_draw_event
import atexit

chunk_load_executor = ProcessPoolExecutor()
atexit.register(lambda: chunk_load_executor.shutdown(False))

sector_length = 4096
byte_order= "big"

def load_chunk(info):
    data, timestamp = info
    return MCChunk(_read_chunk(data),timestamp,None)

class MCRegion():
    def __init__(self, filename):
        self.chunks_timestamps : list[int] = None
        self.xz_chunks : dict[tuple[int,int], MCChunk] = {}
        self.fileName = filename
        self.loaded = False
        self.loading = False

    def load_in_background(self):
        self.loading = True
        log("loading: "+self.fileName)
        with open(self.fileName, 'rb') as f:
            _content= f.read()
            _chunk_infos = [_content[i*4:i*4+4] for i in range(1024)]
            self.chunks_timestamps = [int.from_bytes(_content[i*4:i*4+4],byte_order) for i in range(1024,2048)]
                        
            def collect_chunk_data():
                for i in range(1024):
                    info = _chunk_infos[i]
                    offset = int.from_bytes(info[:3],byte_order)
                    sector_count =  int.from_bytes(info[3:4],byte_order)
                    if sector_count !=0:
                        yield _content[offset*sector_length: offset*sector_length+sector_count*sector_length], self.chunks_timestamps[i]

            
            futures = [chunk_load_executor.submit(load_chunk, info) for info in collect_chunk_data()]
            for future in as_completed(futures):
                c = future.result()
                c.region = self
                self.xz_chunks [c.get_xz()] = c 
                send_draw_event()
            self.loaded = True
            self.loading = False
            log("loaded: "+self.fileName)
            '''
            for i in range(1024):
                info = _chunk_infos[i]
                offset = int.from_bytes(info[:3],byte_order)
                sector_count =  int.from_bytes(info[3:4],byte_order)
                if sector_count !=0:
                    chunk_data = _content[offset*sector_length: offset*sector_length+sector_count*sector_length]
                    chunk = MCChunk(_read_chunk(chunk_data),self.chunks_timestamps[i],self)
                    x,z = chunk.get_xz()
                    self.xz_chunks[(x,z)] = chunk
                    send_draw_event()
            '''
        return self

    def load(self):
        self.loading = True
        with open(self.fileName, 'rb') as f:
            _content= f.read()
            _chunk_infos = [_content[i*4:i*4+4] for i in range(1024)]
            self.chunks_timestamps = [int.from_bytes(_content[i*4:i*4+4],byte_order) for i in range(1024,2048)]
            for i in range(1024):
                info = _chunk_infos[i]
                offset = int.from_bytes(info[:3],byte_order)
                sector_count =  int.from_bytes(info[3:4],byte_order)
                if sector_count !=0:
                    chunk_data = _content[offset*sector_length: offset*sector_length+sector_count*sector_length]
                    chunk = MCChunk(_read_chunk(chunk_data),self.chunks_timestamps[i],self)
                    x,z = chunk.get_xz()
                    self.xz_chunks[(x,z)] = chunk
                    send_draw_event()
        self.loaded = True
        self.loading = False

        log("loaded: "+self.fileName)
        return self
    

    def get_chunk(self,x,z) -> MCChunk | None:
        if (x,z) in self.xz_chunks:
            return self.xz_chunks[(x,z)]
        return None

    def remove_chunk(self, x, z):
        if (x,z) in self.xz_chunks:
            self.xz_chunks[(x,z)] = None
        
    def dump(self,file): #TODO
        chunk_bytes = [x.nbt.dumps(compression = "zlib") if x else b'' for x in self.xz_chunks.values()]
        sector_lengths = [0 if len(b)==0 else (len(b)+5-1)//sector_length + 1 for b in chunk_bytes] # +5: chunk length (4) and compression type (1)
        offsets = [2]
        for i in range(1023):
            offsets.append(offsets[-1]+sector_lengths[i])

        with open(file, "wb") as f:

            # write chunk info

            for i in range(1024):
                f.write(int.to_bytes(offsets[i], 3, byte_order))
                f.write(int.to_bytes(sector_lengths[i],1,byte_order))

            # write timestamp

            for i in range(1024):
                f.write(int.to_bytes(self.chunks_timestamps[i], 4, byte_order))

            # write chunk data

            for i in range(1024):
                if sector_lengths[i]>0:
                    cbl = sector_lengths[i]*sector_length
                    cb= int.to_bytes(len(chunk_bytes[i]),4,byte_order) + int.to_bytes(2,1,byte_order) + chunk_bytes[i] + (cbl - len(chunk_bytes[i]) - 5) * b'\x00'
                    f.write(cb)

def _read_chunk(content):
    if not content:
        return None
    return _read_chunk_as_nbt(content)

    
def _read_chunk_as_nbt(data):
    length = int.from_bytes(data[:4],byte_order)
    compressionType = int.from_bytes(data[4:5],byte_order)
    payload = data[5:5+length]
    if compressionType == 2:   # default => zlib
        chunk = zlib.decompress(payload)
        return  NBT().parse(chunk)
    else:
        raise Exception(f"unknown compression type {compressionType}.")