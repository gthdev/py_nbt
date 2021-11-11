__author__ = 'Karol'

import java_data_io as dio

tagId = (
    "End", "Byte", "Short", "Int", "Long", "Float", "Double", "Byte_Array", "String", "List", "Compound", "Int_Array",
    "Long_Array")


def _read_named_tag(datain):
    id = datain.read_byte()
    if id == 0:
        return End()
    name = datain.read_utf()
    tag = create_tag(id, name)
    tag.read(datain)
    return tag


def _write_named_tag(tag, dataos):
    dataos.write_byte(tag.get_id())
    if tag.get_id() == 0:
        return
    dataos.write_utf(tag.name)
    tag.write(dataos)


def read(datais):
    tag = _read_named_tag(datais)
    if isinstance(tag, Compound):
        return tag
    raise IOError("Root tag must be a named compound tag")


def read_is(input_stream):
    return read(dio.DataIO(input_stream))


def write(root, dataout, close = True):
    if root.get_id() != 10:
        raise IOError("Root tag must be a named compound tag")
    _write_named_tag(root, dataout)
    if close:
        dataout.close()


def write_os(root, output_stream):
    write(root, dio.DataIO(output_stream))


def root(name = "NBT w Pythonie"):
    return Compound(name)


def create_tag(id, name):
    tag = None
    if id == 0:
        tag = End()
    elif id == 1:
        tag = Byte(name, None)
    elif id == 2:
        tag = Short(name, None)
    elif id == 3:
        tag = Int(name, None)
    elif id == 4:
        tag = Long(name, None)
    elif id == 5:
        tag = Float(name, None)
    elif id == 6:
        tag = Double(name, None)
    elif id == 7:
        tag = ByteArray(name, None)
    elif id == 8:
        tag = String(name, None)
    elif id == 9:
        tag = List(name)
    elif id == 10:
        tag = Compound(name)
    elif id == 11:
        tag = IntArray(name, None)
    elif id == 12:
        tag = LongArray(name, None)
    else:
        raise TypeError("Unknown tag ID")
    return tag


class Tag:
    def __init__(self, name, data):
        self.name = name
        self.data = data

    def __str__(self):
        return str("NBT::" + str(tagId[self.get_id()]) + "Tag_" + self.name)


class End(Tag):
    def __init__(self): pass

    def write(self, dataos): pass

    def read(self, datais): pass

    def get_id(self):
        return 0

    def __str__(self):
        return str("NBT::EndTag!")


class Byte(Tag):
    def write(self, dataos):
        dataos.write_byte(self.data)

    def read(self, datais):
        self.data = datais.read_byte()

    def get_id(self):
        return 1


class Short(Tag):
    def write(self, dataos):
        dataos.write_short(self.data)

    def read(self, datais):
        self.data = datais.read_short()

    def get_id(self):
        return 2


class Int(Tag):
    def write(self, dataos):
        dataos.write_int(self.data)

    def read(self, datais):
        self.data = datais.read_int()

    def get_id(self):
        return 3


class Long(Tag):
    def write(self, dataos):
        dataos.write_long(self.data)

    def read(self, datais):
        self.data = datais.read_long()

    def get_id(self):
        return 4


class Float(Tag):
    def write(self, dataos):
        dataos.write_float(self.data)

    def read(self, datais):
        self.data = datais.read_float()

    def get_id(self):
        return 5


class Double(Tag):
    def write(self, dataos):
        dataos.write_double(self.data)

    def read(self, datais):
        self.data = datais.read_double()

    def get_id(self):
        return 6


class ByteArray(Tag):
    def write(self, dataos):
        dataos.write_int(len(self.data))
        dataos.write(self.data)

    def read(self, datais):
        self.data = datais.read(datais.read_int())

    def get_id(self):
        return 7

    def __str__(self):
        return "[" + str(len(self.data)) + " bytes]"


class String(Tag):
    def write(self, dataos):
        dataos.write_utf(self.data)

    def read(self, datais):
        self.data = datais.read_utf()

    def get_id(self):
        return 8

    def __str__(self):
        return self.data


def is_empty(list_inst):
    return list_inst.data is None or len(list_inst.data) == 0


class List(Tag):
    def __init__(self, name):
        self.name = name
        self.data = []
        self.type = 0

    def put(self, tag):
        if is_empty(self):
            self.data = []
        elif self.data[0].get_id() != tag.get_id():
            raise AttributeError(f"Adding {tagId[tag.get_id()]} tag to list of {tagId[self.data[0].get_id()]}")
        self.data.append(tag)

    def get(self, i):
        return self.data[i]

    def get_type(self):
        return self.type

    def write(self, dataos):
        if is_empty(self):
            self.type = 0
        else:
            self.type = self.data[0].get_id()
        dataos.write_byte(self.type)
        dataos.write_int(len(self.data))
        for tag in self.data:
            tag.write(dataos)

    def read(self, datais):
        self.type = datais.read_byte()
        size = datais.read_int()
        self.data = []
        for x in range(0, size):
            tag = create_tag(self.type, None)
            tag.read(datais)
            self.data.append(tag)

    def get_id(self):
        return 9

    def clear(self):
        self.data.clear()

    def __str__(self):
        return f"List of {tagId[self.type]}; length: {len(self.data)} entries"

class Compound(Tag):
    def __init__(self, name):
        self.name = name
        self.data = {}

    def write(self, dataos):
        for name, tag in self.data.items():
            _write_named_tag(tag, dataos)
        _write_named_tag(End(), dataos)

    def read(self, datais):
        self.data = {}
        while True:
            tag = _read_named_tag(datais)
            if tag.get_id() != 0:  # TAG_End
                self.data[tag.name] = tag
            else:
                break

    def get_tag(self, name):
        return self.data[name]

    def contains(self, name):
        return name in self.data

    def get(self, name):
        tag = self.data[name]
        if tag.get_id() == 10:
            return tag
        return tag.data


    def put(self, tag):
        self.data[tag.name] = tag
        return self

    def remove(self, name):
        self.data.pop(name, None)

    def pop(self, name):
        return self.data.pop(name, None)

    def get_id(self):
        return 10


class IntArray(Tag):
    def write(self, dataos):
        dataos.write_int(len(self.data))
        for x in self.data:
            dataos.write_int(x)

    def read(self, datais):
        self.data = []
        le = datais.read_int()
        for x in range(0, le):
            self.data.append(datais.read_int())

    def get_id(self):
        return 11

    def __str__(self):
        return "[" + str(len(self.data)) + " integers]"


class LongArray(Tag):
    def write(self, dataos):
        dataos.write_int(len(self.data))
        for x in self.data:
            dataos.write_long(x)

    def read(self, datais):
        self.data = []
        le = datais.read_int()
        for x in range(0, le):
            self.data.append(datais.read_long())

    def get_id(self):
        return 12

    def __str__(self):
        return "[" + str(len(self.data)) + " longs]"
