import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import cv2
import os
from ultralytics import YOLO

class VisionNode(Node):
    def __init__(self):
        super().__init__('vision_node')
        self.publisher_ = self.create_publisher(String, '/detected_sign', 10)
        
        # Load YOLO model (CPU mode for Raspberry Pi stability)
        model_dir = os.path.expanduser('~/ev_safety_ws/src/ev_safety_control/ev_safety_control/models/')
        self.yolo_model = YOLO(os.path.join(model_dir, "best.pt"))
        self.yolo_model.to('cpu')
        
        # The EXACT 36 classes extracted from your model
        self.class_names = [
            'Cycle Zone', 'Danger Ahead', 'Deer Zone', 'End of Right Road -Go straight-', 
            'Give Way', 'Go Left or Straight', 'Go Right or Straight', 'Go Straight', 
            'Huddle Road', 'Left Curve Ahead', 'Left Sharp Curve', 'No Entry', 
            'No Over Taking Trucks', 'No Over Taking', 'No Stopping', 'No Waiting', 
            'Pedestrian', 'Right Curve Ahead', 'Right Sharp Curve', 'Road Work', 
            'RoundAbout', 'Slippery Road', 'Snow Warning Sign', 'Speed Limit 100', 
            'Speed Limit 120', 'Speed Limit 20', 'Speed Limit 30', 'Speed Limit 50', 
            'Speed Limit 60', 'Speed Limit 70', 'Speed Limit 80', 'Stop', 
            'Traffic Signals Ahead', 'Truck Sign', 'Turn Left', 'Turn Right'
        ]

        self.cap = self.init_webcam()
        
        # Set to 0.3 seconds (~3.3 FPS) to give the Pi 4 CPU breathing room
        self.timer = self.create_timer(0.3, self.process_frame)
        self.get_logger().info("Vision Node: YOLO 36-Class Model Loaded & Active.")

    def init_webcam(self):
        for idx in [0, 1, 2]:
            cap = cv2.VideoCapture(idx)
            if cap.isOpened():
                # HARDWARE OPTIMIZATION: Tell the webcam chip to only send 320x240
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
                # Force OpenCV to keep the buffer as small as possible
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1) 
                return cap
        self.get_logger().error("No webcam found.")
        return None

    def process_frame(self):
        if not self.cap or not self.cap.isOpened():
            return

        # Flush stale frames to ensure zero lag
        self.cap.grab()
        ret, frame = self.cap.retrieve()
        if not ret: return
        
        # Run inference (no need to resize, hardware already did it)
        results = self.yolo_model(frame, verbose=False, imgsz=320, device='cpu')

        best_sign = None
        highest_conf = 0.0

        for r in results:
            for box in r.boxes:
                conf = float(box.conf[0])
                # 45% confidence threshold
                if conf > 0.4 and conf > highest_conf:
                    highest_conf = conf
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    class_id = int(box.cls[0])
                    
                    if class_id < len(self.class_names):
                        best_sign = self.class_names[class_id]
                        
                        # Draw bounding box and confidence score
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(frame, f"{best_sign} {conf:.2f}", (x1, y1 - 10), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # COMMUNICATION FIX: Publish continuously so Safety Manager can count up to 3
        if best_sign:
            msg = String()
            msg.data = best_sign
            self.publisher_.publish(msg)
            # Only log occasionally so we don't spam the terminal
            self.get_logger().debug(f"Seeing: {best_sign}")

        # Show GUI if display is attached
        if os.environ.get('DISPLAY'):
            try:
                cv2.imshow("EV Vision feed", frame)
                cv2.waitKey(1)
            except Exception:
                pass

def main(args=None):
    rclpy.init(args=args)
    node = VisionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node.cap: node.cap.release()
        cv2.destroyAllWindows()
        rclpy.shutdown()

if __name__ == '__main__':
    main()