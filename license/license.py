

import ctypes
import os


file_path = os.path.join(os.getcwd(), "visionai.dll")

mylib = ctypes.CDLL(file_path)

##argument
mylib.initialize.argtypes = [ctypes.c_int, ctypes.c_int]
mylib.validateLicense.argtypes = [ctypes.c_char_p]
mylib.getLicenseData.argtypes = None
mylib.getError.argtypes = None

##return
mylib.initialize.restype = ctypes.c_int
mylib.validateLicense.restype = ctypes.c_int
mylib.getLicenseData.restype = ctypes.c_char_p
mylib.getError.restype = ctypes.c_char_p

#Input
license_key = "5926CD16-FDA93E20-D3E1DE54-ED88F0D6-1861F43F-3329A888-E86796A5-E05E9A0E"
module=8
customer_id=12345

##Execute
ret = mylib.initialize(module,customer_id)
#print("Return1 :"+str(ret))
ret = mylib.validateLicense(license_key.encode('utf-8'))
print("Return2 :"+str(ret))
if(ret ==1):
    val = mylib.getLicenseData()
    print(val)
else:
    print("License is invalid")
    print("Error: "+str(mylib.getError()))    
