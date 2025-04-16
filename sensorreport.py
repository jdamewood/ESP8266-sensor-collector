import csv
import math
from datetime import datetime

def calculate_rms_accuracy_with_stats(csv_file):
    # created with Perplexity 16Apr2025
    
    """
    Calculates the Root Mean Square (RMS) accuracy, duration, min, max, 3-sigma limits (UCL/LCL)
    of the INA219 bus voltage measurements compared to the Fluke voltage measurements in a CSV file,
    and includes statistics for acceleration, rotation, and temperature data.

    Args:
        csv_file (str): Path to the CSV file containing sensor data.

    Returns:
        dict: A dictionary containing the calculated statistics, or None if an error occurred.
    """
    bus_voltages = []
    fluke_voltages = []
    timestamps = []
    currents = []
    esp8266_active = []
    acc_x_values = []
    acc_y_values = []
    acc_z_values = []
    rot_x_values = []
    rot_y_values = []
    rot_z_values = []
    temp_values = []

    try:
        with open(csv_file, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
                    timestamp_str = row['Timestamp']
                    bus_voltage = float(row['Bus Voltage (V)'])
                    fluke_voltage = float(row['Fluke Voltage (V)'])
                    current = float(row['Current (mA)']) if row.get('Current (mA)') else None
                    active = row['ESP8266 Active'].lower() == 'true' if row.get('ESP8266 Active') else False
                    acc_x = float(row['Acceleration X (m/s^2)']) if row.get('Acceleration X (m/s^2)') else None
                    acc_y = float(row['Acceleration Y (m/s^2)']) if row.get('Acceleration Y (m/s^2)') else None
                    acc_z = float(row['Acceleration Z (m/s^2)']) if row.get('Acceleration Z (m/s^2)') else None
                    rot_x = float(row['Rotation X (rad/s)']) if row.get('Rotation X (rad/s)') else None
                    rot_y = float(row['Rotation Y (rad/s)']) if row.get('Rotation Y (rad/s)') else None
                    rot_z = float(row['Rotation Z (rad/s)']) if row.get('Rotation Z (rad/s)') else None
                    temp = float(row['Temperature (°C)']) if row.get('Temperature (°C)') else None

                    # Parse timestamp string into datetime object
                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S.%f')

                    bus_voltages.append(bus_voltage)
                    fluke_voltages.append(fluke_voltage)
                    timestamps.append(timestamp)
                    currents.append(current)
                    esp8266_active.append(active)
                    acc_x_values.append(acc_x)
                    acc_y_values.append(acc_y)
                    acc_z_values.append(acc_z)
                    rot_x_values.append(rot_x)
                    rot_y_values.append(rot_y)
                    rot_z_values.append(rot_z)
                    temp_values.append(temp)

                except ValueError as e:
                    print(f"Skipping row due to invalid data: {e}")
                    continue  # Skip to the next row if there's an error

        if not bus_voltages or not fluke_voltages or not timestamps:
            print("No valid voltage data found in the CSV file.")
            return None

        # Filter data for when ESP8266 was active
        active_data = [(timestamps[i], bus_voltages[i], fluke_voltages[i], currents[i],
                        acc_x_values[i], acc_y_values[i], acc_z_values[i],
                        rot_x_values[i], rot_y_values[i], rot_z_values[i], temp_values[i])
                       for i, active in enumerate(esp8266_active) if active]

        if not active_data or len(active_data) < 2:
            print("No ESP8266 active data found.")
            return None

        (active_timestamps, active_bus_voltages, active_fluke_voltages, active_currents,
         active_acc_x, active_acc_y, active_acc_z,
         active_rot_x, active_rot_y, active_rot_z, active_temp) = zip(*active_data)

        # Calculate the differences between Bus Voltage and Fluke Voltage
        differences = [(fluke - bus) for fluke, bus in zip(active_fluke_voltages, active_bus_voltages)]

        # Calculate the Mean Squared Error (MSE)
        squared_differences = [diff ** 2 for diff in differences]
        mse = sum(squared_differences) / len(squared_differences)

        # Calculate the Root Mean Square (RMS)
        rms = math.sqrt(mse)

        # Calculate duration
        start_time = active_timestamps[0]
        end_time = active_timestamps[-1]
        duration = end_time - start_time

        # Calculate min and max errors
        min_error = min(differences)
        max_error = max(differences)

        # Calculate average error and standard deviation for voltage differences
        average_error = sum(differences) / len(differences)
        squared_diff_from_mean = [(diff - average_error) ** 2 for diff in differences]
        variance = sum(squared_diff_from_mean) / len(differences)
        standard_deviation = math.sqrt(variance)

        # Calculate 3-sigma control limits (UCL and LCL)
        ucl = average_error + 3 * standard_deviation
        lcl = average_error - 3 * standard_deviation

        # Count the number of samples outside UCL and LCL
        outlier_count = sum(1 for diff in differences if diff < lcl or diff > ucl)

        # Calculate battery capacity
        total_mAh = 0.0
        for i in range(1, len(active_timestamps)):
            dt_hours = (active_timestamps[i] - active_timestamps[i-1]).total_seconds() / 3600.0
            avg_current = (active_currents[i] + active_currents[i-1]) / 2.0 if active_currents[i] is not None and active_currents[i-1] is not None else 0.0
            total_mAh += avg_current * dt_hours

        # Helper function to calculate statistics
        def calculate_stats(data):
            if not data:
                return None, None, None
            avg = sum(data) / len(data)
            min_val = min(data)
            max_val = max(data)
            return avg, min_val, max_val

        # Calculate statistics for acceleration
        avg_acc_x, min_acc_x, max_acc_x = calculate_stats(active_acc_x) if active_acc_x else (None, None, None)
        avg_acc_y, min_acc_y, max_acc_y = calculate_stats(active_acc_y) if active_acc_y else (None, None, None)
        avg_acc_z, min_acc_z, max_acc_z = calculate_stats(active_acc_z) if active_acc_z else (None, None, None)

        # Calculate statistics for rotation
        avg_rot_x, min_rot_x, max_rot_x = calculate_stats(active_rot_x) if active_rot_x else (None, None, None)
        avg_rot_y, min_rot_y, max_rot_y = calculate_stats(active_rot_y) if active_rot_y else (None, None, None)
        avg_rot_z, min_rot_z, max_rot_z = calculate_stats(active_rot_z) if active_rot_z else (None, None, None)

        # Calculate statistics for temperature
        avg_temp, min_temp, max_temp = calculate_stats(active_temp) if active_temp else (None, None, None)

        # Prepare results dictionary
        results = {
            'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S.%f'),
            'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S.%f'),
            'duration': str(duration),
            'rms_accuracy': rms,
            'min_error': min_error,
            'max_error': max_error,
            'ucl': ucl,
            'lcl': lcl,
            'battery_capacity': abs(total_mAh),
            'outlier_count': outlier_count,
            'acc_x_avg': avg_acc_x, 'acc_x_min': min_acc_x, 'acc_x_max': max_acc_x,
            'acc_y_avg': avg_acc_y, 'acc_y_min': min_acc_y, 'acc_y_max': max_acc_y,
            'acc_z_avg': avg_acc_z, 'acc_z_min': min_acc_z, 'acc_z_max': max_acc_z,
            'rot_x_avg': avg_rot_x, 'rot_x_min': min_rot_x, 'rot_x_max': max_rot_x,
            'rot_y_avg': avg_rot_y, 'rot_y_min': min_rot_y, 'rot_y_max': max_rot_y,
            'rot_z_avg': avg_rot_z, 'rot_z_min': min_rot_z, 'rot_z_max': max_rot_z,
            'temp_avg': avg_temp, 'temp_min': min_temp, 'temp_max': max_temp,
        }

        return results

    except FileNotFoundError:
        print(f"Error: The file '{csv_file}' was not found.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

# Example usage:
csv_file_path = 'sensor_data.csv'  # Replace with the actual path to your CSV file
analysis_results = calculate_rms_accuracy_with_stats(csv_file_path)

if analysis_results:
    print("Analysis Results:")
    for key, value in analysis_results.items():
        print(f"{key}: {value}")
else:
    print("Could not calculate RMS accuracy and statistics.")

