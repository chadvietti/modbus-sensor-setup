import serial
import struct
import sys

PORT     = "/dev/ttyACM0"
BAUDRATE = 19200
SLAVE_ID = int(sys.argv[1]) if len(sys.argv) > 1 else 1

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

def read_register(ser, slave_id, register):
    request = struct.pack('>BBHH', slave_id, 0x03, register, 1)
    crc = calc_crc(request)
    request += struct.pack('<H', crc)
    ser.write(request)
    response = ser.read(32)
    print(f"  Raw response: {response.hex()}")
    if len(response) >= 5:
        value = struct.unpack('>h', response[3:5])[0]
        return value
    return None

print(f"Connecting to slave ID {SLAVE_ID} on {PORT}...")
ser = serial.Serial(
    port     = PORT,
    baudrate = BAUDRATE,
    bytesize = 8,
    parity   = serial.PARITY_EVEN,
    stopbits = 1,
    timeout  = 1.0
)

raw = read_register(ser, SLAVE_ID, 40)
if raw is not None:
    print(f"  Raw value    : {raw}")
    print(f"  ePAR reading : {raw * 0.1:.1f} µmol m⁻² s⁻¹")

ser.close()
