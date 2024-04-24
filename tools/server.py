#! /usr/bin/python3

import socket
import sys
from threading import Timer
from datetime import datetime
from time import sleep

HOST = '127.0.0.1'
PORT = 8888


def sendDetectionCommand():
    print("Do detection")
    command = "SET:01"
    conn.send(command.encode())
    print("Send message to client.")
    data = str(conn.recv(1024), encoding='utf-8')
    print("Client: " + data)
    return None


def sendCalibrationCommand():
    print("Do calibration to generate ROI")
    command = "SET:02-1"
    conn.send(command.encode())
    print("Send message to client.")
    data = str(conn.recv(1024), encoding='utf-8')
    print("Client: " + data)
    return None


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind((HOST, PORT))
s.listen(10)

while True:
    print("Wait for connection")
    conn, addr = s.accept()
    print("Connected by ", addr)
    data = str(conn.recv(1024), encoding='utf-8')
    print("Client: " + data)
    while True:
        command = input("Command: ")
        try:
            if command == "d" or command == "D":
                print(f"Command is {command}")
                sendDetectionCommand()
            elif command == "c" or command == "C":
                print(f"Command is {command}")
                sendCalibrationCommand()
            else:
                print(f"Command is {command}")
                conn.send(command.encode())
                print("Send message to client.")
                data = str(conn.recv(1024), encoding='utf-8')
                print("Client: " + data)
        except BrokenPipeError:
            print("BokenPipeError occured")
            continue

