# Sky-block type map save optimizer
__author__ = "Karol"

import region_file
import os
import nbt_lib as nbt

# ---- INPUT DATA ----
# Chunks to keep - our map
# Format, in chunk coordinates: (startX, endX), (startZ, endZ)
x_start = -37
x_end = -12
z_start = 9
z_end = 30
save_dir = "C:\\Users\\Karol\\AppData\\Roaming\\.minecraft\\saves\\Sky Islands v1.2\\region"


# ---- END - INPUT DATA ----

def limit(xc, zc):
    return x_start <= xc <= x_end and z_start <= zc <= z_end


# Fill remaining chunks with air - in Anvil format - remove vertical sections
delta = 1
path = None
while os.path.exists(path := os.path.join(save_dir, f"###Python_Optimizer_Backup{'#' * delta}")):
    delta += 1
delta = 0
os.mkdir(path)
emptyHeightMap = [0] * 256
for r, d, files in os.walk(save_dir):
    if "###Python_Optimizer_Backup" in r:
        continue
    print(r)
    for f in files:
        src = os.path.join(r, f)
        dest = os.path.join(r, path, f)
        os.rename(src, dest)
        source = region_file.RegionFile(dest)
        target = region_file.RegionFile(src)
        for c in range(0, 1024):
            x = c % 32
            z = c // 32
            if source.has_chunk(x, z):
                try:
                    tag = nbt.read(source.read_chunk(x, z)).get("Level")
                    xw = tag.get("xPos")
                    zw = tag.get("zPos")
                    if not limit(xw, zw):
                        tag.get("Sections").clear()
                        tag.get("Entities").clear()
                        tag.get("TileEntities").clear()
                        if tag.contains("TileTicks"):
                            tag.get("TileTicks").clear()
                        tag.put(nbt.IntArray("HeightMap", emptyHeightMap))
                        tag.put(nbt.Byte("LightPopulated", 0))
                        tag.remove("V")
                        tag.put(nbt.Long("InhabitedTime", 0))
                        tag.put(nbt.Long("LastUpdate", 0))
                    nbt.write(nbt.root("").put(tag), target.write_chunk(x, z))
                except BaseException as e:
                    print(e)
        target.close()
        source.close()
        delta += os.path.getsize(dest) - os.path.getsize(src)
        del source, target
print(f"Zaoszczędzono: {delta / 1048576} MB")
