import serial
import struct
import sys

PORT     = "/dev/ttyACM0"
BAUDRATE = 19200

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

def write_register(ser, slave_id, register, value):
    # Function code 0x10 = Write Multiple Registers
    # We write 1 register (2 bytes of data)
    payload = struct.pack('>BBHHB', slave_id, 0x10, register, 1, 2)
    payload += struct.pack('>H', value)
    crc = calc_crc(payload)
    payload += struct.pack('<H', crc)
    ser.write(payload)
    response = ser.read(32)
    return response

def read_register(ser, slave_id, register):
    request = struct.pack('>BBHH', slave_id, 0x03, register, 1)
    crc = calc_crc(request)
    request += struct.pack('<H', crc)
    ser.write(request)
    response = ser.read(32)
    if len(response) >= 5:
        return struct.unpack('>h', response[3:5])[0]
    return None

if len(sys.argv) != 3:
    print("Usage: python assign_slave_id.py <current_id> <new_id>")
    print("Example: python assign_slave_id.py 1 3")
    sys.exit(1)

current_id = int(sys.argv[1])
new_id     = int(sys.argv[2])

if new_id < 1 or new_id > 247:
    print("ERROR: New slave ID must be between 1 and 247. Never use 0.")
    sys.exit(1)

print(f"Connecting to sensor at slave ID {current_id}...")

ser = serial.Serial(
    port     = PORT,
    baudrate = BAUDRATE,
    bytesize = 8,
    parity   = serial.PARITY_EVEN,
    stopbits = 1,
    timeout  = 1.0
)

# Confirm sensor is responding before we change anything
current = read_register(ser, current_id, 48)
print(f"  Current slave ID confirmed: {current}")

if current != current_id:
    print("  WARNING: Sensor response doesn't match expected ID. Aborting.")
    ser.close()
    sys.exit(1)

# Write new slave ID to integer register 48
print(f"  Writing new slave ID: {new_id}...")
response = write_register(ser, current_id, 48, new_id)
print(f"  Raw response: {response.hex()}")

# Verify by reading back from the new ID
import time
time.sleep(0.5)  # small pause to let sensor apply the change
verify = read_register(ser, new_id, 48)
if verify == new_id:
    print(f"  SUCCESS: Sensor now responding at slave ID {new_id}")
else:
    print(f"  WARNING: Could not verify new ID. Got: {verify}")

ser.close()
