import requests
import json
import csv
import time
import pyvisa
from datetime import datetime, timedelta
import threading
import queue  # Import the queue module

# --- GPIB Configuration ---
gpib_address = 'GPIB0::2::INSTR'  # Replace with your Fluke 8845A's GPIB address
# --- Web Server Configuration ---
esp8266_url = "http://192.168.1.160"  # Replace with your ESP8266 IP address
# --- CSV File Configuration ---
csv_file = "sensor_data.csv"
csv_columns = ['Timestamp', 'Time', 'Bus Voltage (V)', 'Fluke Voltage (V)', 'Voltage Difference (V)', 'Shunt Voltage (mV)', 'Load Voltage (V)',
               'Current (mA)', 'Power (mW)', 'Acceleration X (m/s^2)', 'Acceleration Y (m/s^2)', 'Acceleration Z (m/s^2)',
               'Rotation X (rad/s)', 'Rotation Y (rad/s)', 'Rotation Z (rad/s)', 'Temperature (°C)', 'ESP8266 Active']  # ESP8266 Active
# --- Battery Threshold ---
ESP8266_LOWER_THRESHOLD = 3.2  # Volts, adjust as needed

# --- Global Variables ---
fluke_data_queue = queue.Queue()
esp_running = True
esp_start_time = None  # track when it started
esp_stop_time = None   # track when it stopped

# Capacity calculation variables:
total_mAh = 0.0
previous_time = None
previous_current = None

def initialize_gpib():
    try:
        rm = pyvisa.ResourceManager()
        instrument = rm.open_resource(gpib_address)
        print(f"Connected to Fluke 8845A at {gpib_address}")
        instrument.query("*IDN?")  # Verify connection
        return instrument
    except Exception as e:
        print(f"Error initializing GPIB: {e}")
        return None

def read_fluke_voltage(instrument):
    try:
        instrument.write("CONF:VOLT:DC 10")
        return float(instrument.query("READ?"))
    except Exception as e:
        print(f"Error reading voltage: {e}")
        return None

def fetch_sensor_data_from_esp():
    global esp_running, esp_start_time, esp_stop_time
    try:
        response = requests.get(esp8266_url)
        response.raise_for_status()
        data = response.json()
        bus_voltage = data['ina219']['busV']
        if bus_voltage < ESP8266_LOWER_THRESHOLD:
            print(f"ESP8266 voltage below threshold ({ESP8266_LOWER_THRESHOLD}V). Stopping ESP data collection.")
            esp_running = False
            if esp_stop_time is None:  # Only record stop time once
                esp_stop_time = datetime.now()
        if esp_start_time is None:
            esp_start_time = datetime.now() # Record when ESP data first appears.
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from ESP8266: {e}")
        esp_running = False
        if esp_stop_time is None: # Only record stop time once
            esp_stop_time = datetime.now()
        return None

def format_time(time_sec):
    hours = int(time_sec // 3600)
    minutes = int((time_sec % 3600) // 60)
    seconds = int(time_sec % 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"

def append_data_to_csv(data, fluke_voltage, filename):
    global total_mAh, previous_time, previous_current
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

    # Default values in case ESP8266 data is missing
    time_str = None
    bus_voltage = None
    shunt_voltage = None
    current = None
    power = None

    if data:
        time_str = format_time(data.get('time', 0))
        bus_voltage = data['ina219']['busV']
        shunt_voltage = data['ina219']['shuntV']
        current = data['ina219']['curr']
        power = data['ina219']['power']

    esp8266_active = esp_running  # True while ESP8266 is actively reporting.

    # Trapezoidal integration of current:
    if data and previous_time is not None and previous_current is not None:
        dt_seconds = (datetime.now() - previous_time).total_seconds()
        dt_hours = dt_seconds / 3600.0  # hours
        avg_current = (current + previous_current) / 2.0
        total_mAh += avg_current * dt_hours

    previous_time = datetime.now()
    previous_current = current

    # Calculate Voltage Difference, handle None values
    voltage_difference = None
    if fluke_voltage is not None and bus_voltage is not None:
        voltage_difference = fluke_voltage - bus_voltage

    row = {
        'Timestamp': timestamp,
        'Time': time_str,
        'Bus Voltage (V)': bus_voltage,
        'Fluke Voltage (V)': fluke_voltage,
        'Voltage Difference (V)': voltage_difference,
        'Shunt Voltage (mV)': shunt_voltage,
        'Load Voltage (V)': data['ina219']['loadV'] if data and 'ina219' in data and 'loadV' in data['ina219'] else None,
        'Current (mA)': current,
        'Power (mW)': power,
        'Acceleration X (m/s^2)': data['mpu6050']['accX'] if data and 'mpu6050' in data else None,
        'Acceleration Y (m/s^2)': data['mpu6050']['accY'] if data and 'mpu6050' in data else None,
        'Acceleration Z (m/s^2)': data['mpu6050']['accZ'] if data and 'mpu6050' in data else None,
        'Rotation X (rad/s)': data['mpu6050']['gyroX'] if data and 'mpu6050' in data else None,
        'Rotation Y (rad/s)': data['mpu6050']['gyroY'] if data and 'mpu6050' in data else None,
        'Rotation Z (rad/s)': data['mpu6050']['gyroZ'] if data and 'mpu6050' in data else None,
        'Temperature (°C)': data['mpu6050']['temp'] if data and 'mpu6050' in data else None,
        'ESP8266 Active': esp8266_active,
    }

    with open(filename, 'a', newline='') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=csv_columns)
        writer.writerow(row)

    print(f"Data saved: {timestamp}, Fluke Voltage: {fluke_voltage}, Bus Voltage: {bus_voltage}, Voltage Difference: {voltage_difference}, ESP8266 Active: {esp8266_active}")

def create_csv_with_header(filename):
    with open(filename, 'w', newline='') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=csv_columns)
        writer.writeheader()

def fluke_reading_thread(instrument):
    """Continuously read voltage from the Fluke meter and put data into a queue."""
    while True:
        fluke_voltage = read_fluke_voltage(instrument)
        if fluke_voltage is not None:
            fluke_data_queue.put(fluke_voltage)
        else:
            fluke_data_queue.put(None)
            print("Failed to read Fluke voltage.")
        time.sleep(0.3)

def main():
    global esp_running, total_mAh, esp_start_time, esp_stop_time

    fluke_instrument = initialize_gpib()
    if fluke_instrument is None:
        print("Failed to initialize GPIB. Exiting.")
        return

    try:
        with open(csv_file, 'r') as f:
            pass
    except FileNotFoundError:
        create_csv_with_header(csv_file)

    fluke_thread = threading.Thread(target=fluke_reading_thread, args=(fluke_instrument,))
    fluke_thread.daemon = True
    fluke_thread.start()

    while True:
        try:
            fluke_voltage = fluke_data_queue.get(timeout=5)
            if fluke_voltage is None:
                print("Skipping iteration due to Fluke reading error.")
                continue
        except queue.Empty:
            print("No Fluke data received for 5 seconds. Skipping iteration.")
            continue

        sensor_data = fetch_sensor_data_from_esp() if esp_running else None
        append_data_to_csv(sensor_data, fluke_voltage, csv_file)

        if not esp_running and fluke_data_queue.empty():
            print("ESP8266 data stopped, and no new Fluke data. Exiting.")
            break

        time.sleep(0.3)

    fluke_instrument.close()

    # Print summary AFTER the main loop:
    print("\n--- Summary ---")
    if esp_start_time:
        print(f"ESP8266 started reporting: {esp_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    if esp_stop_time:
        print(f"ESP8266 stopped reporting: {esp_stop_time.strftime('%Y-%m-%d %H:%M:%S')}")
    if esp_start_time and esp_stop_time:
        duration = esp_stop_time - esp_start_time
        print(f"ESP8266 reporting duration: {duration}")
    print(f"Estimated battery capacity used: {total_mAh:.2f} mAh") # Total mAh.

    # Reset start and stop times for the next run
    esp_start_time = None
    esp_stop_time = None

if __name__ == "__main__":
    main()

