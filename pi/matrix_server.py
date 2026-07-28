#!/usr/bin/env python3
"""
Receives 64x32 RGB frames over a local TCP socket from the Processing
sketch (LEDMatrixSim.pde with SEND_TO_HARDWARE = true) and pushes them to
a physical HUB75 matrix via rpi-rgb-led-matrix.

Run on the Raspberry Pi, before starting the Processing sketch:
    sudo python3 matrix_server.py

Requires root because rpi-rgb-led-matrix accesses GPIO directly.
"""

import socket

from rgbmatrix import RGBMatrix, RGBMatrixOptions

MATRIX_W = 64
MATRIX_H = 32
FRAME_BYTES = MATRIX_W * MATRIX_H * 3  # RGB, row-major, top-left origin

HOST = "127.0.0.1"
PORT = 7890


def build_matrix():
    options = RGBMatrixOptions()
    options.rows = MATRIX_H
    options.cols = MATRIX_W
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
                    idx = 0
                    for y in range(MATRIX_H):
                        for x in range(MATRIX_W):
                            r, g, b = data[idx], data[idx + 1], data[idx + 2]
                            canvas.SetPixel(x, y, r, g, b)
                            idx += 3
                    canvas = matrix.SwapOnVSync(canvas)
            finally:
                conn.close()
                print("Disconnected, waiting for next connection...")
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
