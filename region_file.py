"""
Original Author of the Region File Format: Ryan 'Scaevolus' Hitchman
This is a Python implementation, based off original source code written 
in Java and published by Mojang along with the Anvil Converter tool.

/*

 Region File Format

 Concept: The minimum unit of storage on hard drives is 4KB. 90% of Minecraft
 chunks are smaller than 4KB. 99% are smaller than 8KB. Write a simple
 container to store chunks in single input in runs of 4KB sectors.

 Each region file represents a 32x32 group of chunks. The conversion from
 chunk number to region number is floor(coord / 32): a chunk at (30, -3)
 would be in region (0, -1), and one at (70, -30) would be at (3, -1).
 Region input are named "r.x.z.data", where x and z are the region coordinates.

 A region file begins with a 4KB header that describes where chunks are stored
 in the file. A 4-byte big-endian integer represents sector offsets and sector
 counts. The chunk offset for a chunk (x, z) begins at byte 4*(x+z*32) in the
 file. The bottom byte of the chunk offset indicates the number of sectors the
 chunk takes up, and the top 3 bytes represent the sector number of the chunk.
 Given a chunk offset o, the chunk data begins at byte 4096*(o/256) and takes up
 at most 4096*(o%256) bytes. A chunk cannot exceed 1MB in size. If a chunk
 offset is 0, the corresponding chunk is not stored in the region file.

 Chunk data begins with a 4-byte big-endian integer representing the chunk data
 length in bytes, not counting the length field. The length must be smaller than
 4096 times the number of sectors. The next byte is a version field, to allow
 backwards-compatible updates to how chunks are encoded.

 A version of 1 represents a gzipped NBT file. The gzipped data is the chunk
 length - 1.

 A version of 2 represents a deflated (zlib compressed) NBT file. The deflated
 data is the chunk length - 1.

 */

"""
import gzip, zlib, time, os
from java_data_io import *

__author__ = "Karol"

# Stałe
version_gzip = 1
version_zlib = 2
sector_bytes = 4096  # 4kB
sector_ints = sector_bytes // 4  # 1 int (32 bit) = 4 byte (8 bit)
chunk_header_size = 5
empty_sector = bytearray(sector_bytes)
max_chunk_size = 1048576 // sector_bytes
dbg = lambda self, x: print(f"[REGION]|['{self.fileName}']|[{'EXCEPTION' if isinstance(x, Exception) else 'INFO'}]: {x}")


class RegionFile:

    def __init__(self, file_name):
        self.fileName = file_name
        self.offsets = [0] * sector_ints
        self.chunkTimestamps = [0] * sector_ints
        self.sizeDelta = 0
        self.lastModified = 0

        #dbg(self, "LOAD ")

        try:
            if os.path.exists(file_name):
                self.lastModified = os.path.getmtime(file_name)
            else:
                # Utwórz plik
                with open(file_name, "wb") as f:
                    f.write("ASCII Python Works".encode("ASCII"))
                    dbg(self, "FILE create")
            self.file = DataIO(FileIO(file_name, "i").stream)
            self.file.seek(0)
            if self.file.length() < sector_bytes:
                # Plik jest pusty
                # Zainicjuj dwa pierwsze sektory na tablice: offset, timestamp
                for x in range(0, sector_ints * 2):
                    self.file.write_int(0)
                self.sizeDelta += sector_bytes * 2

            if self.file.length() & 0xfff != 0:
                # Plik składa się z sektorów po 4 KB, i ta wartość jest swoistą sumą kontrolną pliku.
                # Więc długość pliku powinna być wielokrotnością 4KB,
                # jeżeli nie jest, uzupełnij plik zerami.
                # Być może plik został ucięty i utracono część danych,
                # zatem spróbujmy uratować to, co zostało..
                dbg(self, "COMPLEMENT")
                for x in range(0, self.file.length() & 0xfff):
                    self.file.write(bytearray(1))

            # Oblicz, z ilu sektorów aktualnie składa się plik
            n_sectors = self.file.length() // sector_bytes
            # dbg(self, f"SECTORS {n_sectors}")
            self.sectorFree = [True] * n_sectors
            self.sectorFree[0] = False
            self.sectorFree[1] = False
            self.file.seek(0)
            for x in range(0, sector_ints):
                offset = self.file.read_int()
                self.offsets[x] = offset

                if offset != 0 and (offset >> 8) + (offset & 0xFF) <= sector_ints:
                    for sectorNum in range(0, offset & 0xFF):
                        self.sectorFree[(offset >> 8) + sectorNum] = False
            for x in range(0, sector_ints):
                self.chunkTimestamps[x] = self.file.read_int()

        except BaseException as e:
            print(e)

    def last_modified(self):
        return self.lastModified

    @staticmethod
    def out_of_bounds(x, z):
        return x < 0 or x >= 32 or z < 0 or z >= 32

    def get_offset(self, x, z):
        return self.offsets[x + z * 32]

    def set_offset(self, x, z, offset):
        self.offsets[x + z * 32] = offset
        self.file.seek((x + z * 32) * 4)
        self.file.write_int(offset)

    def has_chunk(self, x, z):
        if self.out_of_bounds(x, z):
            return False
        return self.get_offset(x, z) != 0

    def set_timestamp(self, x, z, value):
        self.chunkTimestamps[x + z * 32] = value
        self.file.seek(sector_bytes + (x + z * 32) * 4)
        self.file.write_int(value)

    def get_timestamp(self, x, z):
        return self.chunkTimestamps[x + z * 32]

    def close(self):
        self.file.close()

    def read_chunk(self, x, z):
        if self.out_of_bounds(x, z):
            dbg(self, f"READ {x, z} out of bounds")
            return None
        try:
            offset = self.get_offset(x, z)
            if offset == 0:
                return None

            sector_num = offset >> 8
            num_sectors = offset & 0xFF
            if sector_num + num_sectors > len(self.sectorFree):
                dbg(self, f"READ {x, z} invalid sector")
                return None
            self.file.seek(sector_num * sector_bytes)
            length = self.file.read_int()
            if length > sector_bytes * num_sectors:
                dbg(self, f"READ {x, z} invalid length: {length} > {sector_bytes * num_sectors}")
                return None
            version = self.file.read_byte()
            raw = self.file.read(length - 1)
            if version == version_gzip:
                # dbg(self, f"READ {x, z} GZIP")
                return DataIO(ByteArrayIO(gzip.decompress(raw)))
            elif version == version_zlib:
                # dbg(self, f"READ {x, z} ZLIB")
                return DataIO(ByteArrayIO(zlib.decompress(raw)))
            dbg(self, f"READ {x, z} unknown version '{version}'")
        except IOError as e:
            dbg(self, f"READ {x, z} exception")
            dbg(self, e)
        return None

    def __write(self, sector_num, data, length):
        self.file.seek(sector_num * sector_bytes)
        self.file.write_int(length + 1)
        self.file.write_byte(version_zlib)
        self.file.write(data)

    def write(self, x, z, data, length):
        try:
            offset = self.get_offset(x, z)
            sector_num = offset >> 8
            alloc_sectors = offset & 0xFF
            sectors_needed = (length + chunk_header_size) // sector_bytes + 1
            if sectors_needed >= max_chunk_size:
                dbg(self, f"SAVE {x, z} oversize")
                return

            if sector_num != 0 and alloc_sectors == sectors_needed:
                # dbg(self, f"SAVE {x, z} rewrite")
                self.__write(sector_num, data, length)
            else:
                self.sectorFree[sector_num:sector_num + alloc_sectors] = [True] * alloc_sectors
                run_start = -1
                try:
                    run_start = self.sectorFree.index(True)
                except ValueError:
                    pass
                run_length = 0
                if run_start != -1:
                    for i in range(run_start, len(self.sectorFree)):
                        if run_length != 0:
                            if self.sectorFree[i]:
                                run_length += 1
                            else:
                                run_length = 0
                        elif self.sectorFree[i]:
                            run_start = i
                            run_length = 1
                        if run_length >= sectors_needed:
                            break
                if run_length >= sectors_needed:
                    # dbg(self, f"SAVE {x, z} rewrite")
                    sector_num = run_start
                    self.set_offset(x, z, (sector_num << 8) | sectors_needed)
                    for i in range(0, sectors_needed):
                        self.sectorFree[sector_num + i] = False
                    self.__write(sector_num, data, length)
                else:
                    # dbg(self, f"SAVE {x, z} allocate")
                    self.file.seek(self.file.length())
                    sector_num = len(self.sectorFree)
                    for i in range(0, sectors_needed):
                        self.file.write(empty_sector)
                        self.sectorFree.append(False)
                    self.sizeDelta += sector_bytes * sectors_needed
                    self.__write(sector_num, data, length)
                    self.set_offset(x, z, (sector_num << 8) | sectors_needed)
            self.set_timestamp(x, z, time.time_ns() // 1000000000)
        except IOError as e:
            dbg(self, f"SAVE {x, z} exception")
            dbg(self, e)

    class RegionBuffer(ByteArrayIO):
        def __init__(self, region, x, z):
            ByteArrayIO.__init__(self)
            self.region = region
            self.count = 0
            self.x = x
            self.z = z

        def close(self):
            self.bytearr = zlib.compress(self.bytearr)
            self.region.write(self.x, self.z, self.bytearr, len(self.bytearr))

    def write_chunk(self, x, z):
        if self.out_of_bounds(x, z):
            return None
        return DataIO(self.RegionBuffer(self, x, z))
