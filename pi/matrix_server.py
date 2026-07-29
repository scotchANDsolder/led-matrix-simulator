#!/usr/bin/env python3
"""
Receives 32x64 portrait RGB frames over a local TCP socket from the
Processing sketch (LEDMatrixSim.pde with SEND_TO_HARDWARE = true) and
pushes them to a physical HUB75 matrix via rpi-rgb-led-matrix.

The panel itself is natively 64 cols x 32 rows — its HUB75 wiring can't
change — but it's mounted rotated 90° so it reads as a 32-wide x 64-tall
portrait display. Each incoming portrait frame is rotated back into the
panel's native landscape layout before being written out.

If the image comes out upside-down or mirrored, the panel is mounted
rotated the other way — flip ROTATE_CW below.

Run on the Raspberry Pi, before starting the Processing sketch:
    sudo python3 matrix_server.py

Requires root because rpi-rgb-led-matrix accesses GPIO directly.
"""

import socket

from rgbmatrix import RGBMatrix, RGBMatrixOptions

# Frame dimensions as sent by the Processing sketch (portrait, as mounted).
PORTRAIT_W = 32
PORTRAIT_H = 64
FRAME_BYTES = PORTRAIT_W * PORTRAIT_H * 3  # RGB, row-major, top-left origin

# Physical panel wiring — fixed by the hardware, independent of mounting.
PANEL_COLS = 64
PANEL_ROWS = 32

# Direction the panel is physically rotated relative to its native wiring.
# True: rotate incoming frames 90° clockwise to reach the panel's native
# layout (i.e. the panel was mounted rotated 90° counter-clockwise).
# False: rotate counter-clockwise instead. If the live image is
# upside-down or mirrored, flip this.
ROTATE_CW = True

HOST = "127.0.0.1"
PORT = 7890


def build_matrix():
    options = RGBMatrixOptions()
    options.rows = PANEL_ROWS
    options.cols = PANEL_COLS
    options.chain_length = 1
    options.parallel = 1
    # "adafruit-hat" matches the Adafruit RGB Matrix Bonnet/HAT wiring.
    # If you've done the hardware PWM mod (soldered jumper), switch to
    # "adafruit-hat-pwm" for less flicker.
    options.hardware_mapping = "adafruit-hat"
    options.gpio_slowdown = 2  # raise if you see speckling/glitches
    return RGBMatrix(options=options)


def recv_exact(conn, n):
    buf = bytearray()
    while len(buf) < n:
        chunk = conn.recv(n - len(buf))
        if not chunk:
            return None
        buf.extend(chunk)
    return bytes(buf)


def panel_to_portrait_index(x, y):
    """Maps a native-panel pixel (x, y) to its source index in the
    portrait frame buffer, undoing the mount rotation.

    x, y are panel coordinates: x in [0, PANEL_COLS), y in [0, PANEL_ROWS).
    """
    if ROTATE_CW:
        # portrait(x, y) = panel(y, PORTRAIT_H - 1 - x) is the CW rotation
        # from portrait -> panel, so inverting: source portrait pixel is
        # (px, py) = (y, PORTRAIT_H - 1 - x).
        px, py = y, PORTRAIT_H - 1 - x
    else:
        # CCW rotation from portrait -> panel: panel(x, y) = portrait(PORTRAIT_W - 1 - y, x).
        px, py = PORTRAIT_W - 1 - y, x
    return (py * PORTRAIT_W + px) * 3


def main():
    matrix = build_matrix()
    canvas = matrix.CreateFrameCanvas()

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(1)
    print(f"Waiting for Processing sketch on {HOST}:{PORT} ...")

    try:
        while True:
            conn, addr = server.accept()
            print(f"Connected: {addr}")
            try:
                while True:
                    data = recv_exact(conn, FRAME_BYTES)
                    if data is None:
                        break
                    for y in range(PANEL_ROWS):
                        for x in range(PANEL_COLS):
                            idx = panel_to_portrait_index(x, y)
                            r, g, b = data[idx], data[idx + 1], data[idx + 2]
                            canvas.SetPixel(x, y, r, g, b)
                    canvas = matrix.SwapOnVSync(canvas)
            finally:
                conn.close()
                print("Disconnected, waiting for next connection...")
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
