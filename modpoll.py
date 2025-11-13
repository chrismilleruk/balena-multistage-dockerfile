#!/usr/bin/env python3
"""
modpoll.py
Lightweight Python replacement for `modpoll` using pymodbus to dump holding registers.

Usage examples:
  python3 modpoll.py --port /dev/ttyACM0 --baud 9600 --unit 1 --start 0 --count 64

Prints register index, decimal and hex values.
"""
import argparse
import sys
import os
from pymodbus.client import ModbusSerialClient


def main():
    parser = argparse.ArgumentParser(description='Simple modpoll replacement using pymodbus')
    parser.add_argument('--port', default=os.getenv('SERIAL_PORT', '/dev/ttyACM0'))
    parser.add_argument('--baud', type=int, default=int(os.getenv('BAUDRATE', '9600')))
    parser.add_argument('--unit', type=int, default=int(os.getenv('MODBUS_ADDRESS', '1')))
    parser.add_argument('--start', type=int, default=0)
    parser.add_argument('--count', type=int, default=64)
    parser.add_argument('--parity', default=os.getenv('PARITY', 'N'))
    parser.add_argument('--stopbits', type=int, default=int(os.getenv('STOPBITS', '1')))
    parser.add_argument('--bytesize', type=int, default=int(os.getenv('BYTESIZE', '8')))
    parser.add_argument('--function', type=int, default=3, help='MODBUS function code: 3=holding registers, 4=input registers')
    args = parser.parse_args()

    client = ModbusSerialClient(port=args.port, baudrate=args.baud, parity=args.parity,
                                stopbits=args.stopbits, bytesize=args.bytesize, timeout=1)
    if not client.connect():
        print(f"ERROR: Failed to open serial port {args.port}")
        sys.exit(2)

    try:
        regs = []
        base = args.start
        remaining = args.count
        
        # Read in chunks of max 125 (MODBUS limit)
        max_per_read = 125
        func_name = "input_registers" if args.function == 4 else "holding_registers"
        read_func = client.read_input_registers if args.function == 4 else client.read_holding_registers
        
        while remaining > 0:
            chunk_size = min(max_per_read, remaining)
            try:
                rr = read_func(base + len(regs), count=chunk_size, device_id=args.unit)
                if not rr or getattr(rr, 'isError', lambda: False)():
                    print(f"Read error at register {base + len(regs)} (func {args.function}): {rr}")
                    break
                regs.extend(rr.registers)
            except Exception as e:
                print(f"Exception reading at register {base + len(regs)}: {type(e).__name__}: {e}")
                break
            remaining -= chunk_size
        
        if not regs:
            print(f"No data read from {func_name} (function {args.function})")
            return
        
        # Print all registers
        for i, val in enumerate(regs):
            idx = base + i
            print(f"{idx:5d}: {val:6d}  0x{val:04X}")

    except Exception as e:
        print(f"Fatal error: {type(e).__name__}: {e}")
    finally:
        client.close()


if __name__ == '__main__':
    main()
