import ctypes
import os

# Load the DLL
current_path = os.getcwd()
os.add_dll_directory(current_path)
libconoft_dll = ctypes.CDLL('libconoft.dll')

# Call the add function
p = ctypes.pointer(ctypes.c_int(0))
result = libconoft_dll.RegisterAddFunc(p, 2, 3)
print(f"2 + 3 = {p.contents},{result}")
