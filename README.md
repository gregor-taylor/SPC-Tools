For working with .spc (and associated .set) files from Becker&Hickl photon counting cards.</br>
.spc files are time tagged photon data from imaging experiments where the photon events are stored in a pixel wise format with each pixel containing all of the photon events from that location.</br>
.set files contain the setup files and measurement info for the measurement.</br>
See Becker and Hickl handbook for file formats.</br>

<b>User Guide</b></br>
An example of use exists in 'SPC_test_script.py'.</br>
The spc_reader and set_reader can be used to read the .spc and .set files created when saving the time tagged data from photon counting imaging modes on Becker and Hickl SPC cards. Basic usage is as follows:</br>
- Import a file with SpcFile('filename'). If setFile is set to True (default) then it will ask you for the .set file. This is where the parameters such as TACRange, Gain etc are pulled from. It is possible to set setFile to False and provide the information manually (for example you've lost the .set file). The must be supplied as a parameter setup_values and be a list of the form [TACRange, TACGain, ADCResolution, ImageSizeX, ImageSizeY]. If neither a .set or setup list is provided then the program will abort with an error.</br>
- Once imported you can process the data as you wish. Basic functionality is to run 'create_histo_array' which will take each pixel and compute a histogram of photon counts for each one. If using some interactive Python processing can then be performed on the numpy array, or it can be saved as a .npy if the save_data flag is set to True. If data is saved it will be set to output_array[+number].npy in the directory the code is. The output is an n-pixel by n-pixel array with the element containing the histogram data from that particular pixel.</br>
- A further option is to take a shortened histogram. If, for example, the dwell time per pixel is 5 ms it is possible to only process a subset of that data. This is done by using the 'create_shortened_histo_array' with the argument time_range being provided as a tuple. If you wanted the data from 0 ms to 1 ms then you would provide the time_range (0,1). This will output a similar array as above but with the data for the histograms coming from the time_range specified. This is useful for simulating shorter dwell times etc.</br>

More functionality will be added as we go. All data is available from the processing; InvalidFlag, Mark, MTov, MacroTime, RoutingSignals, ADC and Gap so processing can be performed on all of that. It could be possible to store all of this in one giant array but for most applications and PCs you'll run into memory issues.

