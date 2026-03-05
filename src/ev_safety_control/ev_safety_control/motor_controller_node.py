import os
from gpiozero import Device
from gpiozero.pins.mock import MockFactory, MockPWMPin

# Mock factory for your G15
Device.pin_factory = MockFactory(pin_class=MockPWMPin)

import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Bool, Float32
import curses
from gpiozero import PWMOutputDevice, DigitalOutputDevice

class MotorController(Node):
    def __init__(self, stdscr):
        super().__init__('motor_controller')
        self.stdscr = stdscr
        self.pwm_pub = self.create_publisher(Float32, '/cmd_pwm', 10)
        
        # Pins for TB6612FNG
        self.motor_pwm = PWMOutputDevice(18)
        self.in1 = DigitalOutputDevice(17)
        self.in2 = DigitalOutputDevice(27)
        
        self.current_throttle = 0.0
        self.pwm_limit = 1.0
        
        # --- ADDED RESET SUBSCRIPTION ---
        self.create_subscription(String, '/detected_sign', self.safety_cb, 10)
        self.create_subscription(Bool, '/driver_reset', self.reset_cb, 10)
        
        # Curses setup
        curses.curs_set(0)
        self.stdscr.nodelay(True)
        self.stdscr.timeout(100) 

    def safety_cb(self, msg):
        if 'speed_' in msg.data.lower():
            self.pwm_limit = int(msg.data.split('_')[1]) / 100.0
            self.get_logger().info(f'Speed Limit Active: {self.pwm_limit * 100}%')

    # --- ADDED RESET CALLBACK ---
    def reset_cb(self, msg):
        if msg.data is True:
            self.pwm_limit = 1.0
            self.get_logger().info('Driver Overrode Safety: Limit Reset to 100%')

    def run_loop(self):
        while rclpy.ok():
            key = self.stdscr.getch()
            
            if key == ord('w'):
                self.current_throttle = min(self.current_throttle + 0.1, self.pwm_limit)
                self.get_logger().info(f'Key W pressed. Throttle: {self.current_throttle}')
            elif key == ord('s'):
                self.current_throttle = max(self.current_throttle - 0.1, 0.0)
                self.get_logger().info(f'Key S pressed. Throttle: {self.current_throttle}')
            elif key == ord(' '):
                self.current_throttle = 0.0
                self.get_logger().info('Emergency Brake!')

            # Publishing the value
            msg_out = Float32()
            msg_out.data = float(self.current_throttle)
            self.pwm_pub.publish(msg_out)

            # Hardware Update
            if self.current_throttle > 0:
                self.in1.on(); self.in2.off()
                self.motor_pwm.value = self.current_throttle
            else:
                self.in1.off(); self.in2.off()
                self.motor_pwm.value = 0.0

            rclpy.spin_once(self, timeout_sec=0)

def main(args=None):
    rclpy.init(args=args)
    curses.wrapper(lambda stdscr: MotorController(stdscr).run_loop())
    rclpy.shutdown()