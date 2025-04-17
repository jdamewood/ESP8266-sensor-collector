Here's a summary of the functions in datacollectionjsonGPIB.py and sensorreport.py suitable for a GitHub repository developed with Perplexity:

datacollectionjsonGPIB.py

This script collects sensor data from an ESP8266 and a Fluke 8845A multimeter, then saves it to a CSV file.

* initialize_gpib(): Initializes the GPIB connection to the Fluke 8845A multimeter. It uses the pyvisa library to establish communication and returns an instrument object for further use.

* read_fluke_voltage(instrument): Reads the DC voltage from the Fluke 8845A. It sends commands to configure the meter for DC voltage measurement and retrieves the reading.

* fetch_sensor_data_from_esp(): Retrieves sensor data (INA219 voltage/current, MPU6050 acceleration/rotation/temperature) from the ESP8266 web server by making an HTTP GET request.

* format_time(time_sec): Formats time in seconds to HH:MM:SS format.

* append_data_to_csv(data, fluke_voltage, filename): Appends the sensor data, along with the Fluke voltage reading, to a CSV file. It calculates the voltage difference and estimates battery capacity used via trapezoidal integration of current.

* create_csv_with_header(filename): Creates a new CSV file and writes the header row.

* fluke_reading_thread(instrument): Continuously reads voltage from the Fluke meter in a separate thread. The readings are placed in a queue for the main thread to process.

* main(): The main function that orchestrates the data collection process. It initializes the GPIB connection, creates the CSV file (if it doesn't exist), starts the Fluke reading thread, fetches data from the ESP8266, appends the data to the CSV file, and prints a summary at the end.
 ```Data saved: 2025-04-16 18:30:48.363, Fluke Voltage: 4.17926, Bus Voltage: 4.192, Voltage Difference: -0.012739999999999974, ESP8266 Active: True
Data saved: 2025-04-16 18:30:49.105, Fluke Voltage: 4.179288, Bus Voltage: 4.188, Voltage Difference: -0.008712000000000053, ESP8266 Active: True
Data saved: 2025-04-16 18:30:49.847, Fluke Voltage: 4.179288, Bus Voltage: 4.188, Voltage Difference: -0.008712000000000053, ESP8266 Active: True
Data saved: 2025-04-16 18:30:50.581, Fluke Voltage: 4.179354, Bus Voltage: 4.188, Voltage Difference: -0.00864599999999971, ESP8266 Active: True
``` 

**sensorreport.py**

This script analyzes the data collected by datacollectionjsonGPIB.py from a CSV file and calculates accuracy statistics.

* calculate_rms_accuracy_with_stats(csv_file): This function is the core of the script. It reads data from a CSV file, filters data based on ESP8266 activity, calculates the Root Mean Square (RMS) accuracy, extracts duration, min/max errors, calculates 3-sigma control limits (UCL/LCL), counts outliers, estimates battery capacity, and computes statistics (average, min, and max) for acceleration, rotation, and temperature data.

It reads bus voltage, Fluke voltage, current, acceleration XYZ(m/s^2), rotation XYZ (rad/s), temperature, and ESP8266 active status from the CSV.

* It calculates the difference between Fluke and bus voltage.

* It calculates RMS accuracy, duration, min/max error, UCL/LCL, and outlier count based on voltage differences.

* It estimates battery capacity in mAh.

* It calculates and includes the average, min, and max values for acceleration, rotation, and temperature °C.

```
Analysis Results:
start_time: 2025-04-16 17:40:44.294000
end_time: 2025-04-16 19:28:56.395000
duration: 1:48:12.101000
rms_accuracy: 0.00793586281562684
min_error: -0.019847999999999644
max_error: 0.05315999999999965
ucl: -0.0010998758516112825
lcl: -0.014162871848480526
battery_capacity: 294.7891201388893
outlier_count: 16
acc_x_avg: -3.9728553357866603
acc_x_min: -4.14
acc_x_max: -3.79
acc_y_avg: 7.609757359705166
acc_y_min: 7.4
acc_y_max: 7.77
acc_z_avg: 2.8460579576817113
acc_z_min: 2.61
acc_z_max: 3.0
rot_x_avg: -0.09692042318308469
rot_x_min: -0.15
rot_x_max: -0.07
rot_y_avg: 0.039232980680775256
rot_y_min: -0.03
rot_y_max: 0.1
rot_z_avg: -0.013815547378105428
rot_z_min: -0.12
rot_z_max: 0.21
temp_avg: 25.54500344986224
temp_min: 25.34
temp_max: 25.85

```
**plot_sensor_data.py** Script Summary
![all_plots_2x4](https://github.com/user-attachments/assets/d6b7d48d-b004-424d-bb00-703210f82b2d)

This Python script `plot_sensor_data.py` analyzes sensor data from a CSV file and generates a figure containing eight subplots, arranged in a 2x4 grid. It visualizes:

*   **Voltage Comparison:** Bus and Fluke voltages with peak annotations and a forced annotation for Fluke voltage.
*   **Voltage Difference:** Displays the voltage difference with RMS error and 3-sigma control limits.
*   **Shunt/Load Voltage:** Twin axes plot showing shunt and load voltages.
*   **Current Draw:** Plots the current with peak annotations.
*   **Power Consumption:** Visualizes power consumption with peak markings.
*   **Acceleration:** Displays acceleration data.
*   **Rotation:** Shows rotation data.
*   **Temperature:** Plots temperature with peak annotations.

The script utilizes `pandas` for data loading and manipulation, `matplotlib` for plotting, and `scipy.signal` for peak detection. It includes utility functions for annotation and styling to ensure consistent and informative visualizations.

**Dependencies**

import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from matplotlib.dates import DateFormatter
import numpy as np

*   `pandas`: Used for reading the CSV file and data manipulation.
*   `matplotlib.pyplot`: Used for creating visualizations of the data.
*   `scipy.signal`: Used for finding the peaks of the plots for visual emphasis.
*   `matplotlib.dates`: Used for managing the styling of date axes.
*   `numpy`: Used for numerical operations, especially calculating RMS.

**Data Loading (`df = pd.read_csv(...)`)**

df = pd.read_csv('sensor_data.csv', parse_dates=['Timestamp'])

**Purpose**: This section reads the sensor data from a CSV file into a `pandas` DataFrame, parsing the 'Timestamp' column as datetime objects.

**Utility Functions**

def annotate_plot(ax, df, time_col, data_col, peaks, color, forced_time=None, fmt=None, y_offset=5):
"""Annotates peaks on a plot, adding a forced annotation if specified."""
**... (implementation details)**

def style_plot(ax):
"""Applies consistent styling to a plot."""
**... (implementation details)**

def calculate_rms(data):
"""Calculates the Root Mean Square of a data series."""
**... (implementation details)**

**Purpose:** These functions perform basic operations such as peak value annotation, plot styling, and calculating the RMS error to reduce code duplication and improve readability.
*   `annotate_plot`:  Adds annotations for peaks, with options for forced annotations and flexible formatting.
*   `style_plot`: Applies consistent styling (date formatting, gridlines, tick rotation) to all subplots.
*   `calculate_rms`: Calculates the Root Mean Square (RMS) of a given data series.

**Plotting Functions**

**Voltage Comparison** (Forced Annotation)
ax = axs
ax.plot(df['Timestamp'], df['Bus Voltage (V)'], 'b-', label='Bus (V)')

**Purpose:** This section contains the code for generating eight different sensor data plots. It includes data plotting, peak finding, styling, and annotation for each subplot.
* The same plotting process is done in all 8 plots.
**Final Formatting and Display**

plt.tight_layout()
plt.savefig('all_plots_2x4.png', dpi=300, bbox_inches='tight')
plt.show()

**Purpose**: This section ensures that all plots are properly spaced to prevent overlapping elements, saves the combined plot to a file, and displays it.
