import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from matplotlib.dates import DateFormatter
import numpy as np

# 1. Load Data
df = pd.read_csv('sensor_data.csv', parse_dates=['Timestamp'])

# 2. Create Figure and Subplots (2x4)
fig, axs = plt.subplots(2, 4, figsize=(24, 12))  # Wider figure
plt.subplots_adjust(hspace=0.5, wspace=0.4)

# Flatten the axs array for easier indexing
axs = axs.flatten()

# --- Utility Functions --- (same as before)
def annotate_plot(ax, df, time_col, data_col, peaks, color, forced_time=None, fmt=None, y_offset=5):
    """Annotates peaks on a plot, adding a forced annotation if specified."""
    for peak in peaks:
        if fmt:
            label = fmt.format(df[data_col].iloc[peak])
        else:
            label = f'{df[data_col].iloc[peak]:.3f}'
        ax.annotate(label,
                    xy=(df[time_col].iloc[peak], df[data_col].iloc[peak]),
                    xytext=(5, y_offset), textcoords='offset points',
                    fontsize=8, color=color)
    if forced_time:
        target_time = pd.to_datetime(forced_time)
        time_diff = abs(df[time_col] - target_time)
        closest_index = time_diff.idxmin()
        if fmt:
            label = fmt.format(df[data_col].iloc[closest_index]) + ' (Forced)'
        else:
            label = f'{df[data_col].iloc[closest_index]:.3f} (Forced)'
        ax.annotate(label,
                    xy=(df[time_col].iloc[closest_index], df[data_col].iloc[closest_index]),
                    xytext=(5, -15), textcoords='offset points',
                    fontsize=8, color=color)

def style_plot(ax):
    """Applies consistent styling to a plot."""
    ax.xaxis.set_major_formatter(DateFormatter('%H:%M:%S'))
    ax.grid(True)
    ax.tick_params(axis='x', rotation=45)

def calculate_rms(data):
    """Calculates the Root Mean Square of a data series."""
    return np.sqrt(np.mean(data**2))

# --- Plotting Functions ---

# 3. Voltage Comparison (Forced Annotation)
ax = axs[0]
ax.plot(df['Timestamp'], df['Bus Voltage (V)'], 'b-', label='Bus (V)')
ax.plot(df['Timestamp'], df['Fluke Voltage (V)'], 'r-', label='Fluke (V)')
bus_peaks, _ = find_peaks(df['Bus Voltage (V)'], prominence=0.05)
fluke_peaks, _ = find_peaks(df['Fluke Voltage (V)'], prominence=0.01)
ax.plot(df['Timestamp'].iloc[bus_peaks], df['Bus Voltage (V)'].iloc[bus_peaks], 'bo', markersize=8, label='Bus Peaks')
ax.plot(df['Timestamp'].iloc[fluke_peaks], df['Fluke Voltage (V)'].iloc[fluke_peaks], 'ro', markersize=8, label='Fluke Peaks')
annotate_plot(ax, df, 'Timestamp', 'Bus Voltage (V)', bus_peaks, 'blue', y_offset=5)
annotate_plot(ax, df, 'Timestamp', 'Fluke Voltage (V)', fluke_peaks, 'red', forced_time='2025-04-17 23:41:00', y_offset=-15)
ax.set_title('Voltage Comparison')
style_plot(ax)
ax.legend()

# 4. Voltage Difference (RMS, UCL/LCL)
ax = axs[1]
voltage_diff = df['Voltage Difference (V)']
rms_error = calculate_rms(voltage_diff)
mean_voltage = voltage_diff.mean()
std_dev = voltage_diff.std()
ucl = mean_voltage + 3 * std_dev
lcl = mean_voltage - 3 * std_dev
ax.plot(df['Timestamp'], voltage_diff, 'g-', label='Difference (V)')
v_diff_peaks, _ = find_peaks(df['Voltage Difference (V)'].abs(), prominence=0.01)
ax.plot(df['Timestamp'].iloc[v_diff_peaks], df['Voltage Difference (V)'].iloc[v_diff_peaks], 'go', markersize=8, label='Diff Peaks')
ax.axhline(ucl, color='r', linestyle='--', label='UCL (3-sigma)')
ax.axhline(lcl, color='b', linestyle='--', label='LCL (3-sigma)')
ax.text(0.5, 0.5, f'RMS Error: {rms_error:.3f} V',
        horizontalalignment='center', verticalalignment='center',
        transform=ax.transAxes, fontsize=10, color='purple')
annotate_plot(ax, df, 'Timestamp', 'Voltage Difference (V)', v_diff_peaks, 'green', y_offset=5)
ax.set_title('Voltage Difference with RMS and Control Limits')
style_plot(ax)
ax.legend()

# 5. Shunt/Load Voltage (Twin Axes)
ax = axs[2]  # Main Axis
ax.plot(df['Timestamp'], df['Shunt Voltage (mV)'], 'm-', label='Shunt (mV)')
shunt_peaks, _ = find_peaks(df['Shunt Voltage (mV)'], prominence=0.5)
ax.plot(df['Timestamp'].iloc[shunt_peaks], df['Shunt Voltage (mV)'].iloc[shunt_peaks], 'mo', markersize=8, label='Shunt Peaks')
annotate_plot(ax, df, 'Timestamp', 'Shunt Voltage (mV)', shunt_peaks, 'm', y_offset=5)
ax.set_ylabel('Shunt (mV)', color='m')

ax2 = ax.twinx()  # Twin Axis
ax2.plot(df['Timestamp'], df['Load Voltage (V)'], 'c-', label='Load (V)')
load_peaks, _ = find_peaks(df['Load Voltage (V)'], prominence=0.05)
ax2.plot(df['Timestamp'].iloc[load_peaks], df['Load Voltage (V)'].iloc[load_peaks], 'co', markersize=8, label='Load Peaks')
annotate_plot(ax2, df, 'Timestamp', 'Load Voltage (V)', load_peaks, 'c', y_offset=5)
ax2.set_ylabel('Load (V)', color='c')
ax.set_title('Shunt & Load Voltages')
style_plot(ax)  # DO NOT apply style to twin axes.
ax.grid(False)  # Prevent duplicate gridlines from twin axis.
ax2.grid(False)

# Explicitly create and position the legend
lines, labels = ax.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax.legend(lines + lines2, labels + labels2, loc='upper left')

# 6. Current
ax = axs[3]
ax.plot(df['Timestamp'], df['Current (mA)'], 'k-', label='Current (mA)')
current_peaks, _ = find_peaks(df['Current (mA)'], prominence=10)
ax.plot(df['Timestamp'].iloc[current_peaks], df['Current (mA)'].iloc[current_peaks], 'ko', markersize=8, label='Current Peaks')
annotate_plot(ax, df, 'Timestamp', 'Current (mA)', current_peaks, 'black', y_offset=5)
ax.set_title('Current Draw')
style_plot(ax)
ax.legend()

# 7. Power
ax = axs[4]
ax.plot(df['Timestamp'], df['Power (mW)'], 'orange', label='Power (mW)')
power_peaks, _ = find_peaks(df['Power (mW)'], prominence=5)
ax.plot(df['Timestamp'].iloc[power_peaks], df['Power (mW)'].iloc[power_peaks], 'o', color='orange', markersize=6, label='Power Peaks')
annotate_plot(ax, df, 'Timestamp', 'Power (mW)', power_peaks, 'orange', y_offset=5)
ax.set_title('Power Consumption')
style_plot(ax)
ax.legend()

# 8. Acceleration
ax = axs[5]
ax.plot(df['Timestamp'], df['Acceleration X (m/s^2)'], 'r-', label='Acc X (m/s^2)')
accel_peaks, _ = find_peaks(df['Acceleration X (m/s^2)'].abs(), prominence=0.1)
ax.plot(df['Timestamp'].iloc[accel_peaks], df['Acceleration X (m/s^2)'].iloc[accel_peaks], 'o', color='red', markersize=6, label='Acc Peaks')
annotate_plot(ax, df, 'Timestamp', 'Acceleration X (m/s^2)', accel_peaks, 'red', y_offset=5)
ax.set_title('Acceleration')
style_plot(ax)
ax.legend()

# 9. Rotation
ax = axs[6]
ax.plot(df['Timestamp'], df['Rotation X (rad/s)'], 'r-', label='Rot X (rad/s)')
rot_peaks, _ = find_peaks(df['Rotation X (rad/s)'].abs(), prominence=0.05)
ax.plot(df['Timestamp'].iloc[rot_peaks], df['Rotation X (rad/s)'].iloc[rot_peaks], 'o', color='red', markersize=6, label='Rot Peaks')
annotate_plot(ax, df, 'Timestamp', 'Rotation X (rad/s)', rot_peaks, 'red', y_offset=5)
ax.set_title('Rotation')
style_plot(ax)
ax.legend()

# 10. Temperature
ax = axs[7]
ax.plot(df['Timestamp'], df['Temperature (°C)'], 'm-', label='Temp (°C)')
temp_peaks, _ = find_peaks(df['Temperature (°C)'], prominence=0.1)
ax.plot(df['Timestamp'].iloc[temp_peaks], df['Temperature (°C)'].iloc[temp_peaks], 'mo', markersize=8, label='Temp Peaks')
annotate_plot(ax, df, 'Timestamp', 'Temperature (°C)', temp_peaks, 'm', fmt="{:.1f}°C", y_offset=5)
ax.set_title('Temperature')
style_plot(ax)
ax.legend()

# --- FINAL Formatting and Showing ---
plt.tight_layout()
plt.savefig('all_plots_2x4.png', dpi=300, bbox_inches='tight')
plt.show()

