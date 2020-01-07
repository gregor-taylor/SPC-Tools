import numpy as np

class SetFile():
    def __init__(self, filename):
        self.read_set_file(filename)

    def read_set_file(self, file):
        #define header parameters
        FILE_HEADER = [
        ('revision', 'i2'),
        ('info_offset', 'i4'),
        ('info_length', 'i2'),
        ('setup_offs', 'i4'),
        ('setup_length', 'i2'),
        ('data_block_offset', 'i4'),
        ('no_of_data_blocks', 'i2'),
        ('data_block_length', 'i4'),
        ('meas_desc_block_offset', 'i4'),
        ('no_of_meas_desc_blocks', 'i2'),
        ('meas_desc_block_length', 'i2'),
        ('header_valid', 'u2'),
        ('reserved1', 'u4'),
        ('reserved2', 'u2'),
        ('chksum', 'u2')]    

        with open(file, 'rb') as fileHandle:
            #Read header
            self.FileHeader=np.rec.fromfile(fileHandle, dtype=FILE_HEADER, shape=1, byteorder='<')[0]
            #Read file info
            fileHandle.seek(self.FileHeader.info_offset)
            self.FileInfo=(fileHandle.read(self.FileHeader.info_length)).decode('ascii').replace("\r\n", "\n")
            #Read setup
            fileHandle.seek(self.FileHeader.setup_offs)
            SetupInfoBlock=(fileHandle.read(self.FileHeader.setup_length))
            bin_begin_id=SetupInfoBlock.find(b'BIN_PARA_BEGIN')
            SetupInfo_ascii=SetupInfoBlock[:bin_begin_id].decode('ascii').replace("\r\n", "\n")
            self.PR_data, self.SP_data, self.DI_data, self.WI_data = self.parse_BlockInfo_ascii(SetupInfo_ascii) #This seperates the data into the PR/SP/DI/WI.
            self.SetupInfo_bin=SetupInfoBlock[bin_begin_id:] #This is the binary data. Mostly not needed I don't think but punt it out anyway.

    def parse_BlockInfo_ascii(self, ascii_block):
    	#Splits into PR, SP, DI and WI parameters
    	PR_data={}
    	SP_data={}
    	DI_data={}
    	WI_data=[]
    	for line in ascii_block.splitlines():
    		if line[:5]=='  #PR':
    			data_line=(line.split()[1][1:-1].split(','))
    			value=self.convert_value(data_line)
    			key=data_line[0][3:]
    			PR_data[key]=value
    		if line[:5]=='  #SP':
    			data_line=(line.split()[1][1:-1].split(','))
    			value=self.convert_value(data_line)
    			key=data_line[0][3:]
    			SP_data[key]=value
    		if line[:5]=='  #DI':
    			data_line=(line.split()[1][1:-1].split(','))
    			value=self.convert_value(data_line)
    			key=data_line[0][3:]
    			DI_data[key]=value
    		if line[:5]=='  #WI':
    			WI_data.append(line)

    	return(PR_data, SP_data, DI_data, WI_data)
    			
    def convert_value(self, data_line):
    	if data_line[1] == 'I' or data_line[1] == 'U' or data_line[1] == 'L':
    			value=int(data_line[2])
    	elif data_line[1] == 'B':
    		if data_line[2]=='1':
    			value=True
    		elif data_line[2]=='0':
    			value=False
    	elif data_line[1] == 'F':
    		value=float(data_line[2])
    	elif data_line[1] == 'S' or data_line[1] == 'C':
    		value=data_line[2]
    	return value
