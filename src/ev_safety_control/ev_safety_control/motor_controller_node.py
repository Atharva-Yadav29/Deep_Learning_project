import os
# Force the unlocked Ubuntu backend for hardware PWM
os.environ['GPIOZERO_PIN_FACTORY'] = 'pigpio'

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32, Int32, String
from gpiozero import PWMOutputDevice, DigitalOutputDevice
import curses
import threading
import time

class MotorControllerNode(Node):
    def __init__(self):
        super().__init__('motor_controller')
        
        # Hardware Setup (BCM Numbering for TB6612FNG)
        self.pwmb = PWMOutputDevice(18)
        self.bin1 = DigitalOutputDevice(17)
        self.bin2 = DigitalOutputDevice(27)
        
        # System States
        self.throttle = 0.0
        self.current_limit = 100  # Default 100% speed limit
        
        # ROS 2 Communication
        self.create_subscription(Int32, '/system_limit', self.limit_callback, 10)
        self.pwm_pub = self.create_publisher(Float32, '/cmd_pwm', 10)
        self.override_pub = self.create_publisher(String, '/detected_sign', 10) 
        
        self.get_logger().info("Motor Controller Active. Awaiting Keyboard Input.")
        
        # Start the keyboard listener in a separate background thread
        self.keyboard_thread = threading.Thread(target=self.start_curses_loop, daemon=True)
        self.keyboard_thread.start()

    def limit_callback(self, msg):
        self.current_limit = msg.data
        self.get_logger().info(f"Safety Limit Applied: {self.current_limit}%")
        self.update_motor() # Apply the new limit immediately

    def update_motor(self):
        # Calculate actual power based on user throttle and the Safety Manager's limit
        safe_throttle = self.throttle * (self.current_limit / 100.0)
        
        # Set direction (Forward: BIN1=HIGH, BIN2=LOW)
        if safe_throttle > 0:
            self.bin1.on()
            self.bin2.off()
        else:
            self.bin1.off()
            self.bin2.off()
            
        # Drive the PWM pin safely
        self.pwmb.value = safe_throttle
        
        # Broadcast the current active throttle to the Web Dashboard
        pwm_msg = Float32()
        pwm_msg.data = safe_throttle
        self.pwm_pub.publish(pwm_msg)

    def start_curses_loop(self):
        curses.wrapper(self.keyboard_loop)

    def keyboard_loop(self, stdscr):
        stdscr.nodelay(True)
        stdscr.clear()
        stdscr.addstr("EV Motor Controller Active\n")
        stdscr.addstr("Controls: [W] Accelerate | [Space] Brake | [X] Override Restriction\n")
        
        while rclpy.ok():
            try:
                key = stdscr.getch()
                
                if key != -1:
                    if key == ord('w') or key == ord('W'):
                        # Increase throttle in 10% increments
                        self.throttle = min(1.0, self.throttle + 0.1)
                        self.get_logger().info(f"Key W pressed. Throttle requested: {self.throttle:.1f}")
                        self.update_motor()
                        
                    elif key == ord(' '): # Spacebar
                        self.throttle = 0.0
                        self.get_logger().info("Brakes Applied!")
                        self.update_motor()
                        
                    elif key == ord('x') or key == ord('X'):
                        # The Override Trick
                        self.get_logger().info("Manual Override: Tricking Safety Manager to reset limit!")
                        reset_msg = String()
                        reset_msg.data = "Go Straight"
                        self.override_pub.publish(reset_msg)
                        
            except Exception as e:
                pass
            
            # Small sleep to prevent the keyboard loop from hogging the CPU
            time.sleep(0.05)

def main(args=None):
    rclpy.init(args=args)
    node = MotorControllerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()