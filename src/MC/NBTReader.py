from enum import Enum
import struct
import gzip
import zlib

### NBT tags

byte_order= "big"

class NBT_tag(Enum):
    TAG_End = 0
    # int
    TAG_Byte = 1
    TAG_Short = 2
    TAG_Int = 3
    TAG_Long = 4    
    # float
    TAG_Float = 5
    TAG_Double = 6
    # Bytes
    TAG_Byte_Array = 7 
    # str
    TAG_String = 8
    # list[nbt] (the nbts have no name)
    TAG_List = 9   
    # dict[name: nbt]
    TAG_Compound = 10  

    # list[int]
    TAG_Int_Array = 11
    TAG_Long_Array = 12



class NBT():
    def __init__(self):
        self.tag = NBT_tag.TAG_End
        self.name = None
        self.data = None

    def load(self,fileName :str, compression: str = "gzip" ):
        with open(fileName, 'rb') as f:
            content= f.read()
            if compression == "gzip":
                data = gzip.decompress(content)
            elif compression == "zlib":
                data = zlib.decompress(content)    
            elif compression == None:
                data=content
            else:
                raise Exception(f"unknown compression type {compression}.")
        return self.parse(data)
    
    def parse(self, bytes: bytes):
        self.bytes=bytes
        self.__index__=0
        self.tag, self.name, self.data = self.__get_full_nbt___()
        del self.__index__
        del self.bytes
        return self


    def __get_full_nbt___(self) -> tuple[NBT_tag, str, object]:
        tag = NBT_tag(int.from_bytes(self.__read__(1),byteorder=byte_order))
        if tag==NBT_tag.TAG_End:
            return tag, None, None
        name_length = int.from_bytes(self.__read__(2),byteorder=byte_order)
        name = self.__read__(name_length).decode("utf-8")
        data = self.__read_nbt_payload__(tag)
        return tag, name, data
  
    def __read_nbt_payload__(self, tag:NBT_tag):
         match tag:
            case NBT_tag.TAG_End:
                return None
            case NBT_tag.TAG_Byte:
                return int.from_bytes(self.__read__(1), byteorder=byte_order, signed=True)
            case NBT_tag.TAG_Short:
                return int.from_bytes(self.__read__(2),byteorder=byte_order, signed=True)
            case NBT_tag.TAG_Int:
                return int.from_bytes(self.__read__(4),byteorder=byte_order, signed=True)
            case NBT_tag.TAG_Long:
                return int.from_bytes(self.__read__(8),byteorder=byte_order, signed=True)
            case NBT_tag.TAG_Float:
                return struct.unpack('>f', self.__read__(4))[0]
            case NBT_tag.TAG_Double:
                return struct.unpack('>d', self.__read__(8))[0]
            case NBT_tag.TAG_Byte_Array:
                arr_len =  int.from_bytes(self.__read__(4), byteorder=byte_order,signed=True)
                return bytearray(self.__read__(arr_len))
            case NBT_tag.TAG_String:
                str_len =  int.from_bytes(self.__read__(2),byteorder=byte_order, signed=False)
                data = self.__read__(str_len).decode("utf-8")
                return data
            case NBT_tag.TAG_List:
                item_tag= NBT_tag(int.from_bytes(self.__read__(1),byteorder=byte_order))
                list_len = int.from_bytes(self.__read__(4),byteorder=byte_order, signed=True)
                data=[]
                for _ in range(list_len):
                    item = NBT()
                    item.tag = item_tag
                    item.data = self.__read_nbt_payload__(item_tag)
                    data.append(item)
                return data 
            case NBT_tag.TAG_Compound:
                data={}
                i_tag, i_name ,i_data = self.__get_full_nbt___()
                while i_tag!=NBT_tag.TAG_End:
                    item = NBT()
                    item.tag = i_tag
                    item.name = i_name
                    item.data = i_data
                    data[i_name] = item
                    i_tag, i_name ,i_data = self.__get_full_nbt___()
                return data
            case NBT_tag.TAG_Int_Array:
                list_len = int.from_bytes(self.__read__(4),byteorder=byte_order, signed=True)
                data=[]
                for _ in range(list_len):
                    data.append(int.from_bytes(self.__read__(4),byteorder=byte_order, signed=True))
                return data
            case NBT_tag.TAG_Long_Array:
                list_len = int.from_bytes(self.__read__(4),byteorder=byte_order, signed=True)
                data=[]
                for _ in range(list_len):
                    data.append(int.from_bytes(self.__read__(8),byteorder=byte_order, signed=True))
                return data
            case _:
                 raise Exception(f"Unknown tag: {tag}")
            
    def __read__(self, length:int) -> bytes:
        b=self.bytes[self.__index__: self.__index__+length]
        self.__index__+=length
        return b
    
    def dump(self, file, compression: str = "gzip" ):
        content = self.dumps(compression)
        with open(file, "wb") as f:
            f.write(content)

    def dumps(self, compression: str = "gzip"):
        content = self._get_raw_bytes()
        if compression == "gzip":
            data = gzip.compress(content)
        elif compression == "zlib":
            data = zlib.compress(content)    
        elif compression == None:
            data=content
        else:
            raise Exception(f"unknown compression type {compression}.")
        return data

    def _get_raw_bytes(self) ->bytes: 
        self._bytes=self.tag.value.to_bytes(1, byteorder=byte_order, signed=False)
        if self.tag==NBT_tag.TAG_End:
            return self._bytes
        self._bytes +=  len(self.name).to_bytes(2, byteorder=byte_order, signed=False)
        self._bytes +=  self.name.encode(encoding="utf-8")
        self._bytes +=  self.__get_nbt_bytes(self.data,self.tag)
        return self._bytes

    def __get_nbt_bytes(self, data, nbt_tag):
        _bytes = b''
        match nbt_tag:
            case NBT_tag.TAG_End:
                return None
            case NBT_tag.TAG_Byte:
                _bytes += data.to_bytes(1, byteorder=byte_order, signed=True) 
            case NBT_tag.TAG_Short:
                _bytes += data.to_bytes(2, byteorder=byte_order, signed=True) 
            case NBT_tag.TAG_Int:
                _bytes += data.to_bytes(4, byteorder=byte_order, signed=True) 
            case NBT_tag.TAG_Long:
                _bytes += data.to_bytes(8, byteorder=byte_order, signed=True) 
            case NBT_tag.TAG_Float:
                _bytes += struct.pack('>f', data)
            case NBT_tag.TAG_Double:
                _bytes += struct.pack('>d', data)
            case NBT_tag.TAG_Byte_Array:
                _bytes += len(data).to_bytes(4, byteorder=byte_order, signed=True) 
                _bytes += bytes(data)
            case NBT_tag.TAG_String:
                byte_str = data.encode(encoding="utf-8")
                _bytes += len(byte_str).to_bytes(2, byteorder=byte_order, signed=False) 
                _bytes += byte_str
            case NBT_tag.TAG_List:
                item_tag = NBT_tag.TAG_End
                if data:
                    item_tag = data[0].tag
                _bytes += item_tag.value.to_bytes(1, byteorder=byte_order, signed=False)
                _bytes += len(data).to_bytes(4, byteorder=byte_order, signed=True) 
                for i in data:
                    _bytes += self.__get_nbt_bytes(i.data, i.tag)
            case NBT_tag.TAG_Compound:
                for i_name in data:
                    item = data[i_name]
                    _bytes += item._get_raw_bytes()
                emt = NBT()
                _bytes += emt._get_raw_bytes()
            case NBT_tag.TAG_Int_Array:
                _bytes += len(data).to_bytes(4, byteorder=byte_order, signed=True) 
                for i in data:
                    _bytes += i.to_bytes(4, byteorder=byte_order, signed=True) 
            case NBT_tag.TAG_Long_Array:
                _bytes += len(data).to_bytes(4, byteorder=byte_order, signed=True) 
                for i in data:
                    _bytes += i.to_bytes(8, byteorder=byte_order, signed=True) 
            case _:
                 raise Exception(f"Unknown tag: {nbt_tag}")
        return _bytes