import tkinter as tk
from tkinter import messagebox, ttk
import win32print
import re
import sys
import ctypes
import subprocess
import socket
import threading

# ----------------------------
# ADMIN MODE
# ----------------------------
def ensure_admin():
    try:
        if not ctypes.windll.shell32.IsUserAnAdmin():
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, __file__, None, 1
            )
            sys.exit()
    except:
        pass

ensure_admin()

# ----------------------------
# FLOOR DETECTION
# ----------------------------
def detect_floor(name):
    name = name.lower()

    if "1st" in name or "floor1" in name or "f1" in name:
        return "1st Floor"
    if "2nd" in name or "floor2" in name or "f2" in name:
        return "2nd Floor"
    if "3rd" in name or "floor3" in name or "f3" in name:
        return "3rd Floor"

    return "Unknown Floor"

# ----------------------------
# IP EXTRACTION
# ----------------------------
def extract_ip(port_name):
    match = re.search(r"(\d+\.\d+\.\d+\.\d+)", str(port_name))
    return match.group(1) if match else None

def extract_ip_from_line(text):
    match = re.search(r"(\d+\.\d+\.\d+\.\d+)", str(text))
    return match.group(1) if match else None

# ----------------------------
# GET PRINTERS
# ----------------------------
def get_printers():
    printers = win32print.EnumPrinters(
        win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
    )

    result = []

    for p in printers:
        name = p[2]

        try:
            handle = win32print.OpenPrinter(name)
            info = win32print.GetPrinter(handle, 2)

            port = info.get("pPortName", "")
            ip = extract_ip(port)
            floor = detect_floor(name)

            result.append((name, ip or "No IP", floor))

            win32print.ClosePrinter(handle)

        except:
            result.append((name, "No IP", "Unknown"))

    return result

# ----------------------------
# PRINTER CHECK
# ----------------------------
def is_printer(ip):
    for port in [9100, 631, 515]:
        try:
            s = socket.socket()
            s.settimeout(0.2)
            if s.connect_ex((ip, port)) == 0:
                return True
        except:
            pass
    return False

# ----------------------------
# PING
# ----------------------------
def ping_ip(ip):
    try:
        output = subprocess.check_output(
            ["ping", "-n", "1", "-w", "400", ip],
            stderr=subprocess.DEVNULL,
            text=True
        )
        return "TTL=" in output
    except:
        return False

# ----------------------------
# NETWORK SCANNER
# ----------------------------
from concurrent.futures import ThreadPoolExecutor, as_completed

def scan_network():
    def worker():
        listbox.delete(0, tk.END)

        progress["value"] = 0
        progress["maximum"] = 7 * 254

        found = []

        def check_ip(ip):
            if is_printer(ip):
                return ip

        with ThreadPoolExecutor(max_workers=80) as executor:

            tasks = []
            for subnet in range(0, 8):
                for host in range(1, 255):
                    ip = f"192.168.{subnet}.{host}"
                    tasks.append(executor.submit(check_ip, ip))

            done = 0

            for future in as_completed(tasks):
                done += 1
                progress["value"] = done
                root.update_idletasks()

                result = future.result()
                if result:
                    found.append(result)
                    listbox.insert(tk.END, f"[PRINTER] {result}")

        if not found:
            listbox.insert(tk.END, "No printers found")

    threading.Thread(target=worker, daemon=True).start()

# ----------------------------
# REFRESH LOCAL PRINTERS
# ----------------------------
def refresh():
    listbox.delete(0, tk.END)

    for name, ip, floor in get_printers():
        listbox.insert(tk.END, f"{name} | {ip} | {floor} | UNKNOWN")

# ----------------------------
# DELETE (FIXED FORCE METHOD)
# ----------------------------
def delete_printer(name):
    try:
        subprocess.run(
            f'rundll32 printui.dll,PrintUIEntry /dl /n "{name}"',
            shell=True
        )

        subprocess.run(
            f'rundll32 printui.dll,PrintUIEntry /dn /n "{name}"',
            shell=True
        )

    except Exception as e:
        messagebox.showerror("Delete Error", str(e))

def remove_selected():
    try:
        selected = listbox.get(tk.ACTIVE)
        name = selected.split("|")[0].strip()
        delete_printer(name)
        refresh()
    except:
        pass

# ----------------------------
# COPY
# ----------------------------
def copy_selected_full():
    try:
        selected = listbox.get(tk.ACTIVE)
        root.clipboard_clear()
        root.clipboard_append(selected)
    except:
        pass

def copy_selected_ip():
    try:
        selected = listbox.get(tk.ACTIVE)
        ip = extract_ip_from_line(selected)

        if ip:
            root.clipboard_clear()
            root.clipboard_append(ip)
    except:
        pass

# ----------------------------
# PING STATUS (NO POPUP SPAM)
# ----------------------------
def show_ping_status(event=None):
    try:
        selected = listbox.get(listbox.curselection())
        ip = extract_ip_from_line(selected)

        if not ip:
            return

        status = "ONLINE 🟢" if ping_ip(ip) else "OFFLINE 🔴"
        root.title(f"{ip} - {status}")

    except:
        pass

# ----------------------------
#OPEN PRINTER PANEL
# ----------------------------
def open_printer_panel(_=None):
    try:
        subprocess.Popen("control printers")
    except:
        messagebox.showerror("Error", "Cannot open printer panel")

# ----------------------------
#RIGHT CLICK MENU
# ----------------------------
def show_context_menu(event):
    menu.tk_popup(event.x_root, event.y_root)

# ----------------------------
#UI
# ----------------------------
root = tk.Tk()
root.title("PrintSCAN FAST")
root.geometry("750x500")

listbox = tk.Listbox(root, width=100)
listbox.pack(pady=10)

progress = ttk.Progressbar(root, length=500)
progress.pack(pady=5)

tk.Button(root, text="Refresh Local Printers", command=refresh).pack()
tk.Button(root, text="Delete Selected", command=remove_selected).pack()
tk.Button(root, text="Scan Network (Printers)", command=scan_network, bg="lightblue").pack()

tk.Label(root, text="Burak Akdogan", fg="gray").pack(side="bottom")

menu = tk.Menu(root, tearoff=0)
menu.add_command(label="Copy IP", command=copy_selected_ip)
menu.add_command(label="Copy Full", command=copy_selected_full)
menu.add_command(label="Delete", command=remove_selected)
menu.add_command(label="Open Printer Panel", command=open_printer_panel)

root.bind("<Control-c>", lambda e: copy_selected_full())
listbox.bind("<Button-3>", show_context_menu)

#FIXED: only ONE bind
listbox.bind("<<ListboxSelect>>", show_ping_status)
listbox.bind("<Double-Button-1>", open_printer_panel)

refresh()
root.mainloop()