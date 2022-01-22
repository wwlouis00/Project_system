#!/usr/bin/python3
from time import sleep
import cv2 as cv
import socket

def main():
    host = '127.0.0.1'
    port = 8888
    framerate = 2
    iso = 200

    while True:
        try:
            s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            s.connect((host,port))
            s.setblocking(False) #取消socket預設的阻塞狀態 將此socket設成非阻塞
            s.send("哈囉".encode())
            print("連接伺服器")

            while True:
                try:
                    s.setblocking(False)
                    s.connect((host,port))

                except OSError:
