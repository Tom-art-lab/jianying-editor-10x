# -*- coding: utf-8 -*-
"""剪映 GUI 自动化工具（剪映 10.x 不暴露 accessibility，只能坐标点击 + 截图验证）。

用法:
    python _jy_gui.py info                 # 窗口状态
    python _jy_gui.py shot  <out.png>      # 置顶并截图
    python _jy_gui.py click <x> <y> [wait]
    python _jy_gui.py dclick<x> <y> [wait]
    python _jy_gui.py drag  <x1> <y1> <x2> <y2> [steps] [hold]
    python _jy_gui.py key   "<keys>"       # 例 "{Delete}"  "^s"
    python _jy_gui.py move  <x> <y>
"""
import ctypes
import ctypes.wintypes as wt
import sys
import time

import uiautomation as uia
from PIL import ImageGrab

uia.SetGlobalSearchTimeout(1.0)
try:
    uia.SetProcessDpiAwareness(2)
except Exception:
    pass

user32 = ctypes.WinDLL("user32", use_last_error=True)
k32 = ctypes.WinDLL("kernel32", use_last_error=True)
HWND = ctypes.c_void_p
HWND_TOPMOST = HWND(-1)
SWP = 0x0001 | 0x0002 | 0x0040          # NOSIZE | NOMOVE | SHOWWINDOW
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004


def find_jy():
    for _ in range(3):
        for w in uia.GetRootControl().GetChildren():
            try:
                if (w.Name or "") == "剪映专业版":
                    return w
            except Exception:
                pass
        time.sleep(1.5)
    return None


def activate(h):
    """把剪映窗口抢到前台。Windows 只允许前台进程 SetForegroundWindow，
    因此先用一个 ALT 键事件解除前台锁定，再 AttachThreadInput 强抢，失败重试。"""
    h = HWND(h)
    user32.ShowWindow(h, 9)
    time.sleep(0.4)
    for attempt in range(4):
        # ALT 键脉冲：解除前台锁定
        user32.keybd_event(0x12, 0, 0, 0)
        user32.keybd_event(0x12, 0, 2, 0)
        time.sleep(0.15)
        fg = user32.GetForegroundWindow()
        tf = user32.GetWindowThreadProcessId(HWND(fg), None)
        tm = k32.GetCurrentThreadId()
        user32.AttachThreadInput(tf, tm, True)
        user32.BringWindowToTop(h)
        user32.SetForegroundWindow(h)
        user32.SetFocus(h)
        user32.AttachThreadInput(tf, tm, False)
        time.sleep(0.8)
        if user32.GetForegroundWindow() == h:
            user32.SetWindowPos(h, HWND_TOPMOST, 0, 0, 0, 0, SWP)
            return True
        user32.SetWindowPos(h, HWND_TOPMOST, 0, 0, 0, 0, SWP)
        time.sleep(0.5)
    return user32.GetForegroundWindow() == h


def rect_of(h):
    rc = wt.RECT()
    user32.GetWindowRect(HWND(h), ctypes.byref(rc))
    return rc


def shot(path):
    user32.SetWindowPos(HWND(0), HWND(0), 0, 0, 0, 0, 0)   # no-op
    img = ImageGrab.grab(bbox=(0, 0, 1920, 1032), all_screens=True)
    img.save(path)
    return img


def drag(x1, y1, x2, y2, steps=40, hold=0.35):
    user32.SetCursorPos(int(x1), int(y1))
    time.sleep(0.4)
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(hold)
    for i in range(1, steps + 1):
        xi = int(x1 + (x2 - x1) * i / steps)
        yi = int(y1 + (y2 - y1) * i / steps)
        user32.SetCursorPos(xi, yi)
        time.sleep(0.025)
    time.sleep(0.5)
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    time.sleep(0.5)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    cmd = sys.argv[1]
    w = find_jy()
    if not w:
        print("未找到剪映窗口")
        return 1
    hwnd = w.NativeWindowHandle
    ok = activate(hwnd)
    rc = rect_of(hwnd)
    print(f"剪映 {w.ClassName}  窗口 {rc.right-rc.left}x{rc.bottom-rc.top}  前台={ok}")

    if cmd == "info":
        return 0
    if cmd == "shot":
        shot(sys.argv[2] if len(sys.argv) > 2 else "shot.png")
        print("已截图")
        return 0
    if cmd == "move":
        user32.SetCursorPos(int(sys.argv[2]), int(sys.argv[3]))
        print(f"移到 ({sys.argv[2]},{sys.argv[3]})")
        return 0
    if cmd in ("click", "dclick"):
        x, y = int(sys.argv[2]), int(sys.argv[3])
        wait = float(sys.argv[4]) if len(sys.argv) > 4 else 1.5
        uia.Click(x, y)
        if cmd == "dclick":
            time.sleep(0.15)
            uia.Click(x, y)
        time.sleep(wait)
        print(f"已点击 ({x},{y})")
        return 0
    if cmd == "drag":
        x1, y1, x2, y2 = (int(sys.argv[i]) for i in (2, 3, 4, 5))
        steps = int(sys.argv[6]) if len(sys.argv) > 6 else 40
        hold = float(sys.argv[7]) if len(sys.argv) > 7 else 0.35
        drag(x1, y1, x2, y2, steps, hold)
        print(f"已拖拽 ({x1},{y1}) -> ({x2},{y2})")
        return 0
    if cmd == "key":
        uia.SendKeys(sys.argv[2], waitTime=0.1)
        time.sleep(0.8)
        print(f"已发送 {sys.argv[2]}")
        return 0
    print("未知命令")
    return 1


if __name__ == "__main__":
    sys.exit(main())
