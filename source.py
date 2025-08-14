import io
import time
import RPi.GPIO as GPIO
import picamera
from flask import Flask, Response, render_template_string, request

# ===== GPIO SETUP =====
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Motor pins (BCM numbering)
# L298N Board 1
M1_IN1 = 17  # Front-left motor forward
M1_IN2 = 18  # Front-left motor backward
M2_IN1 = 22  # Front-right motor forward
M2_IN2 = 23  # Front-right motor backward

# L298N Board 2
M3_IN1 = 24  # Rear-left motor forward
M3_IN2 = 25  # Rear-left motor backward
M4_IN1 = 5   # Rear-right motor forward
M4_IN2 = 6   # Rear-right motor backward

motor_pins = [M1_IN1, M1_IN2, M2_IN1, M2_IN2, M3_IN1, M3_IN2, M4_IN1, M4_IN2]
for pin in motor_pins:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

# ===== MOTOR CONTROL FUNCTIONS =====
def stop_all():
    for pin in motor_pins:
        GPIO.output(pin, GPIO.LOW)

def forward():
    GPIO.output(M1_IN1, GPIO.HIGH)
    GPIO.output(M1_IN2, GPIO.LOW)
    GPIO.output(M2_IN1, GPIO.HIGH)
    GPIO.output(M2_IN2, GPIO.LOW)
    GPIO.output(M3_IN1, GPIO.HIGH)
    GPIO.output(M3_IN2, GPIO.LOW)
    GPIO.output(M4_IN1, GPIO.HIGH)
    GPIO.output(M4_IN2, GPIO.LOW)

def backward():
    GPIO.output(M1_IN1, GPIO.LOW)
    GPIO.output(M1_IN2, GPIO.HIGH)
    GPIO.output(M2_IN1, GPIO.LOW)
    GPIO.output(M2_IN2, GPIO.HIGH)
    GPIO.output(M3_IN1, GPIO.LOW)
    GPIO.output(M3_IN2, GPIO.HIGH)
    GPIO.output(M4_IN1, GPIO.LOW)
    GPIO.output(M4_IN2, GPIO.HIGH)

def left():
    GPIO.output(M1_IN1, GPIO.LOW)
    GPIO.output(M1_IN2, GPIO.HIGH)
    GPIO.output(M2_IN1, GPIO.HIGH)
    GPIO.output(M2_IN2, GPIO.LOW)
    GPIO.output(M3_IN1, GPIO.LOW)
    GPIO.output(M3_IN2, GPIO.HIGH)
    GPIO.output(M4_IN1, GPIO.HIGH)
    GPIO.output(M4_IN2, GPIO.LOW)

def right():
    GPIO.output(M1_IN1, GPIO.HIGH)
    GPIO.output(M1_IN2, GPIO.LOW)
    GPIO.output(M2_IN1, GPIO.LOW)
    GPIO.output(M2_IN2, GPIO.HIGH)
    GPIO.output(M3_IN1, GPIO.HIGH)
    GPIO.output(M3_IN2, GPIO.LOW)
    GPIO.output(M4_IN1, GPIO.LOW)
    GPIO.output(M4_IN2, GPIO.HIGH)

# ===== FLASK APP =====
app = Flask(__name__)

# Video feed generator
def generate_frames():
    with picamera.PiCamera() as camera:
        camera.resolution = (640, 480)
        camera.framerate = 24
        time.sleep(2)
        stream = io.BytesIO()
        for _ in camera.capture_continuous(stream, format='jpeg', use_video_port=True):
            stream.seek(0)
            frame = stream.read()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            stream.seek(0)
            stream.truncate()

@app.route('/')
def index():
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>Robot Controller</title>
    <style>
        body { background-color: #111; color: white; text-align: center; font-family: Arial; }
        img { border: 4px solid #444; border-radius: 8px; }
        .controls { margin-top: 20px; }
        button { width: 80px; height: 80px; font-size: 24px; margin: 5px; border-radius: 10px; border: none; background: #333; color: white; }
        button:active { background: #555; }
    </style>
</head>
<body>
    <h1>Raspberry Pi Robot</h1>
    <img src="{{ url_for('video_feed') }}" width="640" height="480">
    <div class="controls">
        <div>
            <button onmousedown="sendCmd('forward')" onmouseup="sendCmd('stop')">W</button>
        </div>
        <div>
            <button onmousedown="sendCmd('left')" onmouseup="sendCmd('stop')">A</button>
            <button onmousedown="sendCmd('backward')" onmouseup="sendCmd('stop')">S</button>
            <button onmousedown="sendCmd('right')" onmouseup="sendCmd('stop')">D</button>
        </div>
    </div>
    <script>
        document.addEventListener('keydown', function(e) {
            if(e.repeat) return; // prevent holding spam
            if (e.key === 'w') sendCmd('forward');
            if (e.key === 's') sendCmd('backward');
            if (e.key === 'a') sendCmd('left');
            if (e.key === 'd') sendCmd('right');
        });
        document.addEventListener('keyup', function(e) {
            if(['w','a','s','d'].includes(e.key)) sendCmd('stop');
        });
        function sendCmd(cmd) {
            fetch('/move?dir=' + cmd);
        }
    </script>
</body>
</html>
''')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/move')
def move():
    direction = request.args.get('dir')
    if direction == 'forward':
        forward()
    elif direction == 'backward':
        backward()
    elif direction == 'left':
        left()
    elif direction == 'right':
        right()
    elif direction == 'stop':
        stop_all()
    return ('', 204)

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000, threaded=True)
    finally:
        GPIO.cleanup()
