import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Bool

class SafetyManager(Node):
    def __init__(self):
        super().__init__('safety_manager')
        self.current_pwm_limit = "100% (Normal)"
        self.horn_enabled = True

        self.sign_sub = self.create_subscription(String, '/detected_sign', self.sign_callback, 10)
        self.reset_sub = self.create_subscription(Bool, '/driver_reset', self.reset_callback, 10)

        self.get_logger().info('SAFETY MANAGER: Terminal Logic Node Started')
        self.display_status()

    def sign_callback(self, msg):
        sign = msg.data.lower()
        if 'speed_' in sign:
            try:
                new_limit = sign.split('_')[1]
                self.current_pwm_limit = f"{new_limit}% (RESTRICTED)"
            except (IndexError, ValueError):
                self.get_logger().error('Invalid speed format!')
        elif 'no_horn' in sign:
            self.horn_enabled = False
        self.display_status()

    def reset_callback(self, msg):
        if msg.data is True:
            self.current_pwm_limit = "100% (Normal)"
            self.horn_enabled = True
            self.get_logger().warn('DRIVER INTERRUPT: Resetting to 100%')
            self.display_status()

    def display_status(self):
        status = "ENABLED" if self.horn_enabled else "DISABLED"
        self.get_logger().info(f'\n--- STATE ---\nPWM: {self.current_pwm_limit}\nHorn: {status}\n-----------')

def main(args=None):
    rclpy.init(args=args)
    node = SafetyManager()
    rclpy.spin(node)
    rclpy.shutdown()