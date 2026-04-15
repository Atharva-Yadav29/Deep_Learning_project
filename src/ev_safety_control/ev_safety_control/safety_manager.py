import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Int32
import re
from collections import deque

class SafetyManager(Node):
    def __init__(self):
        super().__init__('safety_manager')
        
        self.create_subscription(String, '/detected_sign', self.sign_callback, 10)
        self.limit_pub = self.create_publisher(Int32, '/system_limit', 10)
        self.warning_pub = self.create_publisher(String, '/dashboard_warning', 10)
        
        self.current_limit = 100
        
        # --- The Sliding Window (For AI Noise) ---
        self.sign_buffer = deque(maxlen=5) 
        self.required_votes = 3            
        
        self.hazard_signs = [
            'Danger Ahead', 'Deer Zone', 'Pedestrian', 
            'Road Work', 'Slippery Road', 'Snow Warning Sign',
            'Left Curve Ahead', 'Right Curve Ahead', 
            'Left Sharp Curve', 'Right Sharp Curve',
            'Traffic Signals Ahead','Turn Left','Turn Right'
        ]

    def sign_callback(self, msg):
        sign = msg.data
        
        # --- THE FIX: INSTANT OVERRIDE BYPASS ---
        # If it's a reset command, bypass the voting system entirely!
        if sign == 'End of Right Road -Go straight-' or sign == 'Go Straight':
            self.sign_buffer.clear()  # Wipe the memory so old signs don't immediately re-trigger
            if self.current_limit != 100:
                self.current_limit = 100
                limit_msg = Int32()
                limit_msg.data = self.current_limit
                self.limit_pub.publish(limit_msg)
                self.get_logger().info("Manual Override. Limit instantly reset to 100%.")
            return  # Exit the function right here so it doesn't go into the voting buffer!

        # --- NORMAL OPERATION (For AI Signs) ---
        # 1. Add noisy AI signs to the rolling memory buffer
        self.sign_buffer.append(sign)
        
        # 2. Count votes
        votes = self.sign_buffer.count(sign)
        
        if votes < self.required_votes:
            return 
            
        # 3. Handle Speed Limits
        if "Speed Limit" in sign:
            match = re.search(r'\d+', sign)
            if match:
                new_limit = int(match.group())
                if new_limit != self.current_limit:
                    self.current_limit = new_limit
                    limit_msg = Int32()
                    limit_msg.data = self.current_limit
                    self.limit_pub.publish(limit_msg)
                    self.get_logger().info(f"CONFIRMED Speed Cap: {self.current_limit}%")

        # 4. Handle Hazard Warnings
        elif sign in self.hazard_signs:
            warn_msg = String()
            warn_msg.data = sign
            self.warning_pub.publish(warn_msg)

def main(args=None):
    rclpy.init(args=args)
    node = SafetyManager()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()