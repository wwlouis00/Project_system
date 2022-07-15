# Describtion

This file is for Winnoz's eGGi usage.

## For development, testing & debugging

### Modify permission

```bash
cd "Project_directory"/socket_cam
chmod +x main.py
chmod +x autostart.sh
```

### Rewrite autostart file

```bash
cd /etc/xdg/lxsession/LXDE-pi
```

Then use editor(nano, vim... whatever you like) to add following word at the last of "autostart"

```
@"Project_directory"/socket_cam/autostart.sh &
```

## For product usage (no py file)

### Generate .pyc file and copy autostart.sh to /home/pi/socket

```bash
cd "Project_directory"/socket_cam
chmod +x compile2pyc.sh
./compile2pyc.sh
```

### Rewrite autostart file

```bash
cd /etc/xdg/lxsession/LXDE-pi
```

Then use editor(nano, vim... whatever you like) to add following word at the last of "autostart"

```
@/home/pi/socket_cam/autostart.sh &
```
