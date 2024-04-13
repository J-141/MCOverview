import zipfile, json
from PIL import Image
from io import BytesIO
from MC.NBTReader import NBT    

#  manage resource as a singleton

def _get_block_name(filename):
    name = filename.split(":")[-1].split("/")[-1].split(".")[0]
    return name

block_states = {}
block_models = {}
block_textures = {}

with open("src\\MC\\Blocks\\block_info.json", "r") as f:
        block_info = json.load(f)
bame= set()


def get_thumb_color(block_name):
    block_name = _get_block_name(block_name)
    if block_name in block_info:
        if "thumbnail-color" in block_info[block_name]:
            if block_name not in bame and block_info[block_name]["thumbnail-color"] == [255,255,255,0]:
                bame.add(block_name)
                #print(block_name)
            return tuple(block_info[block_name]["thumbnail-color"])
    return (255,255,255,0)
    

def load_resource (file): 
    resource = zipfile.ZipFile(file)
    block_state_dir = "assets/minecraft/blockstates"
    block_model_dir = "assets/minecraft/models/block"
    block_texture_dir = "assets/minecraft/textures/block"

    for file_info in resource.infolist():
        _name = _get_block_name(file_info.filename) 

        if file_info.filename.startswith(block_state_dir):
            with resource.open(file_info.filename) as file:
                block_states[_name] = json.loads(file.read())

        elif file_info.filename.startswith(block_model_dir):
            with resource.open(file_info.filename) as file:
                block_models[_name] = json.loads(file.read())

        elif file_info.filename.startswith(block_texture_dir):
            if file_info.filename.endswith(".png"):
                with resource.open(file_info.filename) as file:
                    file_bytes = BytesIO(file.read())
                    block_textures[_name] = Image.open(file_bytes)



def get_model_by_block_nbt(block_state_nbt: NBT):
    block_name = block_state_nbt.data["Name"].data
    if "Properties" in block_state_nbt.data:
        block_state = {k:v.data for k,v in block_state_nbt.data["Properties"].data.items()}
    else:
        block_state = {}
    return get_model_by_block_state(block_name,block_state)

def get_model_by_block_state(block_name: str, block_state: dict[str,str]):
    _name = _get_block_name(block_name)
    if _name in block_states:
        if "variants" in block_states[_name]:   # one model or a list of models
            match_v, match_k = max([(_match_states(block_state,k),k) for k in block_states[_name]["variants"]])
            return block_states[_name]["variants"][match_k]
        elif "multipart" in block_states[_name]:
            return block_states[_name]["multipart"]    # or a multipart model
    return None

def _match_states(query: dict[str,str],state_as_k:str):
    state = _get_state_dict(state_as_k)
    return sum(1 if k in query and query[k]==state[k] else 0 for k in state_as_k)

def _get_state_dict(state: str):
        if state == "":
            return {}
        return {k:v for (k,v) in [x.split("=") for x in state.split(",")] }