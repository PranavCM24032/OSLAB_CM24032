import json
import os
import sys
import socket
import webbrowser
import functools
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import List, Tuple, Dict, Any

# Fix Windows unicode printing and buffering
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

print = functools.partial(print, flush=True)

def calculate_look(head: int, requests: List[int], direction: str) -> Tuple[List[int], int]:
    """
    LOOK Algorithm: Reverses direction after serving the last request in that direction.
    More efficient than SCAN as it doesn't go to floor 0 or max_floor unnecessarily.
    """
    if not requests:
        return [], 0
    
    unique_reqs = sorted(list(set(requests)))
    upper = [r for r in unique_reqs if r >= head]
    lower = [r for r in unique_reqs if r < head]
    
    sequence = []
    total_distance = 0
    current_pos = head
    
    if direction == "UP":
        # Process upper requests first
        if upper:
            sequence.extend(upper)
            total_distance += abs(upper[-1] - head)
            current_pos = upper[-1]
        # Then reverse to lower requests
        if lower:
            rev_lower = sorted(lower, reverse=True)
            sequence.extend(rev_lower)
            total_distance += abs(current_pos - rev_lower[-1])
    else:  # DOWN
        # Process lower requests first
        if lower:
            rev_lower = sorted(lower, reverse=True)
            sequence.extend(rev_lower)
            total_distance += abs(head - rev_lower[-1])
            current_pos = rev_lower[-1]
        # Then reverse to upper requests
        if upper:
            sequence.extend(upper)
            total_distance += abs(current_pos - upper[-1])
            
    return sequence, total_distance

def get_eta(head: int, direction: str, target: int, max_floor: int) -> int:
    """Simple ETA based on distance and direction."""
    if direction == "UP":
        return target - head if target >= head else (max_floor - head) + (max_floor - target)
    return head - target if target <= head else head + target

def optimize_with_dynamic_allocation(reqs: List[int], lift_a: Dict, lift_b: Dict, max_floor: int) -> Dict:
    reqs_a, reqs_b = [], []
    
    # 1. Balanced Request Allocation
    for r in sorted(reqs):
        eta_a = get_eta(lift_a['head'], lift_a['dir'], r, max_floor)
        eta_b = get_eta(lift_b['head'], lift_b['dir'], r, max_floor)
        if eta_a <= eta_b:
            reqs_a.append(r)
        else:
            reqs_b.append(r)
            
    # 2. Calculate LOOK Sequences
    seq_a, dist_a = calculate_look(lift_a['head'], reqs_a, lift_a['dir'])
    seq_b, dist_b = calculate_look(lift_b['head'], reqs_b, lift_b['dir'])
    
    # 3. Reference for chart (single lift efficiency)
    _, dist_single = calculate_look(lift_a['head'], reqs, lift_a['dir'])
    
    return {
        'liftA': {'sequence': seq_a, 'distance': dist_a, 'head': lift_a['head']},
        'liftB': {'sequence': seq_b, 'distance': dist_b, 'head': lift_b['head']},
        'totalDistance': dist_a + dist_b,
        'singleLiftDistance': dist_single
    }

class RequestHandler(BaseHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200); self.end_headers()

    def do_POST(self):
        if self.path == '/optimize':
            content_length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(content_length).decode('utf-8'))
            
            result = optimize_with_dynamic_allocation(
                data.get('requests', []), 
                data.get('liftA'), 
                data.get('liftB'), 
                data.get('maxFloor', 50)
            )
            
            print(f"\n[LOOK Optimization]")
            print(f"Requests: {data.get('requests', [])}")
            print(f"Lift A Distance: {result['liftA']['distance']}")
            print(f"Lift B Distance: {result['liftB']['distance']}")
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode('utf-8'))

def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

def run():
    port = get_free_port()
    server = HTTPServer(('', port), RequestHandler)
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    index_path = f"file://{os.path.join(current_dir, 'index.html')}?port={port}"
    
    print("\n" + "="*50)
    print("🏢 MULTI-LIFT LOOK ALGORITHM SERVER")
    print("="*50)
    print(f"🚀 Server running on port {port}")
    print(f"🔗 Open this in your browser: {index_path}\n")
    webbrowser.open(index_path)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Server stopped.")

if __name__ == '__main__':
    run()