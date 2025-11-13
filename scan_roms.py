#!/usr/bin/env python3
"""
scan_roms.py
Small MODBUS holding-register scanner that looks for DS18B20 ROM codes (8 bytes)
exposed across consecutive 16-bit holding registers. It validates the Dallas CRC8
and prints candidate ROMs and the register base where they were found.

Run on host or on device (use SERIAL_PORT and other env vars or flags).
"""

import argparse
import sys
import time
import os
from pymodbus.client import ModbusSerialClient


# Dallas CRC8 for 1-Wire ROM verification
def dallas_crc8(data: bytes) -> int:
    crc = 0
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x01:
                crc = (crc >> 1) ^ 0x8C
            else:
                crc >>= 1
    return crc


def parse_regs_to_roms(regs, registers_per_sensor=4, order_within_reg='big'):
    roms = []
    for i in range(0, len(regs), registers_per_sensor):
        chunk = regs[i:i+registers_per_sensor]
        if len(chunk) < registers_per_sensor:
            break
        b = bytearray()
        for reg in chunk:
            high = (reg >> 8) & 0xFF
            low = reg & 0xFF
            if order_within_reg == 'big':
                b.append(high)
                b.append(low)
            else:
                b.append(low)
                b.append(high)
        rom = bytes(b[:8])
        roms.append(rom)
    return roms


def scan(client, start, end, step=32, registers_per_sensor=4, unit=1):
    found = {}
    for block_start in range(start, end, step):
        count = min(step, end - block_start)
        try:
            # Use the same keyword as temp_monitor.py for compatibility across pymodbus versions
            # Some versions expect 'device_id' instead of 'unit'
            rr = client.read_holding_registers(block_start, count=count, device_id=unit)
            if not rr or getattr(rr, "isError", lambda: False)():
                time.sleep(0.02)
                continue
            regs = rr.registers
        except Exception as e:
            print(f"Read error at {block_start}: {e}", file=sys.stderr)
            time.sleep(0.02)
            continue

        for order in ('big', 'little'):
            roms = parse_regs_to_roms(regs, registers_per_sensor, order_within_reg=order)
            for idx, rom in enumerate(roms):
                if len(rom) < 8:
                    continue
                fam = rom[0]
                crc_ok = (dallas_crc8(rom[:7]) == rom[7])
                if fam == 0x28 and crc_ok:
                    reg_index = block_start + idx * registers_per_sensor
                    print(f"Candidate ROM at regs {reg_index} (order={order}): {rom.hex()} CRC OK")
                    found.setdefault(reg_index, []).append((order, rom.hex()))
                else:
                    if fam == 0x28:
                        reg_index = block_start + idx * registers_per_sensor
                        print(f"Family 0x28 but CRC FAIL at regs {reg_index} (order={order}): {rom.hex()} crc={rom[7]:02x} expected={dallas_crc8(rom[:7]):02x}")

    return found


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', default=os.getenv('SERIAL_PORT', '/dev/ttyACM0'))
    parser.add_argument('--baud', type=int, default=int(os.getenv('BAUDRATE', '9600')))
    parser.add_argument('--unit', type=int, default=int(os.getenv('MODBUS_ADDRESS', '1')))
    parser.add_argument('--start', type=int, default=0)
    parser.add_argument('--end', type=int, default=400)
    parser.add_argument('--step', type=int, default=64)
    parser.add_argument('--registers-per-sensor', type=int, default=int(os.getenv('ROM_REGISTERS_PER_SENSOR', '4')))
    args = parser.parse_args()

    print(f"Scanning {args.port} baud={args.baud} unit={args.unit} registers {args.start}..{args.end} step={args.step}")

    # Construct ModbusSerialClient with same params used in temp_monitor.py
    # Some pymodbus versions expect port/baudrate/parity/stopbits/bytesize instead of 'method'
    parity = os.getenv('PARITY', 'N')
    stopbits = int(os.getenv('STOPBITS', '1'))
    bytesize = int(os.getenv('BYTESIZE', '8'))
    client = ModbusSerialClient(
        port=args.port,
        baudrate=args.baud,
        parity=parity,
        stopbits=stopbits,
        bytesize=bytesize,
        timeout=1
    )
    if not client.connect():
        print(f"Failed to open {args.port}", file=sys.stderr)
        sys.exit(2)

    try:
        results = scan(client, args.start, args.end, step=args.step, registers_per_sensor=args.registers_per_sensor, unit=args.unit)
        if not results:
            print("No candidate ROMs found in scanned range.")
        else:
            print("Scan complete. Candidate ROMs printed above.")
    finally:
        client.close()


if __name__ == '__main__':
    main()
