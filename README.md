# madx-ptc-utils
Converts MAD-X sequences into callable python functions using the built in PTC functions in MAD-X.

Instructions
------------

First have a `.madx` file that contains a sequence and beam info you want to convert to python (mylattice.madx).

Run the command 
```
create-ptc-files path/to/mylattice.madx --ptc-order PTC_ORDER --ptc-dim PTC_DIM
```

A folder will be created in `./out` which contains the PTC data for the map.

From you python code have the import statement `from python_from_ptc import python_from_ptc`.

Pass the path of the PTC folder in `./out` to the function to get a callable python function.

PTC does not support all elements. Some of these elements can be removed without
affecting the PTC lattice. To comment them out use the `rm-keyword` command. For example
 if you wanted to remove quadrupoles from mylattice.madx

```
rm-keyword path/to/mylattice.madx quadrupole
```

Any number of keywords can be given after the filename.

Note
----
It is sometimes best to run the program in the directory of the lattice file if it contains calls to other files.

`create-ptc-files` only supports 4-D and 6-D lattices. 4-D supports up to a PTC order of 19 while 6-D supports up to PTC order 9.

`rm-keyword` will NOT discriminate elements that affect the PTC data, use carefully.
