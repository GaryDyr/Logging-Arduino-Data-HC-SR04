"""

  **DEPENDS ON SPECIFIC ARDUINO SKETCH: "usonic_streaming" RUNNING ON THE ARDUINO.  
  Reads and saves ultrasonic sensor data from the Arduino through USB port.
  Will work with Windows, Linux (Ubuntu) for sure.
  Data is added to an array until Arduino signals output is done, and then data is 
  dumped to a csv file that the module automatically generates.
  Possibly will work with MAC, BUT NEEDS TWEAKING IN SETTINGS AND IN serial_ports() 
  method.
  Sketch pings at 33 ms interval for whatever iterator set to, like 
  2000 pings. then sends '111111', to indicate data transmission complete. 
  and saves data to csv file (SEE SETTINGS).
  Order of starting is also important: 
    1. Connect Arduino USB serial port to computer USB serial port.
    2. Load the sketch into Arduino,
    3. Run this module. Each time you run the python file it will reset the arduino.
    
  Logger expects data to start wihtin 7 seconds, (variable: time_stop). If no data 
  appears on port for 7 s or more. the module assumes no more data will be coming.. 
  and dumps data to csv file. 
  
  csv output format will be stream_mmddyy_##.csv,  where ## represents an index for 
  a file, starts with 00. 
  
  The code tries to determine the port conecting the Arduino, 'COM#' for Windows, 
  /dev/tty/ACM0 or /dev/tty/USB0 for linux.
  Be sure to set default_port variable in SETTINGS, which used if port not found. 
  Make sure baud rate in Settings is the same as is set in the sketch, default is 9600.

  Requires PySerial library be installed
"""

import sys
import glob
import serial
import time
from datetime import datetime, timedelta
import serial.tools.list_ports
import os.path
import platform
import re
import sys
import csv

#identify current OS: windows, linux, or mac; impacts reading settings
if sys.platform.startswith('win'):
  os_type = "WIN"
elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
  os_type = "LINUX"
elif sys.platform.startswith('darwin'):
  os_type = "DARWIN"
else:
  raise EnvironmentError('Unsupported platform')
os_platform = os_type

#----------------------------------------------------------
#-------------CHANGE SETTINGS HERE--------------------------
# GET PATH TO CSV FILES
# Name of first 7 characters of csv file name; 
# length and search name can be changed in def walk_files, but right now
# searches for file with specifically first 7 characters as:
csv_prefix = 'stream_' 
header = "usec" # header for csv output; there is a minor problem with how this prints
# DEPENDING ON OS, CHANGE ONE OR MORE OF THESE PATHS
# THESE DIRECTORIES MUST BE MANUALLY CREATED BEFORE RUNNING THIS MODULE
win_path = 'F:/python_files/csvfiles'
#current for linus would be HOME/user/csvfiles or HOME/csvfiles
linux_path = os.path.join(os.path.expanduser('~'), 'csvfiles')
mac_path =  "" # No clue on how MAC directory stuff works.

#SET A DEFAULT PORT, IF serial_ports() method fails
if os_platform == "WIN":
  arduino_port = "COM3"
elif os_platform == "LINUX":
  arduino_port = '/dev/ttyACM0'
elif os_platform == "DARWIN":
  arduino_port ==  '/dev/tty.usbmodem*' #no idea how many port show up; change as needed

#SET BAUD RATE  
baud_rate = 9600
#SET THE WAIT TIME VALUE; IF NO DATA ON PORT DURING THIS PERIOD, PROGRAM 
# ASSUMES OUTPUT ENDED, SAVES DATA AND STOPS.
time_stop = 7
#---------------END SETTINGS-------------------------------
#----------------------------------------------------------

#next block is redundant, but allows for more flexibility if needed.
if os_platform == "WIN":
  input_path = win_path
elif os_platform == "LINUX":
  input_path = linux_path
elif os_platform == "DARWIN":
  input_path = mac_path

#input_path = sys.argv[1] #uncomment to run from PS; not currently used
print('input path is: ', input_path)
os.chdir(input_path)
datestr = datetime.today().strftime('%m%d%y')
#build a current date csv file string for testing.
filename = csv_prefix + datestr + '_00' + '.csv' #set a default name to compare
cwd = os.getcwd()
dir_path = os.path.dirname(os.path.realpath(__file__))
print('python module directory is: ', dir_path)
print('Current working dir. is: ', cwd)

"""
NOT CURRENTLY USED:
def check_platform():
#tries to identify current OS: windows, linux, mac
#not used, but code duplicated in body
  if sys.platform.startswith('win'):
    os_type = "WIN"
  #may have  to alter if starts differently    
  elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
    # this excludes your current terminal "/dev/tty"
    os_type = "LINUX"
  elif sys.platform.startswith('darwin'):
    os_type = "DARWIN"
  else:
    raise EnvironmentError('Unsupported platform')
  result = os_type
"""

def walk_files(directory_path, latest_file):
  #gets the latest directory file info.
  print('searching directory path for csv file: ', directory_path)
  #check file creation dates
  #Walk through files in directory_path, including subdirectories
  #os.walk yields a 3-tuple (dirpath, dirnames, filenames).
  # "_" in tuple is a sort of don't care variable marker.
  fnd_file = False
  for root, _, filenames in os.walk(directory_path):
      old_date = ""
      for fname in filenames:
        #what is the latest stream file in dir w/ current date?
        if fname[:13] == latest_file[:13]:
          file_date = os.path.getctime(fname)
          if old_date == "":
            old_date = os.path.getctime(fname)
            latest_file = fname
            fnd_file = True #fnd a file; may or may not be latest
          if file_date > old_date:
            latest_file = fname
            old_date = file_date
            fnd_file = True
        #file name date collision; add 1 to version suffix/            
        #this will fail if we have more than 99 csv file in one day
        #get the file number add 1 to it and rebuild name.
      if fnd_file:
        if (latest_file[-6:][:2]) == '00':
          copy_num = '01'
        else:  
          copy_num = int(latest_file[-6:][:2].lstrip("0"))+1

        latest_file = latest_file[:14] + str(copy_num).zfill(2) + '.csv'  
        print('output file will be: ', latest_file) #will have number 00
        return latest_file
  if not fnd_file:
    print('output file will be: ', latest_file)
    return latest_file
 
# def copied and modified from https://stackoverflow.com/questions/12090503/listing-available-com-ports-with-python
def serial_ports():
    """ Lists serial port names, attempts to find port for Arduino
        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
      ports = ['COM%s' % (i + 1) for i in range(256)]
      port_sys_type = "WIN"
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
      # this excludes your current terminal "/dev/tty; will find ACM and USB"
      ports = glob.glob('/dev/tty[A-Za-z]*')
      port_sys_type = "LINUX"
    elif sys.platform.startswith('darwin'):
      #likely needs finessing to work well. 
      port_sys_type = "DARWIN"
      ports = glob.glob('/dev/cu.usb*') #might also be /dev/tty*, * = ?.usbmodem or .serial
    else:
      raise EnvironmentError('Unsupported platform')
    result = []
    for port in ports:
      try:
        s = serial.Serial(port)
        s.close()
        result.append(port)
      except (OSError, serial.SerialException):
        pass
    #With my Uno, the port manufacturer property was"Arduino www.arduino.com". 
    #Arduino clones using Arduino.cc specs regularly provide this info.  We are only 
    #setting up either win or linux for sure right now. MAC may need work
    all_ports = list(serial.tools.list_ports.comports())
    #search for Arduino among the manufacturer properties of the ports.
    for ap in all_ports: #go through each user HID port; get manufacturer
      pm = ap.manufacturer
      ndx = pm.find('rduin') #only use partial name
       # 3 cases to search: win, linux, MAC      
      if (ndx != -1): 
        if (port_sys_type == 'WIN'):
          pdev = ap.device
          ndx = pdev.find('COM')  
          if ndx > -1:
            the_port = pdev[ndx:ndx+4] #get full port ref, e.g., COM#
            for pcom in result:
              if the_port == pcom:
                return the_port, pcom
              else:
                return None, None
      elif (port_sys_type == 'LINUX'):
        # defined port_type in settings, because commonly 'ACM0' or 'USB0'
        pdev = ap.device
        ndx = pdev.find('tty') #e.g., '/dev/ttyACM0' if default
        if ndx > -1:
          the_port = ap.device
          for pcom in result:
            if the_port[-7:] == pcom[-7:]:
              return the_port, pcom
            else:
              return None, None
      elif (port_sys_type == 'DARWIN'):
        pdev = ap.device 
        #NEEDS WORK!!!! port ??? /dev/ttyusb or/dev/cu.usbmodem#####etc      
        ndx = ap.find('cu.usb') 
        if ndx > -1:
          the_port = ap.device
          for pcom in result:
            if the_port == pcom:
              return the_port, pcom
            else:
              return None, None
        
def set_serial(COMport, Baudrate):
  #Be careful with timeout and readline. If set to zero will 
  #wait forever for EOL character. If an EOL occurs before timeout value
  #then reads and resets timeout. If start usonic_streaming sketch 
  #before starting python, a short timeout is probably ok, but if 
  #python started first, could time out and stop cycle before starting
  #to see data. So we use 7 seconds, which should be more than sufficient time
  #to reboot the Arduino. 
  arduino = serial.Serial(COMport, Baudrate, timeout= time_stop)
  arduino.flushInput()
  time.sleep(1) #time to settle down 1 s
  print('serial set')
  return arduino

def get_data(arduino):
  #watches and get port data from Arduino
  print('geting_data')
  data_out = []
  while True:
    try:
      data = arduino.readline() 
      print(data[:-2].decode('utf-8')) #remove the CRLF; chr 13 & 10
      if data:
        #if data < 111111: #there was some sort of conversion error with this
        data_out.append(data[:-2].decode('utf-8'))
      else:
        arduino.close 
        break
    except KeyboardInterrupt:
          print("Keyboard Interrupt")
          break
  return data_out
  
if __name__ == '__main__':
  port_name, a_port = serial_ports()
  print(port_name, a_port)
  if port_name:
    print('Found the Arduino on:', port_name)
  else:
    #One last attempt; try arduino_default
    while True:
      myports = [tuple(p) for p in list(serial.tools.list_ports.comports())]
      #check against default
      if arduino_port not in myports:
        print('Did not find port or default port associated with Arduino') 
        print('Is Arduino powered up? Is it connnected?')
        print('Aborting')
        sys.exit(1)
      
  arduino_port = a_port
  print('setting serial port.')
  arduino = set_serial(arduino_port, baud_rate)
  #according to online stuff, this should reset Arduino
  #but turns out not needed. setting serial resets Arduino 
  #arduino.setDTR(False) # Drop DTR
  #time.sleep(2)    # Read somewhere that 22ms is what the UI does.
  #arduino.setDTR(True)  # UP the DTR back
  if arduino.isOpen():
    print('port_status: open...starting data collection.')
  else:
    print('port_status: Port: ', arduino_port, 'not open...aborting')
    sys.exit(1)
    
  data_out = get_data(arduino)
  print('number of points recorded: ', len(data_out))
  if data_out:
    print('Saving data')
    filename = walk_files(input_path, filename)
    with open(filename, "w", newline = '') as f:
      writer = csv.writer(f)
      writer.writerow(header)
      for x in data_out : writer.writerow ([x])
  print(len(data_out), ' values have been saved in file ', filename)
  

