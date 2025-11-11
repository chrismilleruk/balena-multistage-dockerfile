# Current Devices

## Industrial USB to RS485 Converter Adapter (CH343G + SP485EEN)

**Brand:** Waveshare  
**Model:** USB to RS485 Converter B  
**ASIN:** B0B87D9LNC

### Key Features
- **Industrial grade** USB to RS485 bidirectional converter
- **Chips:** Onboard original CH343G (USB bus adapter) and SP485EEN
- **Multi-protection:** Built-in lightningproof tube, resettable fuse, ESD and TVS protection circuits
- **Transmission distance:**  
  - RS485 up to 1.2km  
  - USB up to 5m
- **Reliable speed:** 300bps ~ 3Mbps
- **Operating voltage:** 5V USB
- **Current rating:** 0.3A
- **LED indicators:** 3 LEDs for power and transceiver status
- **System compatibility:** Mac, Linux, Android, WinCE, Windows 11/10/8.1/8/7/XP
- **Automatic direction control; supports point-to-multipoints (up to 32 nodes)**
- **Connector type:** USB Type A, RS485 screw terminal (A+, B-, GND)

### Package Content
- 1x USB to RS485 (B)
- 1x USB-A male to female cable
- 1x Screwdriver

### Physical Details
- **Dimensions:** 5.3 x 2.4 x 1.5 cm
- **Weight:** 0.07 kg
- **Number of Ports:** 2

### Safety & Standards
- Over-current, over-voltage, surge, and shock resistant design  
- Onboard 120Ω balancing resistor

### Customer Ratings
- **Average Rating:** 4.6 out of 5 (225 ratings)
  - 76% ⭐⭐⭐⭐⭐
  - 17% ⭐⭐⭐⭐

### Additional Info
- **First Available:** November 2024
- **Best Sellers Rank:** #17 in Serial Adapters (Amazon IE Electronics)
- **Warranty:** 30-day hassle-free returns (Amazon)

### Notable Reviews
- Works out of the box with Raspberry Pi 4 (Home Assistant)
- Stable operation with Modscan32 (Windows 11 Pro)
- Well suited for industrial/agricultural RS485 use

### Resources
- [Waveshare Wiki / Dev Resources](https://www.waveshare.com/wiki/USB_TO_RS485_(B)?amazon)


## RS485 Temperature Receiver for DS18B20 MODBUS – Development Reference

**Model:** R4DCB08 8Bit RS485 Temperature Receiver  
**Brand:** DONGKER  
**ASIN:** B09H6LCFFP

---

### Hardware Specifications

- **Voltage Range:** DC 6V–24V (typical 12V/24V supported)
- **Current Consumption:** 8–13 mA
- **Dimensions:** 70 × 46 × 18 mm
- **Operating Temperature:** -40°C ~ 80°C
- **Operating Humidity:** 10% ~ 90% RH (non-condensing)
- **Sensor Input:** Supports up to 8 × DS18B20 sensors (1-Wire, *not included*)
- **Temperature Measurement Range:** -55°C ~ 125°C
- **Accuracy:** ±1%

---

### Communication Interface

- **Bus Type:** RS485
- **Protocol:** MODBUS RTU
    - Supported MODBUS commands: `03` (Read Holding Registers), `06` (Write Single Register)
    - Maximum parallel devices: 247
- **UART/AT Command Support:** Contact seller post-purchase for full AT/UART documentation

---

### Electrical Pinout

| Pin | Description       |
|-----|------------------|
| V+  | DC Power (6–24V) |
| GND | Ground           |
| A   | RS485 Data (+)   |
| B   | RS485 Data (-)   |

---

### Software Integration

- **Standard MODBUS RTU libraries compatible**
- **Typical workflow:**
    1. Power module with DC 12V or 24V
    2. Connect up to 8 DS18B20 sensors (sensor address assignment per manufacturer specs)
    3. Wire RS485 A/B to host controller or PLC
    4. Query temperature values over MODBUS [function 03]
    5. Interpret 8-bit temperature results returned per sensor

---

#### Example MODBUS Request (Function 03)


## HALJIA DS18B20 Waterproof Temperature Sensors (Pack of 5) – Developer Reference

**Model/Part:** ADN2103011  
**ASIN:** B092ZHRQ3T  
**Brand:** HALJIA

---

### Hardware Specifications

- **Sensor Chip:** DS18B20 (digital, programmable)
- **Wire Length:** 1 metre (PVC insulated, waterproof)
- **Probe Size:** 6 × 50 mm, Stainless steel
- **Operating Voltage:** 3.0–5.5V DC
- **Temperature Range:** -55°C to +125°C
- **Accuracy:** ±0.5°C (from -10°C to +85°C)
- **Resolution:** Programmable, 9–12 bits
- **Output:** Digital 1-Wire (no external components needed)

---

### Electrical Pinout

- **Red:** VCC (3.0–5.5V)
- **Yellow:** Data (1-Wire)
- **Black:** GND

All pins are sealed and isolated with heat-shrink tubing for robust insulation and safety.

---

### Application & Integration

- Direct digital readout, no ADC/interfacing required
- 1-Wire protocol compatible with Arduino, Raspberry Pi, ESP32, PLCs, MODBUS temperature receivers, etc.
- Sensors are waterproof, high temperature, moisture, and rust resistant for indoor/outdoor and harsh conditions

---

#### Typical Applications

- Thermostatic control systems
- Industrial/process monitoring
- Environmental monitoring (cold storage, telecom rooms, aquaculture, greenhouses)
- Home automation, HVAC
- DIY temperature logging (Raspberry Pi, Arduino, ESP32, etc.)

---

#### Quick Wiring Guide

1. Connect Red to VCC (3.0–5.5V DC)
2. Connect Black to GND
3. Connect Yellow to MCU GPIO pin (use 4.7kΩ pull-up resistor to VCC for reliable 1-Wire communication)

---

#### Example Arduino Initialization



# Reserved for Future Expansion

## Waveshare 7.5" E-Paper Display HAT V2 – Development Reference

**Model:** 7.5inch e-Paper HAT V2  
**ASIN:** B075R4QY3L  
**Brand:** Waveshare

---

### Display Specifications

- **Screen Size:** 7.5 inches
- **Resolution:** 800 × 480 pixels (upgraded V2 revision)
- **Color:** Black & White
- **Dot Pitch:** 0.205 × 0.204 mm
- **Display Size:** 163.2 × 97.9 mm
- **Outline Dimension:** 170.2 × 111.2 mm
- **Gray Levels:** 2 (monochrome)
- **Viewing Angle:** >170°
- **No Backlight:** Image retained when powered down

---

### Electrical & Interface

- **Operating Voltage:** 3.3V–5V (onboard voltage translator for MCU compatibility)
- **Connectivity:** SPI interface (standard Raspberry Pi 40PIN GPIO header)
- **Supported Boards:** Raspberry Pi series, Jetson Nano, Arduino, STM32, Nucleo
- **Full Refresh Time:** ~5 seconds
- **Power Consumption:**  
    - Refresh: 38mW (typical)  
    - Standby: <0.017mW  
    - Ultra low power, only required when refreshing

---

### Features & Notes

- Integrated controller with SPI for easy MCU connection
- Keeps last image with no power; ideal for applications needing persistent display with minimal consumption


## JZK TTL to RS485 Modules (5PCS) – Developer Reference

**Model:** TTL to RS485  
**ASIN:** B09VGJCJKQ  
**Brand:** JZK

---

### Purpose & Functionality

- Converts TTL-level UART (3.3V/5V) to RS485 signal and vice versa
- Enables microcontrollers (Arduino, ESP32, Raspberry Pi, etc.) to communicate over RS485 bus
- Hardware automatic flow control: no need for explicit RE/DE control in code
- Plug and play—operate as a regular serial port device

---

### Hardware Specifications

- **Operating Voltage:** 3.3V or 5.0V (compatible with both logic levels)
- **Transmission Distance:** up to 1000 meters (recommended up to 800 meters for best stability; use repeaters beyond this)
- **Features:**  
    - RXD, TXD signal indicator LEDs for transmit/receive monitoring  
    - Robust anti-interference and lightning protection design  
    - Industrial-grade for field/harsh environments  
    - 120 ohm matching resistor; short R0 for matching, especially for long runs  
    - Standard 2.54 mm pin headers for easy breadboard/PCB development

---

### Pinout & Connectivity

| Pin | Description           |
|-----|-----------------------|
| VCC | 3.3V or 5V input      |
| GND | Ground                |
| TXD | UART transmit from MCU|
| RXD | UART receive to MCU   |
| A   | RS485 A (non-inverting) |
| B   | RS485 B (inverting)   |
| GND | Earth terminal (optional; connect for extra noise immunity in long distance/field
