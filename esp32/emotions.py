import usocket as socket
import ujson
import select
import network
import machine
from math import sin, cos, radians, pi
import utime
from ST7735 import TFT
import urandom

SSID = input("Enter WiFi name: ")
PASSWORD = input("Enter WiFi Password: ")

# Pin Configuration
SPI_CLK = 18
SPI_SDA = 23
RESET_PIN = 4
DC_PIN = 2
CS_PIN = 15

# Initialize SPI
spi = machine.SPI(1, baudrate=20000000, polarity=0, phase=0, sck=machine.Pin(SPI_CLK), mosi=machine.Pin(SPI_SDA))
cs = machine.Pin(CS_PIN, machine.Pin.OUT)
dc = machine.Pin(DC_PIN, machine.Pin.OUT)
rst = machine.Pin(RESET_PIN, machine.Pin.OUT)

# Initialize display
display = TFT(spi, dc, rst, cs)
display.initr()
display.fill(0)
color = display.CYAN

# Connect to Wi-Fi
station = network.WLAN(network.STA_IF)
station.active(True)
station.connect(SSID, PASSWORD)

while not station.isconnected():
    utime.sleep(1)

print(f"Connected to Wi-Fi. IP: {station.ifconfig()[0]}")

def draw_rect(display, x, y, width, height):
    display.fillrect((x, y), (width, height), color)

def eyes_open():
    x1 = 18
    y1 = 38
    width1 = 40
    height1 = 60
    draw_rect(display, x1, y1, width1, height1)

    x2 = 128 - (x1 + width1)
    y2 = y1
    width2 = width1
    height2 = height1
    draw_rect(display, x2, y2, width2, height2)

def eyes_close():
    x1 = 18
    y1 = 64
    width1 = 40
    height1 = 3 
    draw_rect(display, x1, y1, width1, height1)

    x2 = 128 - (x1 + width1)
    y2 = y1
    width2 = width1
    height2 = height1
    draw_rect(display, x2, y2, width2, height2)

def display_arc(center, radius, start_angle, end_angle, straight=1):
    # Ensure start_angle is less than end_angle
    if start_angle > end_angle:
        start_angle, end_angle = end_angle, start_angle

    # Convert angles to radians
    start_rad = radians(start_angle)
    end_rad = radians(end_angle)

    # Number of points to approximate the arc
    num_points = int(abs(end_angle - start_angle) + 1)

    # Draw points along the arc
    for i in range(num_points):
        angle = start_rad + (end_rad - start_rad) * i / (num_points - 1)
        x = center[0] + int(radius * cos(angle) / straight)
        y = center[1] + int(radius * sin(angle))
        display.pixel((x, y), color)


def draw_happy_eyes(size, pos1, pos2):
    # Left eye
    display_arc(pos1, size, 180, 360)
    # Right eye
    display_arc(pos2, size, 180, 360)

def draw_smile(size, pos):
    display_arc(pos, size, 0, 180)

def happy(smile, smile_size, left_eye, right_eye, eye_size):
    display.fill(0)
    draw_happy_eyes(eye_size, left_eye, right_eye)
    draw_smile(smile_size, smile)
    
def draw_sorrow(size, pos, straightness):
    display_arc(pos, size, 180, 360, straightness)

def display_droplet(center, radius, straight_factor=1.7):
    num_points = 100  # Number of points to approximate the droplet shape
    offset = 0.45  # Offset factor to control the droplet shape

    for i in range(center[1], 150, 15):
        y_pos = i
        points = []
        for i in range(num_points):
            angle = 2 * i * pi / num_points
            if i < num_points // 2:
                x = center[0] + int(radius * cos(angle) / straight_factor)
                y = y_pos + int(radius * sin(angle))
                points.append((x, y))
            else:
                x = center[0] + int(radius * (1 - offset) * cos(angle))
                y = y_pos + int(radius * (1 + offset) * sin(angle))
                points.append((x, y))

        for point in points:
            display.pixel(point, color)
        
        utime.sleep(0.15)
        
        for point in points:
            display.pixel(point, display.BLACK)
        

def draw_sad_eyes(size, pos1, pos2, straightness):
    # Left eye
    display_arc(pos1, size, 0, 180, straightness)
    # Right eye
    display_arc(pos2, size, 0, 180, straightness)

def sad(sorrow, sorrow_size, left_eye, right_eye, eye_size, tear, tear_size):
    display.fill(0)
    draw_sad_eyes(eye_size, left_eye, right_eye, 0.75)
    draw_sorrow(sorrow_size, sorrow, 0.5)
    display_droplet(tear, tear_size)

def blink(time=0.01):
    global last_blink_time
    current_time = utime.ticks_ms()
    if not 'last_blink_time' in globals():
        last_blink_time = current_time
    
    if utime.ticks_diff(current_time, last_blink_time) >= time * 1000:
        display.fill(0)
        eyes_close()
        last_blink_time = current_time
    
lock = False

def see(time):
    global last_see_time, lock, delay_to_see
    current_time = utime.ticks_ms()
    if not 'last_see_time' in globals():
        last_see_time = current_time
    
    if not lock:
        delay_to_see = time
        
    if current_time - last_see_time <= delay_to_see * 1000:
        if not lock:
            lock = True
            display.fill(0)
            eyes_open()
    else:
        last_see_time = current_time
        blink()
        lock = False
        
    
def idle():
    global lock
    delay = urandom.randint(0, 7)
    # if not lock:
        # print(f"Blinking after {delay} seconds")
    see(delay)
    

radius = 40        # Radius of the arc
start_angle = 0    # Start angle in degrees
end_angle = 180    # End angle in degrees

addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
s = socket.socket()
s.bind(addr)
s.listen(1)
print('Listening on', addr)

idle()

while True:
    r, w, err = select.select([s], [], [], 0.1)
    if r:
        cl, addr = s.accept()
        print('Client connected from', addr)
        request = cl.recv(1024).decode('utf-8')
        print('Request:', request)

        response = 'HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n'
        cl.send(response)

        if 'POST' in request:
            _, payload = request.split('\r\n\r\n')
            data = ujson.loads(payload.strip())
            emotion = data.get('emotion')
            duration = data.get('duration')
            
            if emotion == 'POS':
                happy(
                    smile=(64, 90),
                    smile_size=40,
                    left_eye=(34, 60),
                    right_eye=(94, 60),
                    eye_size=25
                )
            elif emotion == 'NEG':
                sad(
                    sorrow=(64, 110),
                    sorrow_size=18,
                    left_eye=(34, 40),
                    right_eye=(94, 40),
                    eye_size=15,
                    tear=(104, 74),
                    tear_size=8
                )
            # elif emotion == "NEU":
                # idle()
            utime.sleep(duration)
            idle()
            eyes_open()
        
        cl.close()