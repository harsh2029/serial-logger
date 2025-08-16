import serial
import time
import argparse
from datetime import datetime

# Argument parser setup
# Argument parser setup with default values shown in help
parser = argparse.ArgumentParser(
    description="Serial HEX Viewer with Timing and Logging",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
parser.add_argument("port", type=str, help="Serial port name (e.g., COM1 OR /dev/ttyS0)")
parser.add_argument("-b", "--baudrate", type=int, default=9600, help="Baud rate")
parser.add_argument("-lt", "--line-time", type=float, default=0.01, help="Serial read timeout in seconds to break data chunk to the next line")
parser.add_argument("-l", "--logfile", type=str, help="Optional log file to save HEX output with timestamps")
parser.add_argument("-qt", "--quit-timeout", type=float, help="Quit terminal on given timeout if no data received")

args = parser.parse_args()

# Initialize serial connection
ser = serial.Serial(port=args.port, baudrate=args.baudrate, timeout=1)

buffer = bytearray()
start_time = time.time()
first_byte_received = False
last_byte_time = None

# Open log file if specified
log_file = open(args.logfile, "w", encoding="utf-8") if args.logfile else None

def log_line(hex_line):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    line = f"[{timestamp}] {hex_line}"
    print(line)
    if log_file:
        log_file.write(line + "\n")

try:
    while True:
        data = ser.read(ser.in_waiting or 1)
        current_time = time.time()

        if not first_byte_received:
            # Wait up to 60 seconds for the first byte
            if data:
                buffer.extend(data)
                first_byte_received = True
                last_byte_time = current_time
            elif args.quit_timeout and current_time - start_time > args.quit_timeout:
                print(f"No data received within {args.quit_timeout} seconds. Exiting.")
                break
        else:
            if data:
                # Check time gap between bytes
                if current_time - last_byte_time > args.line_time:
                    if buffer:
                        hex_line = " ".join(f"{b:02X}" for b in buffer)
                        log_line(hex_line)
                        buffer.clear()
                buffer.extend(data)
                last_byte_time = current_time
            elif args.quit_timeout and current_time - last_byte_time > args.quit_timeout:
                if buffer:
                    hex_line = " ".join(f"{b:02X}" for b in buffer)
                    log_line(hex_line)
                print(f"No new data within {args.quit_timeout} second. Exiting.")
                break

except KeyboardInterrupt:
    if buffer:
        hex_line = " ".join(f"{b:02X}" for b in buffer)
        log_line(hex_line)
    print("\nSerial monitoring stopped.")
finally:
    ser.close()
    if log_file:
        log_file.close()
