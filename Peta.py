import tkinter as tk
from tkinter import messagebox, simpledialog
from PIL import Image, ImageTk
import os
import math
import heapq
import json

CANVAS_W, CANVAS_H = 1286, 550
BAR_H = 100
NODE_R, HIT_R = 8, 12
MAP_PATH = "Peta Malang.png"

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Mini Map")
        self.geometry(f"{CANVAS_W}x{CANVAS_H+BAR_H}")
        self.nodes = []
        self.lines = []
        self.selected_node = None
        self.mode = "Add Node"
        self.show_distances = False
        self.node_names = []
        self.shortest_path = []
        self.nodes_file = "data.json"
        
        self.canvas = tk.Canvas(self, width=CANVAS_W, height=CANVAS_H, bg="black")
        self.canvas.pack(side="top", fill="both", expand=True)
        if os.path.exists(MAP_PATH):
            img = Image.open(MAP_PATH).resize((CANVAS_W, CANVAS_H))
            self.bg_img = ImageTk.PhotoImage(img)
            self.canvas.create_image(0, 0, anchor="nw", image=self.bg_img)
        else: 
            self.bg_img = None
            
        frame = tk.Frame(self, height=BAR_H, bg="lightgray", relief="raised", borderwidth=2)
        frame.pack(side="bottom", fill="x", padx=5, pady=5)
        frame.pack_propagate(False)
        
        tk.Button(frame, text="Add Node", command=lambda: self.set_mode("Add Node"), width=12, height=2, bg="lightblue").pack(side="left", padx=5, pady=10)
        tk.Button(frame, text="Delete Node", command=lambda: self.set_mode("Delete Node"), width=12, height=2, bg="lightblue").pack(side="left", padx=5, pady=10)
        tk.Button(frame, text="Connect Node", command=lambda: self.set_mode("Connect Node"), width=12, height=2, bg="lightblue").pack(side="left", padx=5, pady=10)
        tk.Button(frame, text="Delete Line", command=lambda: self.set_mode("Delete Line"), width=12, height=2, bg="lightblue").pack(side="left", padx=5, pady=10)
        tk.Button(frame, text="Display Distance", command=self.toggle_distances, width=13, height=2, bg="lightblue").pack(side="left", padx=5, pady=10)
        tk.Button(frame, text="Find Shortest Path", command=self.find_shortest_path, width=15, height=2, bg="lightblue").pack(side="left", padx=5, pady=10)
        tk.Button(frame, text="Clear All", fg="white", command=self.clear_all, width=12, height=2, bg="red").pack(side="left", padx=5, pady=10)
        
        self.info = tk.Label(frame, text="Mode: Add Node", bg="lightgray")
        self.info.pack(padx=10, pady=27)
        
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Double-Button-1>", self.on_double_click)
        
        self.click_timer = None
        self.click_count = 0
        self.click_node_index = None
        
        self.auto_load()
        
    def calculate_distance(self, x1, y1, x2, y2):
        return math.sqrt((x2-x1)**2+(y2-y1)**2)
        
    def calculate_total_distance(self):
        total = 0
        for line in self.lines:
            if len(line) == 3:
                total += line[2]
        return total
        
    def toggle_distances(self):
        self.show_distances = not self.show_distances
        self.redraw_canvas()
    
    def set_mode(self, m):
        self.mode = m
        self.selected_node = None
        self.update_info()
        
    def update_info(self):
        self.info.config(text=f"Mode: {self.mode}")
        total_distance = self.calculate_total_distance()
        self.distance_info.config(text=f"Total Distance: {total_distance:.2f} px")
     
    def on_click(self, e):
        if self.click_timer:
            self.after_cancel(self.click_timer)
            self.click_timer = None
        
        self.click_count += 1
    
        node_index = self.find_node_at(e.x, e.y)
        
        if node_index is not None:
            self.click_node_index = node_index
            
            if self.click_count == 1:
                self.click_timer = self.after(300, self.process_single_click, e)
            else:
                self.click_count = 0
                self.process_double_click(node_index)
        else:
            self.process_single_click(e)
    
    def find_node_at(self, x, y):
        for i, (px, py) in enumerate(self.nodes):
            if (x - px)**2 + (y - py)**2 <= HIT_R**2:
                return i
        return None
    
    def process_single_click(self, e):
        if self.mode == "Add Node":
            self.add_node(e.x, e.y)
        elif self.mode == "Delete Node":
            self.del_node(e.x, e.y)
        elif self.mode == "Connect Node":
            self.connect_node(e.x, e.y)
        elif self.mode == "Delete Line":
            self.del_line(e.x, e.y)
        
        self.click_count = 0
        self.click_node_index = None
        self.update_info()
    
    def process_double_click(self, node_index):
        self.rename_node(node_index)
        self.click_count = 0
        self.click_node_index = None
    
    def on_double_click(self, e):
        node_index = self.find_node_at(e.x, e.y)
        if node_index is not None:
            self.rename_node(node_index)
    
    def rename_node(self, node_index):
        if 0 <= node_index < len(self.node_names):
            current_name = self.node_names[node_index]
            new_name = simpledialog.askstring(
                "Rename Node", 
                f"Enter new name for node {current_name}:",
                parent=self,
                initialvalue=current_name
            )
            
            if new_name and new_name.strip():
                new_name = new_name.strip()
                if new_name in self.node_names and new_name != current_name:
                    messagebox.showerror("Error", f"Node name '{new_name}' already exists!")
                    return
                
                self.node_names[node_index] = new_name
                self.redraw_canvas()
                self.auto_save()
    
    def add_node(self, x, y):
        self.nodes.append((x, y))
        node_name = chr(65 + len(self.nodes) - 1)
        base_name = node_name
        counter = 1
        while node_name in self.node_names:
            node_name = f"{base_name}{counter}"
            counter += 1
        self.node_names.append(node_name)
        self.redraw_canvas()
        self.auto_save()
        
    def del_node(self, x, y):
        node_index = self.find_node_at(x, y)
        if node_index is not None:
            node_name = self.node_names[node_index]
            if messagebox.askyesno("Confirm Delete", f"Delete node '{node_name}'?"):
                self.nodes.pop(node_index)
                self.node_names.pop(node_index)
                self.lines = [line for line in self.lines if line[0] != node_index and line[1] != node_index]
                for j in range(len(self.lines)):
                    n1, n2, dist = self.lines[j]
                    if n1 > node_index:
                        n1 -= 1 
                    if n2 > node_index:
                        n2 -= 1 
                    self.lines[j] = (n1, n2, dist)
                self.redraw_canvas()
                self.auto_save()
    
    def connect_node(self, x, y):
        node_index = self.find_node_at(x, y)
        if node_index is not None:
            if self.selected_node is None:
                self.selected_node = node_index
                self.redraw_canvas()
            else:
                if self.selected_node != node_index:
                    x1, y1 = self.nodes[self.selected_node]
                    x2, y2 = self.nodes[node_index]
                    distance = self.calculate_distance(x1, y1, x2, y2)
                    
                    new_line = (min(self.selected_node, node_index), max(self.selected_node, node_index), distance)
                    exists = False
                    for line in self.lines:
                        if (line[0] == new_line[0] and line[1] == new_line[1]):
                            exists = True
                            break
                    if not exists:
                        self.lines.append(new_line)
                    self.selected_node = None
                    
                    self.redraw_canvas()
                    self.auto_save()
    
    def del_line(self, x, y):
        for i, line in enumerate(self.lines):
            if len(line) == 3:
                n1, n2, distance = line
                if n1 < len(self.nodes) and n2 < len(self.nodes):
                    x1, y1 = self.nodes[n1]
                    x2, y2 = self.nodes[n2]
                    
                    A = x - x1
                    B = y - y1
                    C = x2 - x1
                    D = y2 - y1
                    
                    dot = A * C + B * D
                    len_sq = C * C + D * D
                   
                    if len_sq == 0:
                        continue
                    
                    param = dot / len_sq
                    
                    if param < 0:
                        xx, yy = x1, y1
                    elif param > 1:
                        xx, yy = x2, y2
                    else:
                        xx = x1 + param * C
                        yy = y1 + param * D
                    
                    dx = x - xx
                    dy = y - yy
                    dist = math.sqrt(dx * dx + dy * dy)
                   
                    if dist <= HIT_R:
                        if messagebox.askyesno("Confirm Delete", "Delete this connection?"):
                            self.lines.pop(i)
                            self.redraw_canvas()
                            self.auto_save()
                        break
    
    def build_graph(self):
        graph = {}
        for i in range(len(self.nodes)):
            graph[i] = {}
        for line in self.lines:
            if len(line) == 3:
                n1, n2, distance = line
                graph[n1][n2] = distance
                graph[n2][n1] = distance
        return graph
    
    def djikstra(self, graph, start):
        distances = {node: float('inf') for node in graph}
        distances[start] = 0
        previous = {node: None for node in graph}
        priority_queue = [(0, start)]
        while priority_queue:
            current_distance, current_node = heapq.heappop(priority_queue)
            if current_distance > distances[current_node]:
                continue
            for neighbor, distance_to_neighbor in graph[current_node].items():
                distance = current_distance + distance_to_neighbor
                if distance < distances[neighbor]:
                    distances[neighbor] = distance
                    previous[neighbor] = current_node
                    heapq.heappush(priority_queue, (distance, neighbor))
        return distances, previous
    
    def get_shortest_path(self, previous, start, end):
        path = []
        current = end
        while current is not None:
            path.append(current)
            current = previous[current]
        path.reverse()
        if path[0] == start:
            return path
        else:
            return []
    
    def find_shortest_path(self):
        if len(self.nodes) < 2:
            messagebox.showwarning("Alert", "Please add more nodes to use this command.")
            return
        if len(self.lines) == 0:
            messagebox.showwarning("Alert", "Please connect the nodes to use this command.")
            return
        path_window = tk.Toplevel(self)
        path_window.title("Choose your starting and ending node")
        path_window.geometry("300x200")
        path_window.transient(self)
        path_window.grab_set()
        
        tk.Label(path_window, text="Starting Node:").pack(pady=5)
        start_var = tk.StringVar(value=self.node_names[0])
        start_menu = tk.OptionMenu(path_window, start_var, *self.node_names)
        start_menu.pack(pady=5)
        
        tk.Label(path_window, text="Ending Node:").pack(pady=5)
        end_var = tk.StringVar(value=self.node_names[1] if len(self.node_names) > 1 else self.node_names[0])
        end_menu = tk.OptionMenu(path_window, end_var, *self.node_names)
        end_menu.pack(pady=5)
        
        def calculate_path():
            try:
                start_node = self.node_names.index(start_var.get())
                end_node = self.node_names.index(end_var.get())
                graph = self.build_graph()
                if end_node not in graph or not graph[end_node]:
                    messagebox.showerror("Error", f"Node {end_var.get()} is not connected to any nodes")
                    return
                distances, previous = self.djikstra(graph, start_node)
                path = self.get_shortest_path(previous, start_node, end_node)
                if path: 
                    result_text = f"The shortest path: {' → '.join([self.node_names[node] for node in path])}\n"
                    result_text += f"Total distances: {distances[end_node]:.2f} px"
                    self.shortest_path = path
                    self.redraw_canvas_with_highlight()
                    messagebox.showinfo("Djikstra Result", result_text)
                else:
                    messagebox.showerror("Error", "No paths detected between the nodes you choose.")
            except Exception as e:
                messagebox.showerror("Error", f"Trouble: {str(e)}")
            path_window.destroy()
        tk.Button(path_window, text="Count", command=calculate_path, bg="lightblue").pack(pady=15)
    
    def auto_save(self):
        if self.nodes:
            try:
                data = {
                    "nodes": self.nodes,
                    "lines": self.lines,
                    "node_names": self.node_names
                    }
                with open(self.nodes_file, 'w') as f:
                    json.dump(data, f, indent=4)
            except Exception as e:
                print(f"Auto-save failed: {e}")
    
    def auto_load(self):
        if os.path.exists(self.nodes_file):
            try: 
                with open(self.nodes_file, 'r') as f:
                    data = json.load(f)
                if all(key in data for key in ["nodes", "lines", "node_names"]):
                    self.nodes = [(node[0], node[1]) for node in data["nodes"]]
                    self.lines = [(line[0], line[1], line[2]) for line in data["lines"]]
                    self.node_names = data["node_names"]
                    
                    self.redraw_canvas()
                    self.update_info()
            except Exception as e:
                return e
    
    def redraw_canvas_with_highlight(self):
        self.canvas.delete("all")
        
        if self.bg_img:
            self.canvas.create_image(0, 0, anchor="nw", image=self.bg_img)
    
        for line in self.lines:
            if len(line) == 3:
                n1, n2, distance = line
                if n1 < len(self.nodes) and n2 < len(self.nodes):
                    x1, y1 = self.nodes[n1]
                    x2, y2 = self.nodes[n2]
                    
                    self.canvas.create_line(x1, y1, x2, y2, fill="black", width=2)
                    if self.show_distances:
                        mid_x = (x1 + x2) / 2
                        mid_y = (y1 + y2) / 2
                        
                        self.canvas.create_rectangle(mid_x - 20, mid_y - 10, mid_x + 20, mid_y + 10, fill="black")
                        self.canvas.create_text(mid_x, mid_y, text=f"{distance:.1f}", fill="white", font=("Arial", 8 ,"bold"))
        
        if self.shortest_path:
            for i in range(len(self.shortest_path) - 1):
                n1, n2 = self.shortest_path[i], self.shortest_path[i + 1]
                x1, y1 = self.nodes[n1]
                x2, y2 = self.nodes[n2]

                self.canvas.create_line(x1, y1, x2, y2, fill="green", width=4)
                
        for i, (x, y) in enumerate(self.nodes):
            if self.shortest_path:
                if i == self.shortest_path[0]:
                    self.canvas.create_oval(x - NODE_R, y - NODE_R, x + NODE_R, y + NODE_R, fill="blue", outline="black")
                    self.canvas.create_text(x, y - 15, text=self.node_names[i], fill="black", font=("Arial", 10, "bold"))
                elif i == self.shortest_path[-1]:
                    self.canvas.create_oval(x - NODE_R, y - NODE_R, x + NODE_R, y + NODE_R, fill="blue", outline="black")
                    self.canvas.create_text(x, y - 15, text=self.node_names[i], fill="black", font=("Arial", 10, "bold"))
                else: 
                    None
                    
    def redraw_canvas(self):
        self.canvas.delete("all")
        if self.bg_img:
            self.canvas.create_image(0, 0, anchor="nw", image=self.bg_img)
            
        for line in self.lines:
            if len(line) == 3:
                n1, n2, distance = line
                if n1 < len(self.nodes) and n2 < len(self.nodes):
                    x1, y1 = self.nodes[n1]
                    x2, y2 = self.nodes[n2]
                    self.canvas.create_line(x1, y1, x2, y2, fill="black", width=2)
                    if self.show_distances:
                        mid_x = (x1 + x2) / 2
                        mid_y = (y1 + y2) / 2
                        self.canvas.create_rectangle(mid_x - 20, mid_y - 10, mid_x + 20, mid_y + 10, fill="black")
                        self.canvas.create_text(mid_x, mid_y, text=f"{distance:.1f}", fill="white", font=("Arial", 8 ,"bold"))
        
        for i, (x, y) in enumerate(self.nodes):
            fill_color = "yellow" if i == self.selected_node else "red"
            self.canvas.create_oval(x - NODE_R, y - NODE_R, x + NODE_R, y + NODE_R, fill=fill_color, outline="black")
            self.canvas.create_text(x, y - 15, text=self.node_names[i], fill="black", font=("Arial", 10, "bold"))
            
    def clear_all(self):
        if messagebox.askyesno("Confirm Clear", "Are you sure you want to clear all nodes and connections?"):
            self.nodes = []
            self.lines = []
            self.node_names = []
            self.selected_node = None 
            self.shortest_path = []
            self.redraw_canvas()
            self.update_info()
            if os.path.exists(self.nodes_file):
                os.remove(self.nodes_file)
        
if __name__ == "__main__":
    App().mainloop()