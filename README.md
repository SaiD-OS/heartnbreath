# Heart Rate and Breathing Rate Measurement

## Get Started
Python is a prerequisite and must be installed on your system

> [!NOTE]
> The below commands are for a Windows System. On a Linux system the activate and deactivate commands for the virtual environment change, make the change accordingly.

Run the following commands to clone the repo, create a virtual environment, install required dependencies for the project
```
git clone https://github.com/SaiD-OS/heartnbreath.git
cd heartnbreath
python -m venv .
Scripts\activate
python -m ensurepip --upgrade
pip install -r requirements.txt
Scripts\deactivate.bat
```

Run the application
```
Scripts\activate
python Src\index.py
```

## Architechture

1. Main Thread     -> GUI
2. GUI spawns      -> Reader
3. GUI spawns      -> Parser
4. Parser spaws    -> SaveRawData

### GUI
Has all the components to load the Interface
1. **RootGUI** -> Initializes tkinter and defines the geometry of the Interface
2. **SelectionGUI** -> Comprises of all the user interaction interfaces
    * COM Port, Baud Rate, and Radar Selection
    * Plot type selection -> Original Data Plot without any modifications, Fourier Transform on the collected data, Applying low/high pass filters, interpolation stratergies etc
    * Radar Configuration Settings
    * Variables that can be used to edit the Data modifications
3. **PlotGUI** -> Will generate the interface for Plotting

### Reader
This will perform reading from/writing to the UART channel to read sensor data and modify sensor configs
1. SerialOpen
2. SerialClose
3. SerialReceiveStream
4. SerialWriteStream

### Parser
The data sent by the Sensor is in bytes and the format is described below. This data is required to be extracted based on demand. This raw sensor data will be modified by using filters, interpolation, transforms, etc
This raw data collected will be saved to a file, cant store modified decoded data as this will increase the load on the processing without any reason. Write a separate file parser with the same functionality that will parse the raw data into desired data separately of this application

* **Head Byte 1**: 0x53
* **Head Byte 2**: 0x59
* **Packet Type**: Specific Information, Detailed Information, etc
* **Data Type**: Exit energy information, Static Distance information, Movement energy information, Dynamic Distance information, Heartbeat signal, Breathing signal, Heart rate(static body), Breath rate(static body), etc
* **Trail Byte 1**: 0x54
* **Trail Byte 2**: 0x43

1. DecodeMessage
2. Decode24GHzSensorMessage
3. Decode60GHzSensorMessage
4. SaveRawData
5. AllPassFilter        -> Limit certain frequencies from the raw data. Acts as HighPass and LowPass filter based on a boolean flag
Below mentioned functions will return (X, Y) tuples for plotting graph data. 

> [!IMPORTANT]
> Whenever such a function is declared the fnlist dictionary should be updated with the function

6. FourierTransform     -> Plots the density of the frequencies found in the data; X -> frequency domain, Y -> density based on occurence of the respective Frequency
7. RawData              -> No modification provide the data for plotting as is X -> time domain, Y -> Energy Signals from the sensor
8. HeartRate            -> Modified Raw data to extract Heartbeat signal
9. BreathRate           -> Modified Raw data to extract Breathing signal
