import serial
import time

class ScaleInterface:
    def __init__(self, port='COM1', baudrate=9600):
        self.port = port
        self.baudrate = baudrate
        self.serial = None
        self.connect()
        
    def connect(self):
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1
            )
            print(f"Connected to scale on {self.port}")
        except serial.SerialException as e:
            print(f"Failed to connect to scale: {e}")
            self.serial = None
            
    def get_weight(self):
        if not self.serial or not self.serial.is_open:
            self.connect()
            if not self.serial:
                return 0.0
                
        try:
            # Send command to request weight
            self.serial.write(b'W\r\n')
            time.sleep(0.1)  # Wait for response
            
            # Read response
            response = self.serial.readline().decode('ascii').strip()
            
            # Parse weight value
            try:
                weight = float(response)
                return weight
            except ValueError:
                print(f"Invalid weight response: {response}")
                return 0.0
                
        except serial.SerialException as e:
            print(f"Error reading from scale: {e}")
            self.serial = None
            return 0.0
            
    def __del__(self):
        if self.serial and self.serial.is_open:
            self.serial.close() 