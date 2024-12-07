
import sys
import socket
import struct
import binascii

def send_payload(ip, port, filepath):
    
    data = open(filepath, "rb").read()
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:        
        sock.connect((ip, int(port)))
        
        # send size (qword) + <buffer..>
        size = struct.pack("<Q", len(data))   # little endian
        sock.sendall(size + data)

        response = []
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response.append(chunk)

            if len(chunk) == 8:
                break

        response = b''.join(response)
        if len(response) == 8:
            crash_address = binascii.hexlify(bytes(reversed(response))).decode('utf-8')
            print(f"SIGSEGV at 0x{crash_address}")
        else:
            print(response.decode("utf-8"))

def main():
    
    if len(sys.argv) != 4:
        print("{} <ps-ip> <port> <filepath>".format(sys.argv[0]))
        return

    ip, port, filepath = sys.argv[1:]
    send_payload(ip, port, filepath)


main()
