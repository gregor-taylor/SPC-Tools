import tkinter as tk
from tkinter.filedialog import askopenfilename
from spc_reader import SpcFile
from numpy import arange

def analyse_data_in_chunks(spcFileObject, chunksize, length_of_dwell): 
    for i in arange(0, length_of_dwell, chunksize):
        start_time=i
        stop_time=i+chunksize
        spcFileObject.create_shortened_histo_array((start_time,stop_time),save_data=True)

root=tk.Tk()
root.withdraw()
filename = askopenfilename(initialdir="C:\\", title="Choose an spc file")
spcF=SpcFile(filename)
#spcF.create_shortened_histo_array((4.75,5),save_data=True)
analyse_data_in_chunks(spcF, 2.5, 5)



