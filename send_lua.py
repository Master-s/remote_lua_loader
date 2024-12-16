import sys
import socket
import struct
import binascii

signals = {
    4: "SIGILL",
    10: "SIGBUS",
    11: "SIGSEGV",
}

MAGIC_VALUE = struct.pack('<I', 0x13371337)  # Magic value in byte form (0x13371337)
MAGIC_VALUE_LEN = len(MAGIC_VALUE)
SIGNAL_LEN = 16

def send_payload(ip, port, filepath):
    data = open(filepath, "rb").read()
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:        
        sock.connect((ip, int(port)))
        
        # send size (qword) + <buffer..>
        size = struct.pack("<Q", len(data))   # little endian
        sock.sendall(size + data)

        buffer = b""  # Buffer to accumulate partial data
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            
            buffer += chunk  # Add received chunk to buffer

            while True:
                if len(buffer) < MAGIC_VALUE_LEN:  # Not enough data for magic value
                    break

                # Search for the magic value
                magic_index = buffer.find(MAGIC_VALUE)
                if magic_index == -1:
                    break  # Magic value not found in current buffer

                # Check if we have enough data following the magic value
                if len(buffer) < magic_index + MAGIC_VALUE_LEN + SIGNAL_LEN:  # 4 (magic) + 16 (next bytes)
                    break  # Wait for more data

                # Extract the 16 bytes following the magic value
                start_index = magic_index + MAGIC_VALUE_LEN
                magic_data = buffer[start_index:start_index + SIGNAL_LEN]

                # Handle the magic_data separately
                crash_code_data, crash_address_data = struct.unpack("<QQ", magic_data)
                
                crash_code = signals.get(crash_code_data, f"Unknown signal code {crash_code_data}")
                crash_address = f"0x{crash_address_data:016x}"

                print(buffer[:magic_index].decode("utf-8"), end="")
                print(f"{crash_code} at {crash_address}")
                print(buffer[start_index + SIGNAL_LEN:].decode("utf-8"), end="")

                # Remove processed part from the buffer
                buffer = b""

            # Optional: Process remaining buffer (without magic value) if needed
            if buffer:
                print(buffer.decode("utf-8"), end="")
                buffer = b""

def main():
    if len(sys.argv) != 4:
        print("{} <ps-ip> <port> <filepath>".format(sys.argv[0]))
        return

    ip, port, filepath = sys.argv[1:]
    send_payload(ip, port, filepath)

if __name__ == "__main__":
    main()
