import tkinter as tk
from tkinter.filedialog import askopenfilename
import numpy as np
import matplotlib.pyplot as plt
from set_reader import SetFile

class SpcFile():
    def __init__(self, filename, setFile=True, setup_values=None):
        self.filename=filename
        if setFile==True:
            self.setFile_path=askopenfilename(initialdir="C:\\", title="Choose a .set file")
            if self.setFile_path == '' or self.setFile_path[-4:] != '.set':
                print('No .set file loaded! Choose one or provide a setup_dict')
            else:
                self.setFile=SetFile(self.setFile_path)
                self.TACRange=self.setFile.SP_data['TAC_R']
                self.TACGain=self.setFile.SP_data['TAC_G']
                self.ADCRe=self.setFile.SP_data['ADC_RE']
                self.ImageSizeX=self.setFile.SP_data['IMG_X']
                self.ImageSizeY=self.setFile.SP_data['IMG_Y']
        elif setFile==False and setup_values != None:
            self.TACRange=setup_values[0]
            self.TACGain=setup_values[1]
            self.ADCRe=setup_values[2]
            self.ImageSizeX=setup_values[3]
            self.ImageSizeY=setup_values[4]
        else:
            print('No setup parameters supplied. Cannot evaluate spc file.')

    def create_photon_array(self, save_data=False):
        #Shortcut to create photon data arrays
        #Tried this with large dataset and it just runs out of memory. So this might not be possible (at least on my laptop).
        #Better wat may be to specify what you want and have it spit out that i.e MacroTime and MicroTime etc.
        #Do not use at moment
        self.create_array(save_data=save_data, array_type='photon')

    def create_histo_array(self, save_data=False):
        #Shortcut to create histogram arrays
        self.create_array(save_data=save_data, array_type='hist')

    def create_array(self, save_data=False, array_type='hist'):
        root=tk.Tk()
        root.withdraw()
        with open(self.filename, "rb") as binary_file:
            #Header data for the .spc file
            macro_clock=(int.from_bytes(binary_file.read(3), 'little'))
            info_byte=int.from_bytes(binary_file.read(1), 'little')
            routing_bits=self.read_specific_bits(3,6,info_byte)
            invalid_data=self.read_single_bit(7, info_byte)
            #Make some data containers
            if array_type=='hist':
                PhotonTimeList=[]
            elif array_type == 'photon':
                PhotonDataList=[]
            data_start=False
            self.image_arr=np.ndarray((self.ImageSizeX, self.ImageSizeY), dtype='object')
            x_counter=0
            y_counter=0
            pos_direction=True
            #MacroTime counters
            MacroTimeOverflows=0
            MacroTime_val=0
            last_MT=0 

            #Read in file
            while True:
                byte_in = binary_file.read(4)
                if not byte_in:
                    break #EOF
                data_packet = self.decode_photon_packet(byte_in)
                if data_packet == False:
                    pass
                else:
                    ScanClk=data_packet[4]
                    if data_packet[0] == True: #Invalid flag
                        if data_packet[2]==True and data_packet[1]==False: #Checks it's definitely a MT Overflow count packet
                            MacroTimeOverflows += data_packet[3]
                    if ScanClk == "Frame/Line/Pixel":
                        #Start of scan
                        if data_start == False:
                            data_start=True
                        #End of scan
                        else:
                            if array_type=='hist':
                                PhotonTimes=np.asarray(PhotonTimeList, dtype='float')
                                self.image_arr[x_counter][y_counter]=self.construct_histogram(PhotonTimes, self.ADCRe, plotting=False)
                                break
                            elif array_type=='photon':
                                self.image_arr[x_counter][y_counter]=np.asarray(PhotonDataList, dtype=('f,f,?'))
                                break
                    elif ScanClk =="Pixel":
                        #For each pixel in a line
                        if array_type=='hist':
                            PhotonTimes=np.asarray(PhotonTimeList, dtype='float')
                            self.image_arr[x_counter][y_counter]=self.construct_histogram(PhotonTimes, self.ADCRe, plotting=False)
                        elif array_type=='photon':
                            self.image_arr[x_counter][y_counter]=np.asarray(PhotonDataList, dtype=('f,f,?'))
                        if pos_direction == True:
                            x_counter+=1
                        else:
                            x_counter-=1
                        PhotonTimeList = []
                    elif ScanClk =="Line/Pixel":
                        #Last pixel of the line and a new line starts
                        if array_type=='hist':
                            PhotonTimes=np.asarray(PhotonTimeList, dtype='float')
                            self.image_arr[x_counter][y_counter]=self.construct_histogram(PhotonTimes, self.ADCRe, plotting=False)
                        elif array_type=='photon':
                            self.image_arr[x_counter][y_counter]=np.asarray(PhotonDataList, dtype=('f,f,?'))
                        y_counter+=1
                        pos_direction = not pos_direction
                        PhotonTimeList = []
                    elif ScanClk == "Pixel/Frame" or data_packet =="Frame" or data_packet =="Line":
                        #TO DO: Not used at moment. Will do logic for these later
                        break
                    elif data_packet[0] == False: #Final check on validity of photon
                        if data_start == True:
                            #MicroTime
                            MicroTime_val=self.MicroTime(data_packet[5], self.TACRange, self.TACGain) 
                            if array_type =='photon':
                                #MacroTime
                                if data_packet[2] == False: #For when there has been no overflow
                                    MacroTime_val=(MacroTime_val+data_packet[3]-last_MT)
                                    last_MT=data_packet[3]
                                elif data_packet[2] == True: #Mtov bit. 
                                    MacroTime_val=MacroTime_val+(data_packet[3]+(2**12-last_MT))
                                    last_MT=data_packet[3]
                                #Checks the buffer for overflows and adds them if neccessary
                                if MacroTimeOverflows != 0:
                                    MacroTime_val+=(2**12*MacroTimeOverflows)
                                    MacroTimeOverflows=0
                                PhotonDataList.append(((MacroTime_val*macro_clock), MicroTime_val, data_packet[6]))#returns macro, micro and gap flag.
                            if array_type=='hist':
                                PhotonTimeList.append(MicroTime_val)
                        else:
                            pass   
                if save_data==True:
                    np.save('output_array.npy', self.image_arr)    

    def read_specific_bits(self, bit_start, bit_stop, input_val):
        bit_mask=[0,0,0,0,0,0,0,0]
        for i in range(bit_start, bit_stop+1):
            bit_mask[-(i+1)] = 1
        bit_mask=int('0b'+''.join(str(v) for v in bit_mask), 2) #maybe better to do this with bitshifting but not doing it much for this anyway
        #mask and shift
        return (input_val&bit_mask) >> bit_start    

    def read_single_bit(self, bit_id, input_val):
        if type(input_val) == bytes:
            input_val=int.from_bytes(input_val, 'little')
            value=(input_val&(1<<bit_id))!=0
        else:
            value=(input_val&(1<<bit_id))!=0
        return value    

    def decode_photon_packet(self, packet):
        #define routing dict
        routing_sigs={
            7:"Frame/Line/Pixel",
            5:"Pixel/Frame",
            4:"Frame",
            3:"Line/Pixel",
            2:"Line",
            1:"Pixel",
            0:"None"
        }
        #Invalid is Byte 3, bit 8
        Invalid=self.read_single_bit(7,packet[3])
        #MTov (MacroTime overflow) is Byte 3, bit 7. If set then data packet is the number of overflows which have occurred.
        MTOv=self.read_single_bit(6,packet[3])
        #Mark is Byte 3, bit 5
        Mark=self.read_single_bit(4,packet[3])
        #Reads the Invalid data bit. Checks if it's a MacroOverflow packet or a Signal (Frame/Line/Pixel). If it's not, ignores the packets as invalid.
        if Invalid == True:
            if MTOv == False and Mark == False:
                return False
            else:
                if MTOv == True:
                    #This entry is punted out if the MacroClock has overflowed since the last photon. The Count is the number of overflows
                    OverflowCount=((packet[3]&0x0F)<<24)+(packet[2]<<16)+(packet[1]<<8)+packet[0]
                else:
                    OverflowCount=None          
                if Mark==True:
                    #RoutingSignals are top nibble of Byte 1.
                    RoutingSig=self.read_specific_bits(4, 7, packet[1])
                else:
                    RoutingSig=0
                return (Invalid, Mark, MTOv, OverflowCount, routing_sigs[RoutingSig])      
        else:
            #Returns the valid photon data
            #MacroTime is Byte 0 and bottom nibble of Byte 1. Endianess is little.
            #bin_str='0b'+((format(packet[1], '08b')[-4:])+format(packet[0], '08b')) OLD - Left for future use
            MacroTime=((packet[1]&0x0F)<<8)+packet[0]
            #RoutingSignals are top nibble of Byte 1.
            RoutingSig=self.read_specific_bits(4, 7, packet[1])
            #ADC is Byte 2 and bottom nibble of Byte 3
            ADC=((packet[3]&0x0F)<<8)+packet[2]
            #Gap is Byte 3, bit 6
            Gap=self.read_single_bit(5,packet[3])  
            photon_data=(Invalid, Mark, MTOv, MacroTime, routing_sigs[RoutingSig], ADC, Gap)
            return photon_data    

    def MicroTime(self, ADC, TACRange, TACGain):
        return ((4095-ADC)*TACRange)/(TACGain*4096)    

    def construct_histogram(self, MicroTimes, bin_number, plotting=False):
        hist=np.histogram(MicroTimes, bins=bin_number, range=(0,(self.TACRange/self.TACGain)))
        if plotting == True:
            plt.hist(MicroTimes,bins=bin_number, range=(0,(self.TACRange/self.TACGain)))
            plt.show()
        return hist


#For testing
#root=tk.Tk()
#root.withdraw()
#filename = askopenfilename(initialdir="C:\\", title="Choose an spc file")
#spcF=SpcFile(filename)


