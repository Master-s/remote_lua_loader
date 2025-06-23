import sys
import select
import socket
import struct
import argparse

signals = {
    4: "SIGILL",
    10: "SIGBUS",
    11: "SIGSEGV",
}

COMMAND_MAGIC = struct.pack('<Q', 0xFFFFFFFF)  # Command magic value in byte form (0xFFFFFFFF)
MAGIC_VALUE = struct.pack('<Q', 0x13371337)  # Magic value in byte form (0x13371337)
MAGIC_VALUE_LEN = len(MAGIC_VALUE)
SIGNAL_LEN = 16
MCONTEXT_LEN = 0x100

DISABLE_SIGNAL_HANDLER = 0
ENABLE_SIGNAL_HANDLER = 1


def print_mcontext(buffer):
    # mcontext_t structure
    fmt = "<QQQQQQQQQQQQQQQQIHHQIHHQQQQQQ"
    
    struct_buf = buffer[:struct.calcsize(fmt)]
    struct_data = struct.unpack(fmt, struct_buf)
    
    regs_name = [
        "onstack", "rdi", "rsi", "rdx", "rcx", 
        "r8", "r9", "rax", "rbx", "rbp", "r10",
        "r11", "r12", "r13", "r14", "r15", "trapno",
        "fs", "gs", "addr", "flags", "es", "ds", "err",
        "rip", "cs", "rflags", "rsp", "ss"
    ]
    
    regs = []
    for name,value in zip(regs_name, struct_data):
        regs.append((name, value))

    print()
    for i in range(1, len(regs), 2):
        print("%5s: %016x  %7s: %016x" % (
            regs[i][0], regs[i][1], regs[i+1][0], regs[i+1][1]
        ))
    print()

def send_command(ip, port, command):    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:        
        sock.connect((ip, int(port)))
        
        sock.sendall(COMMAND_MAGIC + struct.pack("B", command))
        
        process_incoming_data(sock)


def send_payload(ip, port, filepath):
    with open(filepath, "rb") as file:
        data = file.read()
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:        
        sock.connect((ip, port))
        
        # Send size (qword) + <buffer..>
        size = struct.pack("<Q", len(data))   # little endian
        sock.sendall(size + data)
        
        process_incoming_data(sock)

def process_incoming_data(sock):
    buffer = b""
    while True:
        readable, _, _ = select.select([sock], [], [], 1.0)
        if not readable:
            continue

        try:
            chunk = sock.recv(4096)
        except Exception as e:
            print(f"Error receiving data: {e}")
            break

        if not chunk:
            break

        buffer += chunk
        buffer = process_buffer(buffer)

def process_buffer(buffer):
    while True:
        if len(buffer) < MAGIC_VALUE_LEN:
            break

        magic_index = buffer.find(MAGIC_VALUE)
        if magic_index == -1:
            break

        if len(buffer) < magic_index + MAGIC_VALUE_LEN + SIGNAL_LEN + MCONTEXT_LEN:
            break

        start_index = magic_index + MAGIC_VALUE_LEN
        magic_data = buffer[start_index:start_index + SIGNAL_LEN]
        mcontext_data = buffer[start_index + SIGNAL_LEN : start_index + SIGNAL_LEN + MCONTEXT_LEN]

        process_crash_data(buffer[:magic_index], magic_data, mcontext_data)

        buffer = buffer[start_index + SIGNAL_LEN + MCONTEXT_LEN:]

    # Print leftover data if they are not part of signal handling
    magic_index = buffer.find(MAGIC_VALUE)
    if magic_index == -1:
        print(buffer.decode("latin-1"), end="")
        buffer = b""

    return buffer

def process_crash_data(prefix, magic_data, mcontext_data):
    crash_code_data, crash_address_data = struct.unpack("<QQ", magic_data)
    
    crash_code = signals.get(crash_code_data, f"Unknown signal code {crash_code_data}")
    crash_address = f"0x{crash_address_data:016x}"

    print(prefix.decode("latin-1"))
    print(f"{crash_code} at {crash_address}")
    print_mcontext(mcontext_data)

def main():
    parser = argparse.ArgumentParser(description='Send payload to specified target')
    group = parser.add_mutually_exclusive_group()
    
    parser.add_argument('ip', help='Target IP address')
    parser.add_argument('port', type=int, help='Target port number')
    group.add_argument('filepath', nargs='?', help='Path to the payload file')
    group.add_argument('--enable-signal-handler', action='store_true', 
                    help='Enable signal handler (print info in case of crash)')
    group.add_argument('--disable-signal-handler', action='store_true', 
                        help='Disable signal handler (print info in case of crash)')
    
    args = parser.parse_args()
    
    if args.disable_signal_handler:
        send_command(args.ip, args.port, DISABLE_SIGNAL_HANDLER)
    elif args.enable_signal_handler:
        send_command(args.ip, args.port, ENABLE_SIGNAL_HANDLER)
    else:
        send_payload(args.ip, args.port, args.filepath)

if __name__ == "__main__":
    main()