## About this project
I am lazy, so it was boring to create a python reader for '.exe' files headers.
Thus, I decided to play with code generation and turn reader rules (files in the `formats` directory) into python code (files in the `out` directory).



## How to execute this program ?
* write the reader rules into a file
* run the main.py file: `python3 main.py <your reader>`. The output can be found in `out/<your reader>.py`
* run the generated file with the binary file you want to read: `python3 -i out/<your reader>.py <file to read>`, and play with it in the python REPL.



## Reader specifications
### Maps
Maps are mapping from an integer to an other integer or a string.
You can use them to show the fields in a human-readable way.

Here is an example of a map you can find in `formats/pe_file_format` :
```
map Machine where
    | 0x14c > "x86 (32 bits)"
    | 0x8664 > "amd64 (64 bits)"
end
```

### Bitflags
Bitflags are representing flags. This is close to the `IntFlag` class from the `enum` module, but it is not an `IntFlag`. It is something home-made.

Here is an example:
```
bitflag Characteristics where
    | 0x0001 > IMAGE_FILE_RELOCS_STRIPPED
    | 0x0002 > IMAGE_FILE_EXECUTABLE_IMAGE
    | 0x0004 > IMAGE_FILE_LINE_NUMS_STRIPPED
    [...]
end
```

### Readers
A reader is a kind of structure specifying the name of each field and the number of bytes to read for each fields. The `as` instruction is used to read the field in a more human-readable way than only hexadecimal.

Here is an example:
```
reader PE_IMAGE_HEADER where
    | signature: 4 as bytes
    | machine: 2 as Machine
    | section_numbers: 2
    | time_stamp: 4
    | useless: 8
    | optional_header_size: 2 as int
    | characteristics: 2 as Characteristics
end
```

### Read instructions
Once maps, bitflags and readers are declared, you have to write the read instructions.
For now, there are two read instructions:
* `READ <reader name>`: it reads the binary file following the reader instructions
* `GOTO <reader>.<field>`: it changes the virtual cursor to the specified localisation

Here is an example:
```
main {
    read IMAGE_DOS_HEADER
    goto IMAGE_DOS_HEADER.pe_header_address
    read PE_IMAGE_HEADER
    read PE_OPTIONAL_HEADER
    read WINDOWS_FIELDS
    read DATA_DIRECTORIES
}
```

## Example, in the python REPL
```sh
horus@horus:~$ python3 main.py formats/pe_file_format
horus@horus:~$ python3 -i out/pe_file_format.py test.exe
```
```py
>>> IMAGE_DOS_HEADER.magic_number
b'MZ'
>>> PE_IMAGE_HEADER.machine
x86 (32 bits)
>>> PE_IMAGE_HEADER.characteristics
IMAGE_FILE_EXECUTABLE_IMAGE | IMAGE_FILE_32BIT_MACHINE | IMAGE_FILE_REMOVABLE_RUN_FROM_SWAP | IMAGE_FILE_NET_RUN_FROM_SWAP
>>>
```