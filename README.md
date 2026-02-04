# kreslotron-jankestyczny

chart drawing program

This program requires a data file and a config file to work properly
standard data:
Data file should have a header on the first line and data in following written like that: value1;value2;value3...
semicolon is also interchangable with a comma. Every type of file can be used as a data file, but you can filter only
text files (.txt, .TXT, .Txt) or csv files (.csv, .CSV, .Csv).
Config file needs to be named as follows "config{whatever name you want to give it}.txt". The file should we written
in a specific format, every line corresponds to one collumn in the data file and it should look like this: {name of collumn};{unit};{type of fir filter (0-4)}. One collumn needs to be named Time for program to work
binary data:
Data file doesnt have a header and should consist of time written as a 32-bit number and one value written as a 24-bit number with 8 bits of padding.
Config file must have word "bin" in the first line, time in second and value in third, values should follow the same format as with normal data.

how to use:
1. select a data file
2. select a proper config file
3. wait for data to load
4. select which values graph you want to draw
5. set the time boundaries (min-max if left empty)
6. set gain and offset (1 and 0 default)
7. set name to the file (wykres_{unix time} by default, if value is set to be filtered it will generate 2 files, marking unfiltered as unf and filtered as fil)
8. draw a graph
9. if you close the graph window you can change the settings and draw again, but if you dont change the name your old files will be overwritten (unless the name is default)

error codes and possible fixes:
error 1 - not enough collumns in data file, check the data file for empty or faulty lines, check config file, you can try removing lines from config file
error 2 - data or config files opening error, mostly happens when you cancel selecting a file
error 3 - Time collumn error, check if config has Time collumn written correctly
error 4 - first line of Time has bigger value than the last, check if files have matching Time collumn or if data file is correct
error 5 - wrong config file format
error 6 - a collumn that is used by program is empty, so it cant be converted into a number

fir parameters:
0 - no filter
1 - numtaps = 0.4*f + 1, cutoff = 8, made for fast changing values like IMU
2 - numtaps = 2*f + 1, cutoff = 2, slower, but still fast changing values like pressure
3 - numtaps = 5*f + 1, cutoff = 0.2, slow changing values like temperature
4 - numtaps = 10*f + 1, cutoff = 0.04, very slow changing values like battery voltage

f - sampling frequency
WARNING!!!
if data file has a "hole" in it (it doesnt have data from part of the measured time) fir filter will be deformed, potentially filtering data