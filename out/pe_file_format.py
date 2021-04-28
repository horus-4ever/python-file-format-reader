
import sys

FILE = sys.argv[1]
reader = open(FILE, "rb")


def _runtime_lookup(name):
    try:
        return _func_wrapper(getattr(MAPS, name).__getitem__)
    except AttributeError:
        pass
    try:
        return _func_wrapper(getattr(BITFLAGS, name).get)
    except AttributeError:
        print(f"No such map or bitflag {name}")
        sys.exit(0)


def _func_wrapper(func):
    def inner_wrapper(self, *args, **kwargs):
        return func(*args, **kwargs)
    return inner_wrapper

_int = _func_wrapper(int)
_hex = _func_wrapper(hex)
_bin = _func_wrapper(bin)


def _to_bytes(rule, value):
    return int.to_bytes(value, rule.to_read, "little")

def _str(rule, value):
    return _to_bytes(rule, value).decode("ascii")


class Symbol:
    __symbols__ = {}
    def __new__(cls, value):
        if value in cls.__symbols__:
            return cls.__symbols__[value]
        obj = object.__new__(cls)
        cls.__symbols__[value] = obj
        return obj
    def __init__(self, value):
        self.value = value
    def __repr__(self):
        return self.value
    def __eq__(self, other):
        return self is other


class Flag:
    def __init__(self, number, *symbols):
        self.number = number
        self.symbols = symbols
    def __or__(self, other):
        return Flag(self.number | other.number, *self.symbols, *other.symbols)
    def __int__(self):
        return self.number
    def __repr__(self):
        return " | ".join(str(symbol) for symbol in self.symbols)


class Bitflag:
    def __init_subclass__(cls):
        cls.__members__ = [item[0] for item in vars(cls).items() if isinstance(item[1], Flag)]
    @classmethod
    def get(cls, value):
        result = None
        for member in cls.__members__:
            flag = getattr(cls, member)
            if int(flag) & value != 0:
                result = flag if result is None else result | flag
        return result


class Attribute:
    def __init__(self, value, changed_value):
        self.value = value
        self.changed_value = changed_value

    def __int__(self):
        return self.value

    def __repr__(self):
        return str(self.changed_value)


class ReaderRule:
    def __init__(self, to_read, as_rule):
        self.to_read = to_read
        self.as_rule = as_rule
        self.name = None

    def __get__(self, instance, owner):
        if instance is not None:
            value = getattr(instance, self.name)
            return Attribute(value, self.as_rule(self, value))
        else:
            return self

    def __set_name__(self, cls, name):
        self.name = f"_{name}"


class Reader:
    def __init_subclass__(cls):
        cls.__members__ = [item[0] for item in vars(cls).items() if isinstance(item[1], ReaderRule)]

    @classmethod
    def read(cls, stream):
        reader = cls()
        for name in cls.__members__:
            new_name = f"_{name}"
            to_read = getattr(cls, name).to_read
            value = int.from_bytes(stream.read(to_read), "little")
            setattr(reader, new_name, value)
        return reader


class MAPS:
    Machine = {332: 'x86 (32 bits)', 34404: 'amd64 (64 bits)'}
    Subsystem = {0: 'IMAGE_SUBSYSTEM_UNKNOWN (0)', 1: 'IMAGE_SUBSYSTEM_NATIVE (1)', 2: 'IMAGE_SUBSYSTEM_WINDOWS_GUI (2)', 3: 'IMAGE_SUBSYSTEM_WINDOWS_CUI (3)'}

class BITFLAGS:
    class Characteristics(Bitflag):
      IMAGE_FILE_RELOCS_STRIPPED = Flag(1, "IMAGE_FILE_RELOCS_STRIPPED")
      IMAGE_FILE_EXECUTABLE_IMAGE = Flag(2, "IMAGE_FILE_EXECUTABLE_IMAGE")
      IMAGE_FILE_LINE_NUMS_STRIPPED = Flag(4, "IMAGE_FILE_LINE_NUMS_STRIPPED")
      IMAGE_FILE_LOCAL_SYMS_STRIPPED = Flag(8, "IMAGE_FILE_LOCAL_SYMS_STRIPPED")
      IMAGE_FILE_AGGRESSIVE_WS_TRIM = Flag(16, "IMAGE_FILE_AGGRESSIVE_WS_TRIM")
      IMAGE_FILE_LARGE_ADDRESS_AWARE = Flag(32, "IMAGE_FILE_LARGE_ADDRESS_AWARE")
      IMAGE_FILE_BYTES_REVERSED_LO = Flag(128, "IMAGE_FILE_BYTES_REVERSED_LO")
      IMAGE_FILE_32BIT_MACHINE = Flag(256, "IMAGE_FILE_32BIT_MACHINE")
      IMAGE_FILE_DEBUG_STRIPPED = Flag(512, "IMAGE_FILE_DEBUG_STRIPPED")
      IMAGE_FILE_REMOVABLE_RUN_FROM_SWAP = Flag(1024, "IMAGE_FILE_REMOVABLE_RUN_FROM_SWAP")
      IMAGE_FILE_NET_RUN_FROM_SWAP = Flag(2048, "IMAGE_FILE_NET_RUN_FROM_SWAP")
      IMAGE_FILE_SYSTEM = Flag(4096, "IMAGE_FILE_SYSTEM")
      IMAGE_FILE_DLL = Flag(8192, "IMAGE_FILE_DLL")
      IMAGE_FILE_UP_SYSTEM_ONLY = Flag(16384, "IMAGE_FILE_UP_SYSTEM_ONLY")
      IMAGE_FILE_BYTES_REVERSED_HI = Flag(32768, "IMAGE_FILE_BYTES_REVERSED_HI")
    class DllCharacteristics(Bitflag):
      IMAGE_DLLCHARACTERISTICS_HIGH_ENTROPY_VA = Flag(32, "IMAGE_DLLCHARACTERISTICS_HIGH_ENTROPY_VA")
      IMAGE_DLLCHARACTERISTICS_DYNAMIC_BASE = Flag(64, "IMAGE_DLLCHARACTERISTICS_DYNAMIC_BASE")
      IMAGE_DLLCHARACTERISTICS_FORCE_INTEGRITY = Flag(128, "IMAGE_DLLCHARACTERISTICS_FORCE_INTEGRITY")
      IMAGE_DLLCHARACTERISTICS_NX_COMPAT = Flag(256, "IMAGE_DLLCHARACTERISTICS_NX_COMPAT")
      IMAGE_DLLCHARACTERISTICS_NO_ISOLATION = Flag(512, "IMAGE_DLLCHARACTERISTICS_NO_ISOLATION")
      IMAGE_DLLCHARACTERISTICS_NO_SEH = Flag(1024, "IMAGE_DLLCHARACTERISTICS_NO_SEH")
      IMAGE_DLLCHARACTERISTICS_NO_BIND = Flag(2048, "IMAGE_DLLCHARACTERISTICS_NO_BIND")
      IMAGE_DLLCHARACTERISTICS_APPCONTAINER = Flag(4096, "IMAGE_DLLCHARACTERISTICS_APPCONTAINER")
      IMAGE_DLLCHARACTERISTICS_WDM_DRIVER = Flag(8192, "IMAGE_DLLCHARACTERISTICS_WDM_DRIVER")
      IMAGE_DLLCHARACTERISTICS_GUARD_CF = Flag(16384, "IMAGE_DLLCHARACTERISTICS_GUARD_CF")
      IMAGE_DLLCHARACTERISTICS_TERMINAL_SERVER_AWARE = Flag(32768, "IMAGE_DLLCHARACTERISTICS_TERMINAL_SERVER_AWARE")

class READERS:
    class IMAGE_DOS_HEADER(Reader):
        magic_number = ReaderRule(2, _to_bytes)
        useless = ReaderRule(58, _hex)
        pe_header_address = ReaderRule(4, _hex)
    class PE_IMAGE_HEADER(Reader):
        signature = ReaderRule(4, _to_bytes)
        machine = ReaderRule(2, _runtime_lookup('Machine'))
        section_numbers = ReaderRule(2, _hex)
        time_stamp = ReaderRule(4, _hex)
        useless = ReaderRule(8, _hex)
        optional_header_size = ReaderRule(2, _int)
        characteristics = ReaderRule(2, _runtime_lookup('Characteristics'))
    class PE_OPTIONAL_HEADER(Reader):
        magic_number = ReaderRule(2, _to_bytes)
        major_linker_version = ReaderRule(1, _hex)
        minor_linker_version = ReaderRule(1, _hex)
        total_size = ReaderRule(4, _hex)
        data_section_size = ReaderRule(4, _hex)
        bss_section_size = ReaderRule(4, _hex)
        entry_point_address = ReaderRule(4, _hex)
        base_of_code = ReaderRule(4, _hex)
        base_of_data = ReaderRule(4, _hex)
    class WINDOWS_FIELDS(Reader):
        image_base = ReaderRule(4, _hex)
        section_alignement = ReaderRule(4, _hex)
        file_alignement = ReaderRule(4, _hex)
        major_os_version = ReaderRule(2, _hex)
        minor_os_version = ReaderRule(2, _hex)
        major_image_version = ReaderRule(2, _hex)
        minor_image_version = ReaderRule(2, _hex)
        major_subsystem_version = ReaderRule(2, _hex)
        minor_subsystem_version = ReaderRule(2, _hex)
        win_version_value = ReaderRule(4, _hex)
        image_size = ReaderRule(4, _hex)
        headers_size = ReaderRule(4, _hex)
        checksum = ReaderRule(4, _hex)
        subsystem = ReaderRule(2, _runtime_lookup('Subsystem'))
        dll_characeristics = ReaderRule(2, _runtime_lookup('DllCharacteristics'))
        stack_reserve_size = ReaderRule(4, _hex)
        stack_commit_size = ReaderRule(4, _hex)
        heap_reserve_size = ReaderRule(4, _hex)
        heap_commit_size = ReaderRule(4, _hex)
        loader_flags = ReaderRule(4, _hex)
        number_of_rva_and_sizes = ReaderRule(4, _hex)
    class DATA_DIRECTORIES(Reader):
        export_table = ReaderRule(4, _hex)
        export_table_size = ReaderRule(4, _hex)
        import_table = ReaderRule(4, _hex)
        import_table_size = ReaderRule(4, _hex)
        ressource_table = ReaderRule(4, _hex)
        ressource_table_size = ReaderRule(4, _hex)
        exception_table = ReaderRule(4, _hex)
        exception_table_size = ReaderRule(4, _hex)
        certificate_table = ReaderRule(4, _hex)
        certificate_table_size = ReaderRule(4, _hex)
        base_relocation_table = ReaderRule(4, _hex)
        base_relocation_table_size = ReaderRule(4, _hex)
        debug = ReaderRule(4, _hex)
        debug_size = ReaderRule(4, _hex)
        architecture_data = ReaderRule(4, _hex)
        architecture_data_size = ReaderRule(4, _hex)
        global_ptr = ReaderRule(4, _hex)
        useless_one = ReaderRule(4, _hex)
        tls_table = ReaderRule(4, _hex)
        tls_table_size = ReaderRule(4, _hex)


IMAGE_DOS_HEADER = getattr(READERS, 'IMAGE_DOS_HEADER').read(reader)
reader.seek(int(IMAGE_DOS_HEADER.pe_header_address), 0)
PE_IMAGE_HEADER = getattr(READERS, 'PE_IMAGE_HEADER').read(reader)
PE_OPTIONAL_HEADER = getattr(READERS, 'PE_OPTIONAL_HEADER').read(reader)
WINDOWS_FIELDS = getattr(READERS, 'WINDOWS_FIELDS').read(reader)
DATA_DIRECTORIES = getattr(READERS, 'DATA_DIRECTORIES').read(reader)