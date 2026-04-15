import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Bool, Float32
import tkinter as tk
from math import cos, sin, radians
from threading import Thread
import re

class EVDashboard(Node):
    def __init__(self):
        super().__init__('ev_dashboard')
        
        # 1. Tkinter Window Setup MUST happen before creating UI elements
        self.root = tk.Tk()
        self.root.title("Intelligent EV Safety Cluster")
        self.root.geometry("600x480")
        self.root.configure(bg='#000000')

        # 2. UI Elements setup
        self.warning_label = tk.Label(self.root, text="", fg="red", bg="#000000", font=("Helvetica", 24, "bold"))
        self.warning_label.pack(pady=10)

        self.status_label = tk.Label(self.root, text="SYSTEM READY", font=("Arial", 14, "bold"), bg='#000000', fg='#00FF00')
        self.status_label.pack(pady=5)

        self.canvas = tk.Canvas(self.root, width=600, height=350, bg='#000000', highlightthickness=0)
        self.canvas.pack()

        # 3. ROS Subscriptions (Notice warning_callback is referenced here)
        self.create_subscription(String, '/dashboard_warning', self.warning_callback, 10)
        self.create_subscription(String, '/detected_sign', self.sign_cb, 10)
        self.create_subscription(Bool, '/driver_reset', self.reset_cb, 10)
        self.create_subscription(Float32, '/cmd_pwm', self.speed_cb, 10)

        self.throttle = 0.0
        self.limit = 1.0
        self.horn = True

        Thread(target=lambda: rclpy.spin(self), daemon=True).start()
        
        self.animate()
        self.root.mainloop()

    def speed_cb(self, msg): 
        self.throttle = msg.data

    def sign_cb(self, msg):
        sign = msg.data
        if "Speed Limit" in sign:
            match = re.search(r'\d+', sign)
            if match:
                limit_val = int(match.group())
                self.limit = limit_val / 100.0
                self.status_label.config(text=f"LIMIT ACTIVE: {limit_val}%", fg='#FFA500')
        elif sign == 'No Horn' or sign == 'No Sound': 
            self.horn = False
            self.status_label.config(text="SILENT ZONE: HORN DISABLED", fg='#FF4444')

    # ---> Here is the missing function that caused the crash! <---
    def warning_callback(self, msg):
        self.root.after(0, self.trigger_popup, msg.data)

    def trigger_popup(self, hazard_text):
        self.warning_label.config(text=f"⚠️ {hazard_text.upper()} ⚠️", bg="yellow", fg="black")
        self.root.after(3000, self.clear_popup)
        
    def clear_popup(self):
        self.warning_label.config(text="", bg="#000000")

    def reset_cb(self, msg):
        if msg.data:
            self.limit = 1.0
            self.horn = True
            self.status_label.config(text="SYSTEM READY", fg='#00FF00')

    def animate(self):
        self.canvas.delete("all")
        cx, cy, r = 300, 200, 130
        
        self.canvas.create_arc(cx-r, cy-r, cx+r, cy+r, start=-30, extent=240, outline='#333333', width=12, style='arc')
        
        limit_extent = -(240 * self.limit)
        self.canvas.create_arc(cx-r, cy-r, cx+r, cy+r, start=210, extent=limit_extent, outline='#00AAFF', width=12, style='arc')

        angle = 210 - (240 * self.throttle)
        nx = cx + (r-25) * cos(radians(angle))
        ny = cy - (r-25) * sin(radians(angle))
        self.canvas.create_line(cx, cy, nx, ny, fill='white', width=4)
        
        self.canvas.create_text(cx, cy+30, text=f"{int(self.throttle*100)}", font=("Arial", 50, "bold"), fill="white")
        self.canvas.create_text(cx, cy+70, text="THR %", font=("Arial", 12), fill="#888888")
        
        horn_color = "#00FF00" if self.horn else "#FF0000"
        self.canvas.create_oval(40, 40, 70, 70, fill=horn_color, outline="")
        self.canvas.create_text(55, 85, text="HORN", fill="white", font=("Arial", 9))

        self.root.after(50, self.animate)

def main(args=None):
    rclpy.init(args=args)
    EVDashboard()
    rclpy.shutdown()

if __name__ == '__main__':
    main()