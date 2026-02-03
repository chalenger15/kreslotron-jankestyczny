import os
import pandas as pd
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import filedialog, messagebox
from scipy.signal import lfilter, firwin
import time
import numpy as np
import struct

def split(line): #dzieli string na liste oddzieloną średnikiem
    result = line.rstrip().split(';')
    try:
        result[1] == 0
    except IndexError:
        result = line.rstrip().split(',')
    if result[0] != '':
        return result
    else:
        return "empty"


def locate_var(list, var): #sprawdza obecność wartości w liście i zwraca jej indeks jeśli ją znajdzie, jeśli nie zwraca -1
    index = 0
    for elem in list:
        if elem == var:
            return index
        else:
            index += 1
    return -1


def dir_check(name): #sprawdza czy dany folder istnieje, jeśli nie tworzy go
    if not os.path.exists(name):
        os.mkdir(name)


def hex_to_splitdec(data, var):
    if len(data) < 8:
        print("empty")
        return "empty"
    time, b0, b1, b2, unused = struct.unpack('<I3B1B', data)
    thrust = (b0 << 16) | (b1 << 8) | b2
    val_list = {var[0]:[time], var[1]:[thrust]}
    df = pd.DataFrame(val_list)
    return(df)


def data_frame_init(file_name, config_file_name): #tworzy dataframe, listy jednostek i nazw kolumn z podanego pliku danych i konfiguracyjnego
    mode = 0
    if os.path.isfile(config_file_name):
        c = open(config_file_name)
        axis_titles = c.readline()
        if os.path.isfile(file_name) and axis_titles != "bin\n":
            f = open(file_name)
            mode = 1
        elif os.path.isfile(file_name):
            f = open(file_name, 'rb')
            mode = 2
    if mode == 1:
        f.readline()
        units = []
        var_list = []
        filter_bool = []
        axis_titles = split(axis_titles)
        while axis_titles != "empty":
            var_list.append(axis_titles[0])
            units.append(axis_titles[1])
            filter_bool.append(axis_titles[2])
            axis_titles = c.readline()
            axis_titles = split(axis_titles)
        data = f.readline()
        data = split(data)
        list_dics = []
        inter = len(var_list)
        while data != "empty":
            dic = {}
            if len(data) < len(var_list):
                print(data)
                print(len(data))
                messagebox.showerror("Błąd 1", "Błędny plik konfiguracyjny lub danych, zamykanie programu")
                quit()
            for i in range (inter):
                dic[var_list[i]] = float(data[i])
            list_dics.append(dic)
            data = f.readline()
            data = split(data)
        df = pd.DataFrame(list_dics)
        return df, units, var_list, filter_bool

    elif mode == 2:
        units = []
        var_list = []
        filter_bool = []
        time_list = []
        thrust_list = []
        axis_titles = c.readline()
        axis_titles = split(axis_titles)
        while axis_titles != "empty":
            var_list.append(axis_titles[0])
            units.append(axis_titles[1])
            filter_bool.append(axis_titles[2])
            axis_titles = c.readline()
            axis_titles = split(axis_titles)
        data = f.read(8)
        dic = hex_to_splitdec(data, var_list)
        stop = 0
        while stop == 0:
            if len(data) < 8:
                stop = 1
                break
            time, b0, b1, b2, unused = struct.unpack('<I3B1B', data)
            thrust = (b0 << 16) | (b1 << 8) | b2
            time_list.append(time)
            thrust_list.append(thrust)
            data = f.read(8)
        time_array = np.array(time_list, dtype=np.uint32)
        thrust_array = np.array(thrust_list, dtype=np.uint32)
        signed_thrust_array = thrust_array.copy()
        mask = 0x800000  # bit 23
        signed_thrust_array[signed_thrust_array & mask != 0] |= 0xFF000000
        signed_thrust_array = signed_thrust_array.view(np.int32)
        df = pd.DataFrame({var_list[0]:time_array, var_list[1]:signed_thrust_array})
        return df, units, var_list, filter_bool
    else:
        messagebox.showerror("Błąd 2", "Błąd wczytywania pliku, zamykanie programu")
        quit()
    
#rysuje wykres
def plot(df, units, axis_titles, value_to_print, gain, offset, name):
    index = locate_var(axis_titles, value_to_print)
    df[value_to_print] = df[value_to_print]*gain + offset
    plt.figure(figsize=(12,6))
    plt.plot('Time', value_to_print, data = df)
    plt.xlabel(f"Time(ms)")
    plt.ylabel(f"{value_to_print}({units[index]})")
    plt.title(f"wykres {value_to_print} w czasie [{units[index]}(ms)]")
    plt.grid()
    dir_check('wykresy')
    if name == '':
        plt.savefig(f'wykresy/wykres_{round(time.time())}.png')
    else:
        plt.savefig(f'wykresy/{name}')
    plt.show()

#rysuje 2 wykresy: z filtrem fir i bez
def plot_with_filter(df, units, axis_titles, value_to_print, gain, offset, name, filter_var):
    fs_const = round(1000/((df.at[len(df)-1, 'Time'] - df.at[0, 'Time'])/len(df)))
    index = locate_var(axis_titles, value_to_print)
    #df[value_to_print] = df[value_to_print]*gain + offset
    if filter_var == 1:
        fir = firwin(numtaps = round(0.4 * fs_const) + 1, cutoff = 8, fs = fs_const)
        #opóźnienie około 0.2s
    elif filter_var == 2:
        fir = firwin(numtaps = 2 * fs_const + 1, cutoff = 2, fs = fs_const)
        #opóźnienie około 1s
    elif filter_var == 3:
        fir = firwin(numtaps = 5 * fs_const + 1, cutoff = 0.2, fs = fs_const)
        #opóźnienie około 2.5s
    else:
        fir = firwin(numtaps = 10 * fs_const + 1, cutoff = 0.04, fs = fs_const)
        #opóźnienie około 5s
    filtered = lfilter(fir, [1], df[value_to_print])
    df[value_to_print] = df[value_to_print]*gain + offset
    filtered = filtered*gain + offset
    plt.figure(figsize=(12,6))
    plt.plot('Time', value_to_print, data = df)
    plt.xlabel(f"Time(ms)")
    plt.ylabel(f"{value_to_print}({units[index]})")
    plt.title(f"wykres {value_to_print} w czasie [{units[index]}(ms)], nieprzefiltrowany")
    plt.grid()
    dir_check('wykresy')
    if name == '':
        plt.savefig(f'wykresy/unf_wykres_{round(time.time())}.png')
    else:
        plt.savefig(f'wykresy/unf_{name}')
    plt.close()
    plt.figure(figsize=(12,6))
    plt.plot(df['Time'], filtered)
    plt.xlabel(f"Time(ms)")
    plt.ylabel(f"{value_to_print}({units[index]})")
    plt.title(f"wykres {value_to_print} w czasie [{units[index]}(ms)], przefiltrowany")
    plt.grid()
    if name == '':
        plt.savefig(f'wykresy/fil_wykres_{round(time.time())}.png')
    else:
        plt.savefig(f'wykresy/fil_{name}')
    plt.close()
    plt.figure(figsize=(12,6))
    plt.subplot(1,2,1)
    plt.plot('Time', value_to_print, data = df)
    plt.xlabel(f"Time(ms)")
    plt.ylabel(f"{value_to_print}({units[index]})")
    plt.title(f"wykres {value_to_print} w czasie [{units[index]}(ms)], nieprzefiltrowany")
    plt.grid()
    plt.subplot(1,2,2)
    plt.plot(df['Time'], filtered)
    plt.xlabel(f"Time(ms)")
    plt.ylabel(f"{value_to_print}({units[index]})")
    plt.title(f"wykres {value_to_print} w czasie [{units[index]}(ms)], przefiltrowany")
    plt.grid()
    plt.show()

def value_check(value, axis_titles): #sprawdza czy wartość jest w liście
    var = locate_var(axis_titles, value)
    if var>=0:
        return 1
    else:
        return 0

###sprawdza czy dana jest intem lub floatem###

def is_int(value):
    return value.isdigit()

def is_float(value):
    try:
        float(value)
        return True
    except ValueError:
        return False

#############################################

def time_to_index(time_val, time): #zmienia podany czas na indeks z listy
    index = 0
    while float(time_val) > time[index]:
        index +=1
        if len(time) == index+1:
            return index
    return index
    

class GUI:
    def __init__(self, file_name, config_file_name):
        self.root = tk.Tk()
        self.root.title("kreslotron jankestyczny")
        self.root.geometry("350x275")
        self.wybor = tk.StringVar()
        self.df, self.units, self.axis_titles, self.filter_var = data_frame_init(file_name, config_file_name)
        try:
            self.time_min_limit = self.df['Time'][0]
            self.time_max_limit = self.df['Time'][len(self.df)-1]
            if self.time_max_limit < self.time_min_limit:
                messagebox.showerror("Błąd 3", "Możliwy błędny plik danych, zamykanie programu")
                quit()
        except(KeyError):
            messagebox.showerror("Błąd 4", "Błąd wczytywania danych, zamykanie programu")
            quit()
        self.wybor.set(self.axis_titles[0])
        self.plot = tk.Button(self.root, text='rysuj', command=self.plot)
        self.choice = tk.OptionMenu(self.root, self.wybor, *self.axis_titles)
        self.choice.place(x=170, y=10)
        self.plot.place(x=150, y=220)
        self.gain = tk.Entry(self.root, width=10, font=('Arial', 10))
        self.gain.place(x=40,y=25)
        self.offset = tk.Entry(self.root, width=10, font=('Arial', 10))
        self.offset.place(x=40,y=75)
        self.time_min = tk.Entry(self.root, width=12, font=('Arial', 10))
        self.time_min.place(x=45,y=125)
        self.time_max = tk.Entry(self.root, width=12, font=('Arial', 10))
        self.time_max.place(x=200,y=125)
        self.picture_name = tk.Entry(self.root, width=30, font=('Arial', 10))
        self.picture_name.place(x=50, y=185)
        self.label_time = tk.Label(self.root, text=f'zakres czasu (od {self.time_min_limit}ms do {self.time_max_limit}ms)', font=('Arial', 10))
        self.label_name = tk.Label(self.root, text='wpisz nazwę pliku do którego będzie zapisany wykres', font=('Arial', 10))
        self.label_gain = tk.Label(self.root, text='gain', font=('Arial', 10))
        self.label_offset = tk.Label(self.root, text='offset', font=('Arial', 10))
        self.label_gain.place(x=60, y=0)
        self.label_offset.place(x=60, y=50)
        self.label_time.place(x=40, y=100)
        self.label_name.place(x=10, y=160)
        self.root.mainloop()
    def plot(self):
        if self.time_min.get() != '' and (is_int(self.time_min.get()) or is_float(self.time_min.get())):
            self.time_min_val = time_to_index(self.time_min.get(), self.df['Time'])
        else:
            self.time_min_val = 0
        if self.time_max.get() != '' and (is_int(self.time_max.get()) or is_float(self.time_max.get())):
            self.time_max_val = time_to_index(self.time_max.get(), self.df['Time']) 
        else:
            self.time_max_val = len(self.df)  
        if self.gain.get() != '' and (is_int(self.gain.get()) or is_float(self.gain.get())):
            self.gain_val=float(self.gain.get())
        else:
            self.gain_val=1
        if self.offset.get() != '' and (is_int(self.offset.get()) or is_float(self.offset.get())):
            self.offset_val=float(self.offset.get())
        else:
            self.offset_val=0
        if value_check(self.wybor.get(), self.axis_titles):
            if int(self.filter_var[locate_var(self.axis_titles, self.wybor.get())]) != 0:
                plot_with_filter(self.df.iloc[self.time_min_val:self.time_max_val+1], self.units, self.axis_titles, self.wybor.get(), self.gain_val, self.offset_val, self.picture_name.get(), int(self.filter_var[locate_var(self.axis_titles, self.wybor.get())]))
            else:
                plot(self.df[self.time_min_val:self.time_max_val+1], self.units, self.axis_titles, self.wybor.get(), self.gain_val, self.offset_val, self.picture_name.get())
        else:
            print("brak danej wartosci")
        self.time_assigned = 0


file = filedialog.askopenfilename(title="wybierz plik z danymi", filetypes=[("wszystkie pliki", "*.*"), ("pliki tekstowe", ['*.txt', '*.TXT', '*.Txt']), ('pliki csv', ['*.csv', '*.CSV', '*.Csv'])])
config = filedialog.askopenfilename(title="wybierz plik konfiguracyjny", filetypes=[("plik konfiguracyjny", "config*.txt")])
GUI(file, config)

