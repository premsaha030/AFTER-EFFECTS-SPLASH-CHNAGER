import sys
import os
import glob
import ctypes
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox

# --- Request admin privileges on launch ---
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    script = os.path.abspath(sys.argv[0])
    params = " ".join([f'"{arg}"' for arg in sys.argv[1:]])
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}" {params}', None, 1)
    sys.exit()

# --- Get directory of this script and locate ResourceHacker.exe ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RESOURCE_HACKER_PATH = os.path.join(SCRIPT_DIR, "aftereffectsui\ResourceHacker.exe)

if not os.path.exists(RESOURCE_HACKER_PATH):
    tk.Tk().withdraw()    auto-py-to-exe
    messagebox.showerror("Error", f"ResourceHacker.exe not found in:\n{SCRIPT_DIR}\n\nPlease place it in the same folder as this tool.")
    sys.exit()

# Get all fixed drives (C, D, etc.)
def get_fixed_drives():
    drives = []
    bitmask = ctypes.windll.kernel32.GetLogicalDrives()
    for i in range(26):
        if bitmask & (1 << i):
            drive = f"{chr(65 + i)}:\\"
            if os.path.isdir(drive):
                drive_type = ctypes.windll.kernel32.GetDriveTypeW(drive)
                if drive_type == 3:
                    drives.append(drive)
    return drives

# Search for AfterFXLib.dll in AE folders
def find_ae_dll_paths():
    ae_paths = []
    for drive in get_fixed_drives():
        pattern = os.path.join(drive, "Program Files", "Adobe", "Adobe After Effects *", "Support Files", "AfterFXLib.dll")
        matches = glob.glob(pattern)
        ae_paths.extend(matches)
    return ae_paths

# Replace resource using Resource Hacker
def replace_resource(dll_path, resource_name, img_path):
    temp_output = dll_path + ".mod.dll"
    cmd = [
        RESOURCE_HACKER_PATH,
        "-open", dll_path,
        "-save", temp_output,
        "-action", "addoverwrite",
        "-res", img_path,
        "-mask", f"PNG,{resource_name},0"
    ]
    try:
        subprocess.run(cmd, check=True)
        os.replace(temp_output, dll_path)
        return True
    except Exception as e:
        print(f"Error replacing {resource_name}: {e}")
        return False

# GUI app
class AESplashReplacerApp:
    def __init__(self, root):
        self.root = root
        root.title("After Effects Splash Screen Replacer")
        root.geometry("600x500")
        root.resizable(False, False)

        self.canvas = tk.Canvas(root, width=600, height=500, highlightthickness=0)
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self.draw_gradient(self.canvas, 600, 500, "#000000", "#00aaff")

        self.ae_versions = find_ae_dll_paths()
        if not self.ae_versions:
            messagebox.showerror("Error", "No After Effects versions found.")
            root.destroy()
            return

        self.dll_var = tk.StringVar(value=self.ae_versions[0])
        self.entries = {}

        self.title_canvas = tk.Canvas(root, width=600, height=60, bg="black", highlightthickness=0)
        self.title_canvas.place(x=0, y=0)
        for dx in (-1, 1):
            for dy in (-1, 1):
                self.title_canvas.create_text(300+dx, 30+dy, text="AE Splash Replacer by Energy", fill="darkred", font=("Arial", 18, "bold"))
        self.title_canvas.create_text(300, 30, text="AE Splash Replacer by Energy", fill="red", font=("Arial", 18, "bold"))

        path_frame = tk.Frame(root, bg="black")
        path_frame.place(x=20, y=80)
        self.path_entry = tk.Entry(path_frame, textvariable=self.dll_var, width=60)
        self.path_entry.pack(side=tk.LEFT, padx=5)
        browse_dll = tk.Button(path_frame, text="📁", command=self.browse_dll)
        browse_dll.pack(side=tk.LEFT)

        splash_info = {
            "AE_SPLASH": "AE Splash (750 x 500)",
            "AE_SPLASH_AT_2X": "AE Splash @2x (1500 x 1000)",
            "AE_SPLASH_AT_3TO2X": "AE Splash @3to2x (1125 x 750)"
        }

        y_offset = 130
        for key, label_text in splash_info.items():
            frame = tk.Frame(root, bg="black")
            frame.place(x=20, y=y_offset)
            label = tk.Label(frame, text=label_text, fg="white", bg="black", width=30, anchor="e")
            label.pack(side=tk.LEFT, padx=5)
            entry = tk.Entry(frame, width=40)
            entry.pack(side=tk.LEFT)
            button = tk.Button(frame, text="Browse", command=lambda e=entry: self.browse_file(e))
            button.pack(side=tk.LEFT, padx=5)
            self.entries[key] = entry
            y_offset += 50

        self.apply_btn = tk.Button(
            root,
            text="APPLY",
            command=self.apply_changes,
            font=("Arial", 12, "bold"),
            bg="black",
            fg="white",
            relief="raised",
            bd=4
        )
        self.apply_btn.place(x=250, y=400, width=100, height=40)

    def draw_gradient(self, canvas, width, height, start_color, end_color):
        r1, g1, b1 = self.root.winfo_rgb(start_color)
        r2, g2, b2 = self.root.winfo_rgb(end_color)
        steps = height
        for i in range(steps):
            r = int(r1 + (r2 - r1) * i / steps) >> 8
            g = int(g1 + (g2 - g1) * i / steps) >> 8
            b = int(b1 + (b2 - b1) * i / steps) >> 8
            color = f"#{r:02x}{g:02x}{b:02x}"
            canvas.create_line(0, i, width, i, fill=color)

    def browse_file(self, entry):
        filepath = filedialog.askopenfilename(filetypes=[("PNG files", "*.png")])
        if filepath:
            entry.delete(0, tk.END)
            entry.insert(0, filepath)

    def browse_dll(self):
        path = filedialog.askopenfilename(filetypes=[("DLL files", "*.dll")])
        if path:
            self.dll_var.set(path)

    def apply_changes(self):
        dll_path = self.dll_var.get()
        success = True
        for resource, entry in self.entries.items():
            img_path = entry.get()
            if img_path:
                replaced = replace_resource(dll_path, resource, img_path)
                if not replaced:
                    success = False
        if success:
            messagebox.showinfo("Success", "Splash screens updated successfully.")
        else:
            messagebox.showerror("Error", "Some resources failed to update. Check console for details.")

if __name__ == "__main__":
    root = tk.Tk()
    app = AESplashReplacerApp(root)
    root.mainloop()