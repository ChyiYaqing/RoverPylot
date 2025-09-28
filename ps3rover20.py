#!/usr/bin/env python3

'''
ps3rover20.py Drive the Brookstone Rover 2.0 via the P3 Controller, displaying
the streaming video using OpenCV.

Copyright (C) 2014 Simon D. Levy

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as 
published by the Free Software Foundation, either version 3 of the 
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
'''

from rover import Rover20
import time
import pygame
import sys
import signal
import numpy as np
from typing import Optional

# Controller configuration - adjust these for your specific controller
BUTTON_LIGHTS = 3       # Square button toggles lights
BUTTON_STEALTH = 1      # Circle button toggles stealth mode
BUTTON_CAMERA_UP = 0    # Triangle button raises camera
BUTTON_CAMERA_DOWN = 2  # X button lowers camera

# Timing and sensitivity configuration
MIN_BUTTON_LAG_SEC = 0.5  # Debounce delay between button presses
MIN_AXIS_ABSVAL = 0.01    # Dead zone for analog sticks


# Enhanced signal handler with cleanup
def _signal_handler(sig, frame):
    """Handle CTRL-C gracefully with proper cleanup."""
    print("\nShutting down rover...")
    rover = frame.f_globals.get('rover')
    if rover:
        rover.cleanup()
        rover.close()
    sys.exit(0)

# Try to start OpenCV for video
try:
    import cv2
except ImportError:
    cv2 = None
    print("Warning: OpenCV not available. Video display will be disabled.")

# Rover subclass for PS3 + OpenCV
class PS3Rover(Rover20):
    """Enhanced PS3 controller interface for Rover 2.0 with modern OpenCV support."""
    
    def __init__(self):
        # Set up basics
        super().__init__()
        self.wname = 'Rover 2.0: Hit ESC to quit'
        self.quit = False
        
        # Set up controller using PyGame
        pygame.display.init()
        pygame.joystick.init()
        
        if pygame.joystick.get_count() == 0:
            raise RuntimeError("No joystick/controller detected. Please connect a PS3 controller.")
            
        self.controller = pygame.joystick.Joystick(0)
        self.controller.init()
        
        # Defaults on startup: lights off, ordinary camera
        self.lights_are_on = False
        self.stealth_is_on = False
        
        # Tracks button-press times for debouncing
        self.last_button_time = 0
        
        # Create OpenCV window if available
        self.video_enabled = False
        if cv2 is not None:
            try:
                cv2.namedWindow(self.wname, cv2.WINDOW_AUTOSIZE)
                self.video_enabled = True
            except cv2.error as e:
                print(f"Warning: Could not create OpenCV window: {e}")
        
        # Use context manager for PCM file
        self.pcm_file: Optional[object] = None
        try:
            self.pcm_file = open('rover20.pcm', 'w')
        except IOError as e:
            print(f"Warning: Could not create PCM file: {e}")

    def processAudio(self, pcmsamples, timestamp_10msec):
        """Process audio samples from the rover.
        
        Args:
            pcmsamples: List of PCM audio samples
            timestamp_10msec: Timestamp in 10ms units (unused but kept for API compatibility)
        """
        if self.pcm_file:
            try:
                for samp in pcmsamples:
                    self.pcm_file.write(f'{samp}\n')
            except IOError:
                pass  # Continue if file write fails

    def processVideo(self, jpegbytes, timestamp_10msec):
        """Process video frames from the rover and handle controller input.
        
        Args:
            jpegbytes: JPEG image data from rover
            timestamp_10msec: Timestamp in 10ms units (unused but kept for API compatibility)
        """
        # Update controller events
        pygame.event.pump()
        
        # Toggle lights
        self.lights_are_on = self._check_button(
            self.lights_are_on, BUTTON_LIGHTS, 
            self.turnLightsOn, self.turnLightsOff
        )
        
        # Toggle night vision (infrared camera)
        self.stealth_is_on = self._check_button(
            self.stealth_is_on, BUTTON_STEALTH, 
            self.turnStealthOn, self.turnStealthOff
        )
        
        # Move camera up/down
        if self.controller.get_button(BUTTON_CAMERA_UP):
            self.moveCameraVertical(1)
        elif self.controller.get_button(BUTTON_CAMERA_DOWN):
            self.moveCameraVertical(-1)
        else:
            self.moveCameraVertical(0)
        
        # Set treads based on axes
        self.setTreads(self._get_axis_value(1), self._get_axis_value(3))
        
        # Display video image if possible
        if self.video_enabled and cv2 is not None:
            try:
                # Decode JPEG bytes directly in memory
                nparr = np.frombuffer(jpegbytes, np.uint8)
                image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                if image is not None:
                    # Show image
                    cv2.imshow(self.wname, image)
                    key = cv2.waitKey(1) & 0xFF
                    if key == 27:  # ESC key
                        self.quit = True
                        
            except (cv2.error, ValueError) as e:
                print(f"Video processing error: {e}")
        
        
    def _get_axis_value(self, index: int) -> int:
        """Convert axis coordinate to normalized direction value."""
        value = -self.controller.get_axis(index)
        
        if value > MIN_AXIS_ABSVAL:
            return 1
        elif value < -MIN_AXIS_ABSVAL:
            return -1
        else:
            return 0


    def _check_button(self, flag: bool, button_id: int, 
                     on_routine=None, off_routine=None) -> bool:
        """Handle button press with debouncing logic."""
        if self.controller.get_button(button_id):
            current_time = time.time()
            if (current_time - self.last_button_time) > MIN_BUTTON_LAG_SEC:
                self.last_button_time = current_time
                if flag:
                    if off_routine:
                        off_routine()
                    return False
                else:
                    if on_routine:
                        on_routine()
                    return True
        return flag
    
    def cleanup(self):
        """Clean up resources."""
        if self.pcm_file:
            try:
                self.pcm_file.close()
            except IOError:
                pass
        
        if self.video_enabled and cv2 is not None:
            cv2.destroyAllWindows()
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        self.cleanup()
        
def main():
    """Main function to run the PS3 Rover controller."""
    rover = None
    try:
        # Create a PS3 Rover object
        rover = PS3Rover()
        print(f"Connected to controller: {rover.controller.get_name()}")
        print("Controls:")
        print("  Left/Right sticks: Move treads")
        print("  Triangle/X: Camera up/down")
        print("  Square: Toggle lights")
        print("  Circle: Toggle infrared")
        print("  ESC key in video window: Quit")
        print("  Ctrl+C: Emergency stop")
        
        # Set up signal handler for CTRL-C
        signal.signal(signal.SIGINT, _signal_handler)
        
        # Main control loop with small sleep to prevent busy waiting
        while not rover.quit:
            time.sleep(0.01)  # 100 FPS max, reduces CPU usage
            
    except RuntimeError as e:
        print(f"Error: {e}")
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1
    finally:
        # Clean shutdown
        if rover:
            rover.cleanup()
            rover.close()
        print("Rover connection closed.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
