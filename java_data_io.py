import gzip
from struct import *


class DataIO:
    def __init__(self, stream):
        self.stream = stream

    def read_boolean(self):
        return unpack('?', self.stream.read(1))[0]

    def read_byte(self):
        return unpack('b', self.stream.read(1))[0]

    def read_unsigned_byte(self):
        return unpack('B', self.stream.read(1))[0]

    def read_char(self):
        return chr(unpack('>H', self.stream.read(2))[0])

    def read_double(self):
        return unpack('>d', self.stream.read(8))[0]

    def read_float(self):
        return float(unpack('>f', self.stream.read(4))[0])

    def read_short(self):
        return unpack('>h', self.stream.read(2))[0]

    def read_unsigned_short(self):
        return unpack('>H', self.stream.read(2))[0]

    def read_long(self):
        return unpack('>q', self.stream.read(8))[0]

    def read_utf(self):
        utf_length = self.read_unsigned_short()
        return self.stream.read(utf_length).decode("utf-8")

    def read_int(self):
        return unpack('>i', self.stream.read(4))[0]

    def read(self, length):
        return self.stream.read(length)

    def write_boolean(self, bool):
        self.stream.write(pack('?', bool))

    def write_byte(self, val):
        self.stream.write(pack('b', val))

    def write_unsigned_byte(self, val):
        self.stream.write(pack('B', val))

    def write_char(self, val):
        self.stream.write(pack('>H', ord(val)))

    def write_double(self, val):
        self.stream.write(pack('>d', val))

    def write_float(self, val):
        self.stream.write(pack('>f', val))

    def write_short(self, val):
        self.stream.write(pack('>h', val))

    def write_unsigned_short(self, val):
        self.stream.write(pack('>H', val))

    def write_long(self, val):
        self.stream.write(pack('>q', val))

    @staticmethod
    def __utf_length(self, string, start, sum):
        le = len(string)
        i = start
        while i < le and sum <= 65535:
            c = string[i]
            i += 1
            if '\u0001' <= c <= '\u007f':
                sum += 1
            elif c == '\u0000' or ('\u0080' <= c <= '\u07ff'):
                sum += 2
            else:
                sum += 3
        if sum > 65536:
            print("Danusia we have a problem")
        return sum

    def write_utf(self, string):
        le = len(string)
        i = 0
        length_written = False
        buf_len = 512
        while True:
            buf = bytearray()
            while i < le and len(buf) < buf_len - 3:
                c = string[i]
                i += 1
                if '\u0001' <= c <= '\u007f':
                    buf.append(ord(c))
                elif c == '\u0000' or ('\u0080' <= c <= '\u07ff'):
                    buf.append(0xc0 | (0x1f & (ord(c) >> 6)))
                    buf.append(0x80 | (0x3f & ord(c)))
                else:
                    buf.append(0xe0 | (0x0f & (ord(c) >> 12)))
                    buf.append(0x80 | (0x3f & (ord(c) >> 6)))
                    buf.append(0x80 | (0x3f & ord(c)))
            if not length_written:
                if i == le:
                    self.write_short(len(buf))
                else:
                    self.write_short(self.__getUTFLength(string, i, len(buf)))
                length_written = True
            self.stream.write(buf)
            if i >= le:
                break

    def write_int(self, val):
        self.stream.write(pack('>i', val))

    def write(self, bytes):
        self.stream.write(bytes)

    def flush(self):
        self.stream.flush()

    def seek(self, offset):
        self.stream.seek(offset)

    def jumpToEnd(self):
        self.stream.seek(0, 2)


    def close(self):
        self.stream.close()

    def length(self):
        pos = self.stream.tell()
        self.jumpToEnd()
        ret = self.stream.tell()
        self.stream.seek(pos)
        return ret


class FileIO:
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stream.__exit__()

    def __enter__(self):
        return self.stream

    def __init__(self, path, mode):
        mode = mode.lower().replace("i", "r").replace("o", "w").replace("a", "a")
        self.stream = open(path, mode + "b+")

    def close(self):
        self.stream.close()


class GZFileIO:
    def __init__(self, path, mode):
        mode = mode.lower().replace("i", "r").replace("o", "w")
        self.stream = gzip.open(path, mode + "b+")

    def close(self):
        self.stream.close()


class ByteArrayIO:
    def __init__(self, bytearr=None):
        self.bytearr = bytearr
        self.offset = 0
        if self.bytearr is None:
            self.count = 0
            self.bytearr = bytearray()
        else:
            self.count = len(bytearr)

    def read(self, length):
        bytes = self.bytearr[self.offset: self.offset + length]
        self.offset += length
        return bytes

    def seek(self, index):
        self.offset = index;

    def write(self, bytes):
        end = self.offset + len(bytes)
        if end >= self.count:
            self.count = end + 1
        self.bytearr[self.offset : end] = bytes
        self.offset += len(bytes)

    def close(self):
        pass
