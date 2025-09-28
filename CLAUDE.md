# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

RoverPylot is a Python API and demo program for controlling Brookstone Rover 2.0 and Rover Revolution spy vehicles from a computer using a PS3 controller. The project enables remote control and live video streaming from these robotic vehicles.

## Common Development Commands

### Installation and Setup
```bash
# Install the package
sudo python setup.py install

# Install dependencies
pip install -r requirements.txt
```

### Running Demo Scripts
```bash
# Control Rover 2.0 (requires OpenCV and PS3 controller)
python ps3rover20.py

# Control Rover Revolution (requires ffmpeg and PS3 controller)  
python ps3revolution.py

# Test battery level (Rover 2.0 only)
python rover20battery.py

# Test audio capture (Rover 2.0 only)
python rover20shout.py

# Test computer vision features
python cv_revolution.py
```

### Dependencies
- **Required**: pygame (for PS3 controller input)
- **Rover 2.0**: OpenCV for Python (cv2) for JPEG video processing
- **Rover Revolution**: ffmpeg for H.264 video decoding and playback
- **Optional**: numpy for advanced processing

## Code Architecture

### Core Classes (`rover/__init__.py`)

#### `Rover` (Base Class)
- Handles network communication with rover (192.168.1.100:80)
- Manages Blowfish encryption for authentication
- Provides base video/audio streaming infrastructure
- Implements keep-alive mechanism and camera controls

#### `Rover20` (Rover 2.0 Implementation)
- Extends `Rover` for tank-style movement with left/right treads
- Processes JPEG video frames via `processVideo(jpegbytes, timestamp_10msec)`
- Handles ADPCM audio via `processAudio(pcmsamples, timestamp_10msec)`
- Supports headlights, infrared mode, and vertical camera movement

#### `Revolution` (Rover Revolution Implementation) 
- Extends `Rover` for car-style movement with steering
- Processes H.264 video frames via `processVideo(imgbytes, timestamp_msec)`
- Supports dual cameras (driving/turret) with horizontal/vertical movement
- Uses different timestamp format (milliseconds vs 10ms units)

### Demo Applications

#### `PS3Rover` Classes
- Subclass respective rover classes to add PS3 controller integration
- Override `processVideo()` and `processAudio()` methods for display/processing
- Implement controller mapping for movement, camera, lights, and mode switching

### Supporting Modules

- `blowfish.py`: Custom Blowfish encryption (P-arrays zeroed instead of Pi digits)  
- `adpcm.py`: ADPCM to PCM audio decoder for Rover 2.0
- `byteutils.py`: Byte manipulation utilities for network protocol

## Network Protocol

- Rovers create ad-hoc WiFi networks that you join from your computer
- Communication uses custom binary protocol over TCP sockets
- Authentication via modified Blowfish encryption with camera ID as key component
- Separate command and media socket connections
- Media frames identified by 'MO_V' header signature

## Hardware Integration

### Controller Mapping (Customizable)
- **Rover 2.0**: Left/right stick Y-axes control treads independently (tank mode)
- **Revolution**: Right stick controls drive/steer, left stick controls turret camera
- Button mappings for lights, infrared mode, camera switching

### Video Processing
- **Rover 2.0**: Real-time JPEG frame display via OpenCV
- **Revolution**: H.264 frames saved to temp file, played via ffplay subprocess

## Development Notes

- The codebase supports both Python 2.7 and Python 3.x
- Video display implementations differ significantly between rover models
- Revolution video has known blurring issues due to H.264 workaround approach
- Controller axis/button IDs may need adjustment for third-party PS3 controllers
- Windows compatibility requires specific ffmpeg path and temp file handling modifications