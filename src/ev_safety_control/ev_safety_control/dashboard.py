import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Bool, Float32
import tkinter as tk
from math import cos, sin, radians
from threading import Thread

class EVDashboard(Node):
    def __init__(self):
        super().__init__('ev_dashboard')
        
        # ROS Subscriptions
        self.create_subscription(String, '/detected_sign', self.sign_cb, 10)
        self.create_subscription(Bool, '/driver_reset', self.reset_cb, 10)
        self.create_subscription(Float32, '/cmd_pwm', self.speed_cb, 10)

        # UI State Variables
        self.throttle = 0.0
        self.limit = 1.0
        self.horn = True

        # Tkinter Window Setup
        self.root = tk.Tk()
        self.root.title("Intelligent EV Safety Cluster")
        self.root.geometry("600x450")
        self.root.configure(bg='#000000') # Tesla-style dark mode

        # Gauge Canvas
        self.canvas = tk.Canvas(self.root, width=600, height=350, bg='#000000', highlightthickness=0)
        self.canvas.pack()

        # Status Text Display
        self.status_label = tk.Label(self.root, text="SYSTEM READY", font=("Arial", 14, "bold"), bg='#000000', fg='#00FF00')
        self.status_label.pack(pady=10)

        # Threading: Run ROS in background, Tkinter in foreground
        Thread(target=lambda: rclpy.spin(self), daemon=True).start()
        
        self.animate()
        self.root.mainloop()

    # Callback: Updates needle position from /cmd_pwm
    def speed_cb(self, msg): 
        self.throttle = msg.data

    # Callback: Handles speed limit signs and silent zones
    def sign_cb(self, msg):
        sign = msg.data.lower()
        if 'speed_' in sign:
            try:
                self.limit = int(sign.split('_')[1]) / 100.0
                self.status_label.config(text=f"LIMIT ACTIVE: {int(self.limit*100)}%", fg='#FFA500')
            except (IndexError, ValueError): pass
        elif 'no_horn' in sign:
            self.horn = False
            self.status_label.config(text="SILENT ZONE: HORN DISABLED", fg='#FF4444')

    # Callback: Resets GUI when driver interrupts safety
    def reset_cb(self, msg):
        if msg.data:
            self.limit = 1.0
            self.horn = True
            self.status_label.config(text="SYSTEM READY", fg='#00FF00')

    def animate(self):
        self.canvas.delete("all")
        cx, cy, r = 300, 200, 130
        
        # 1. Background Gauge Arc (Gray)
        self.canvas.create_arc(cx-r, cy-r, cx+r, cy+r, start=-30, extent=240, 
                              outline='#333333', width=12, style='arc')
        
        # 2. Dynamic Limit Arc (Blue) - Shows available throttle range
        limit_extent = -(240 * self.limit)
        self.canvas.create_arc(cx-r, cy-r, cx+r, cy+r, start=210, extent=limit_extent, 
                              outline='#00AAFF', width=12, style='arc')

        # 3. Needle Logic
        angle = 210 - (240 * self.throttle)
        nx = cx + (r-25) * cos(radians(angle))
        ny = cy - (r-25) * sin(radians(angle))
        self.canvas.create_line(cx, cy, nx, ny, fill='white', width=4)
        
        # 4. Digital Speed Readout
        self.canvas.create_text(cx, cy+30, text=f"{int(self.throttle*100)}", 
                               font=("Arial", 50, "bold"), fill="white")
        self.canvas.create_text(cx, cy+70, text="THR %", font=("Arial", 12), fill="#888888")
        
        # 5. Horn Status Icon
        horn_color = "#00FF00" if self.horn else "#FF0000"
        self.canvas.create_oval(40, 40, 70, 70, fill=horn_color, outline="")
        self.canvas.create_text(55, 85, text="HORN", fill="white", font=("Arial", 9))

        # Refresh at 20 FPS (50ms)
        self.root.after(50, self.animate)

def main(args=None):
    rclpy.init(args=args)
    EVDashboard()
    rclpy.shutdown()

if __name__ == '__main__':
    main()