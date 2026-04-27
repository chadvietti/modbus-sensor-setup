import serial
import struct
import csv
import time
from datetime import datetime

# ── Config ──────────────────────────────────────────
PORT        = "/dev/ttyACM0"
BAUDRATE    = 19200
SLAVE_IDS   = [7, 8, 9, 10, 11, 12]
INTERVAL    = 60        # seconds between readings
RAW_CSV     = "epar_raw.csv"
# ────────────────────────────────────────────────────

def calc_crc(data):
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc

def read_epar(ser, slave_id):
    request = struct.pack('>BBHH', slave_id, 0x03, 40, 1)
    crc = calc_crc(request)
    request += struct.pack('<H', crc)
    ser.write(request)
    time.sleep(0.1)
    response = ser.read(32)
    if len(response) >= 5:
        raw = struct.unpack('>h', response[3:5])[0]
        return round(raw * 0.1, 1)
    return None

def write_header_if_needed(filename):
    try:
        with open(filename, 'r'):
            pass
    except FileNotFoundError:
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            header = ['timestamp'] + [f'sensor_{i}' for i in SLAVE_IDS]
            writer.writerow(header)

write_header_if_needed(RAW_CSV)

print(f"Starting ePAR collection — sensors {SLAVE_IDS}, every {INTERVAL}s")
print(f"Logging to: {RAW_CSV}")
print("Press Ctrl+C to stop.\n")

ser = serial.Serial(
    port=PORT, baudrate=BAUDRATE,
    bytesize=8, parity=serial.PARITY_EVEN,
    stopbits=1, timeout=1.0
)

try:
    while True:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        readings = []
        row_display = [timestamp]

        for sid in SLAVE_IDS:
            val = read_epar(ser, sid)
            readings.append(val)
            row_display.append(f"S{sid}={val if val is not None else 'ERR'}")
            time.sleep(0.05)   # small gap between sensors on the bus

        with open(RAW_CSV, 'a', newline='') as f:
            csv.writer(f).writerow([timestamp] + readings)

        print("  ".join(row_display))

        # Sleep until the next 60-second mark
        next_tick = (time.time() // INTERVAL + 1) * INTERVAL
        time.sleep(max(0, next_tick - time.time()))

except KeyboardInterrupt:
    print("\nStopped.")
finally:
    ser.close()
