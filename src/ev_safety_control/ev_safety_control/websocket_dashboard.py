import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Float32, Int32
import asyncio
import websockets
import json
import threading

class WebSocketNode(Node):
    def __init__(self):
        super().__init__('websocket_dashboard')
        
        # ROS 2 Subscriptions
        self.create_subscription(Float32, '/cmd_pwm', self.pwm_cb, 10)
        self.create_subscription(Int32, '/system_limit', self.limit_cb, 10)
        self.create_subscription(String, '/dashboard_warning', self.warn_cb, 10)
        self.create_subscription(String, '/detected_sign', self.sign_cb, 10)
        
        self.ws_clients = set()
        self.get_logger().info("WebSocket Server blasting on ws://0.0.0.0:8765")
        
        # Start the background thread
        self.loop = asyncio.new_event_loop()
        threading.Thread(target=self.start_ws_server, daemon=True).start()

    # --- UPDATED: Modern websockets API requires serving inside an async context ---
    async def serve_forever(self):
        async with websockets.serve(self.ws_handler, "0.0.0.0", 8765):
            await asyncio.Future()  # Keeps the server alive infinitely

    def start_ws_server(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.serve_forever())

    # Added *args to safely absorb the deprecated 'path' argument across versions
    async def ws_handler(self, websocket, *args, **kwargs):
        self.ws_clients.add(websocket)
        try:
            await websocket.wait_closed()
        finally:
            self.ws_clients.remove(websocket)

    def broadcast(self, data):
        if not self.ws_clients: 
            return
        
        msg = json.dumps(data)
        
        async def send_to_clients():
            dead_clients = set()
            for ws in self.ws_clients:
                try:
                    await ws.send(msg)
                except Exception:
                    dead_clients.add(ws)
                    
            for ws in dead_clients:
                self.ws_clients.remove(ws)
                
        asyncio.run_coroutine_threadsafe(send_to_clients(), self.loop)

    # Callbacks
    def pwm_cb(self, msg):
        self.broadcast({"type": "pwm", "value": int(msg.data * 100)})

    def limit_cb(self, msg):
        self.broadcast({"type": "limit", "value": msg.data})

    def warn_cb(self, msg):
        self.broadcast({"type": "warning", "value": msg.data})
        
    def sign_cb(self, msg):
        self.broadcast({"type": "sign", "value": msg.data})

def main(args=None):
    rclpy.init(args=args)
    node = WebSocketNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()