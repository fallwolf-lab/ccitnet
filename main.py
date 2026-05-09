import time
import requests
import json
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox

if getattr(sys, "frozen", False):
    APP_DIR = os.path.dirname(sys.executable)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(APP_DIR, "config.json")


def rc4_encrypt(key: str, plaintext: str) -> str:
    """RC4 加密，返回十六进制字符串"""
    key_bytes = key.encode()
    plain_bytes = plaintext.encode()

    s = list(range(256))
    j = 0
    for i in range(256):
        j = (j + s[i] + key_bytes[i % len(key_bytes)]) % 256
        s[i], s[j] = s[j], s[i]

    i = j = 0
    cipher = []
    for byte in plain_bytes:
        i = (i + 1) % 256
        j = (j + s[i]) % 256
        s[i], s[j] = s[j], s[i]
        k = s[(s[i] + s[j]) % 256]
        cipher.append(byte ^ k)

    return bytes(cipher).hex()


def load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_config(config: dict) -> None:
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


class SettingsDialog(tk.Toplevel):
    def __init__(self, parent, config: dict, on_save, is_first_time: bool = False):
        super().__init__(parent)
        self.title("设置账号密码")
        self.resizable(False, False)
        self.on_save = on_save
        self.is_first_time = is_first_time
        self.result = None

        self.transient(parent)
        self.grab_set()

        frame = ttk.Frame(self, padding=20)
        frame.pack()

        if is_first_time:
            ttk.Label(frame, text="首次使用，请先设置您的账号和密码",
                      foreground="red").grid(row=0, column=0, columnspan=2,
                                              pady=(0, 12))

        ttk.Label(frame, text="账号:").grid(row=1, column=0, sticky="e",
                                              padx=(0, 8), pady=4)
        self.user_entry = ttk.Entry(frame, width=28)
        self.user_entry.grid(row=1, column=1, pady=4)
        self.user_entry.insert(0, config.get("userName", ""))

        ttk.Label(frame, text="密码:").grid(row=2, column=0, sticky="e",
                                              padx=(0, 8), pady=4)
        self.pwd_entry = ttk.Entry(frame, width=28, show="*")
        self.pwd_entry.grid(row=2, column=1, pady=4)
        self.pwd_entry.insert(0, config.get("password", ""))

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=(16, 0))

        ttk.Button(btn_frame, text="保存", command=self._on_save,
                   width=10).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="取消", command=self._on_cancel,
                   width=10).pack(side="left", padx=4)

        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

        self.user_entry.focus_set()
        self.wait_window()

    def _on_save(self):
        user = self.user_entry.get().strip()
        pwd = self.pwd_entry.get().strip()
        if not user or not pwd:
            messagebox.showwarning("提示", "账号和密码不能为空",
                                   parent=self)
            return
        self.result = {"userName": user, "password": pwd}
        self.on_save(self.result)
        self.destroy()

    def _on_cancel(self):
        if self.is_first_time:
            if messagebox.askyesno("提示",
                                   "未设置账号密码将无法登录，确定要退出吗？",
                                   parent=self):
                self.result = None
                self.destroy()
        else:
            self.result = None
            self.destroy()


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("CCITNet 校园网登录")
        self.root.resizable(False, False)
        self.root.geometry("360x200")

        self.config = load_config()
        self.countdown_id = None
        self.countdown = 0

        self._build_menu()
        self._build_main()

        if not self.config.get("userName") or not self.config.get("password"):
            self.root.after(100, self._show_settings_first_time)
        else:
            self._start_countdown()

    def _build_menu(self):
        menubar = tk.Menu(self.root)
        menubar.add_command(label="修改账号密码",
                            command=self._show_settings_modify)
        self.root.config(menu=menubar)

    def _build_main(self):
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill="both", expand=True)

        self.status_label = ttk.Label(main_frame, text="程序已启动",
                                      font=("", 11))
        self.status_label.pack(pady=(10, 4))

        self.user_label = ttk.Label(main_frame, text="", foreground="gray")
        self.user_label.pack(pady=4)

        self.countdown_label = ttk.Label(main_frame, text="",
                                         font=("", 14, "bold"),
                                         foreground="#2196F3")
        self.countdown_label.pack(pady=8)

        self.result_label = ttk.Label(main_frame, text="")
        self.result_label.pack(pady=4)

        self._refresh_user_label()

    def _refresh_user_label(self):
        user = self.config.get("userName", "")
        if user:
            self.user_label.config(text=f"当前账号: {user}")
        else:
            self.user_label.config(text="尚未设置账号密码")

    def _show_settings_modify(self):
        if self.countdown_id:
            self.root.after_cancel(self.countdown_id)
            self.countdown_id = None
        self.countdown_label.config(text="")

        dialog = SettingsDialog(self.root, self.config, self._on_config_saved,
                                is_first_time=False)
        if not self.config.get("userName") or not self.config.get("password"):
            messagebox.showwarning("提示", "未设置账号密码，程序将退出")
            self.root.destroy()
        elif dialog.result is None:
            self._start_countdown()

    def _show_settings_first_time(self):
        dialog = SettingsDialog(self.root, self.config, self._on_config_saved,
                                is_first_time=True)
        if dialog.result is None:
            self.root.destroy()
            return
        if not self.config.get("userName") or not self.config.get("password"):
            self.root.destroy()

    def _on_config_saved(self, config: dict):
        self.config = config
        save_config(config)
        self._refresh_user_label()
        if self.countdown_id:
            self.root.after_cancel(self.countdown_id)
        self._start_countdown()

    def _start_countdown(self):
        self.countdown = 4
        self._tick_countdown()

    def _tick_countdown(self):
        if self.countdown > 0:
            self.countdown_label.config(
                text=f"将在 {self.countdown} 秒后自动登录...")
            self.countdown -= 1
            self.countdown_id = self.root.after(1000, self._tick_countdown)
        else:
            self.countdown_label.config(text="正在登录...")
            self._do_login()

    def _do_login(self):
        url = "http://1.1.1.4/ac_portal/login.php"
        timestamp = str(int(time.time() * 1000))

        data = {
            "opr": "pwdLogin",
            "userName": self.config.get("userName", ""),
            "pwd": rc4_encrypt(timestamp, self.config.get("password", "")),
            "auth_tag": timestamp,
            "rememberPwd": "0",
        }

        try:
            resp = requests.post(url, data=data, timeout=10)
            if resp.status_code == 200:
                self.result_label.config(text="登录成功，2秒后自动关闭",
                                         foreground="green")
                self.root.after(2000, self.root.destroy)
            else:
                self.result_label.config(
                    text=f"登录失败，状态码: {resp.status_code}",
                    foreground="red")
        except requests.RequestException as e:
            self.result_label.config(text=f"请求异常: {e}",
                                     foreground="red",
                                     wraplength=300)
        finally:
            self.countdown_label.config(text="")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    App().run()
