#!/usr/bin/python3

from calibration import Calibration
from detection import Detection
from Ct_calculation import ct_calculation
from public_method import initialize
from merge import merge
from time import sleep
import socket
import time


def main():
    initialize()
    HOST = '127.0.0.1'
    PORT = 8888
    framerate = 2
    iso = 200

    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((HOST, PORT))
            s.setblocking(False)    # use non-blocking mode
            s.send('Hello'.encode())
            print("Connect to server")

            while True:
                try:
                    s.setblocking(False)    # use non-blocking mode
                    s.connect((HOST, PORT))

                except OSError:  # already connect
                    try:
                        sleep(1)
                        k = ''
                        k = str(s.recv(1024), encoding='utf-8')
                        print("Incoming command: " + k + '\n')
                        if not len(k):
                            print("Connection lost")
                            break
                        elif 'SET:02-1' in k:  # calibrate for calibration dye
                            try:
                                CA_msg = Calibration.calibrate_for_dye(framerate, iso)
                                # convert CA_msg to the protocol format
                                msg = ''
                                for i, context in enumerate(CA_msg):
                                    if context < 10:
                                        msg += ('00'+str(context))
                                    elif context < 100:
                                        msg += ('0'+str(context))
                                    else:
                                        msg += str(context)
                                    if i != len(CA_msg)-1:
                                        msg += ','
                                print("Calibration done!")
                                print(f"CA:{msg}")
                                s.sendall(f"CA:{msg}".encode())
                                print("Send data to server")

                            except Exception as exc:
                                print(f"Error message: {exc}")
                                print("Calibration failed!")
                                s.sendall("CA:ERROR".encode())
                                print("Send data to server")

                        elif 'SET:02-2' in k:  # calibrate for water strip
                            try:
                                if Calibration.check_necessity():
                                    CT_msg = Calibration.calibrate_for_water(framerate, iso)
                                    # convert CT_msg to the protocol format
                                    msg = ''
                                    for i, context in enumerate(CT_msg):
                                        if context < 10:
                                            msg += ('00'+str(context))
                                        elif context < 100:
                                            msg += ('0'+str(context))
                                        else:
                                            msg += str(context)
                                        if i != len(CT_msg)-1:
                                            msg += ','
                                    print("Detection done!")
                                    print(f"CT:{msg}")
                                    merge()
                                    print("ROI Merge Finish")
                                    s.sendall(f"CT:{msg}".encode())
                                    print("Send data to server")
                                else:
                                    print("Calibration unsuccessful!")
                                    s.sendall("CT:ERROR".encode())
                                    print("Send data to server")

                            except Exception as exc:
                                print(f"Error message: {exc}")
                                print("Calibration failed!")
                                s.sendall("CA:ERROR".encode())
                                print("Send data to server")

                        elif 'SET:01' in k:  # detection
                            if Detection.check_necessity():
                                CT_msg = Detection.detect(framerate, iso)
                                # convert CT_msg to the protocol format
                                msg = ''
                                for i, context in enumerate(CT_msg):
                                    if context < 10:
                                        msg += ('00'+str(context))
                                    elif context < 100:
                                        msg += ('0'+str(context))
                                    else:
                                        msg += str(context)
                                    if i != len(CT_msg)-1:
                                        msg += ','
                                print("Detection done!")
                                print(f"CT:{msg}")
                                s.sendall(f"CT:{msg}".encode())
                                print("Send data to server")
                            else:
                                print("You have to do calibration first!")
                                s.sendall("CT:ERROR".encode())
                                print("Send data to server")

                        elif 'SET:03' in k:  # Ct calculation
                            """
                            the following parameters reprsent the range of baseline
                            example: SET:03,00035,00320 for baseline is between 3.5~32 mins
                            """
                            # Since the first data starts from 0 minute, the number of recorded data needs to be increased by 1,
                            # so that 3.5 minutes should map to 8 ,which is "35 / 5 + 1", to point to the correct data
                            baseline_begin = int(int(k[7:12])/5)+1
                            baseline_end = int(int(k[13:18])/5)+1
                            print(f"Baseline is from {baseline_begin} to {baseline_end}")
                            CT_msg = ct_calculation(baseline_begin, baseline_end)
                            # convert CT_msg to the protocol format
                            msg = ''
                            for i, context in enumerate(CT_msg):
                                context_str = str(context)
                                if len(context_str) == 5:
                                    msg += context_str
                                elif len(context_str) == 4:
                                    if context > 10:
                                        msg += (context_str+'0')
                                    else:
                                        msg += ('0'+context_str)
                                elif len(context_str) == 3:
                                    msg += ('0'+context_str+'0')
                                if i != len(CT_msg)-1:
                                    msg += ','
                            print("Ct_calculation done!")
                            print(f"CT:{msg}")
                            s.sendall(f"CT:{msg}".encode())
                            print("Send data to server")

                        elif 'SET:00' in k:  # change camera parameters; example: SET:00,01,80 for framerate=1, ISO=800
                            try:
                                framerate = int(k[7:9])
                                iso = int(k[10:12])*10
                                s.sendall(f"ISO:0x{k[10:12]}".encode())
                                print("Send data to server")
                                print(f"Set shutter speed to {1/framerate} second(s), ISO to {iso}")
                            except:
                                s.sendall("ISO:ERROR".encode())
                                print("Send data to server")
                        else:    # incorrect formate of message
                                print("Incorrect message formate from server!")
                                s.sendall("Incorrect message formate, please check and sent it again!".encode())

                    except BlockingIOError:
                        sleep(1)
                        seconds = time.time()
                        local_time = time.ctime(seconds)
                        print("now:", local_time , "server is still connected")

                        continue

                    except (ConnectionResetError, BrokenPipeError):
                        print("Connection lost, re-connect")
                        break

        except ConnectionRefusedError:
            s.close()
            print("Cannot connect to server, try again...")
            sleep(1)


if __name__ == "__main__":
    main()
