from flask import Flask, render_template_string, Response, request
import cv2
import RPi.GPIO as GPIO

# === GPIO Setup ===
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

in1, in2, in3, in4 = 17, 18, 22, 23
for pin in [in1, in2, in3, in4]:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

def move_forward():
    GPIO.output(in1, GPIO.HIGH)
    GPIO.output(in2, GPIO.LOW)
    GPIO.output(in3, GPIO.HIGH)
    GPIO.output(in4, GPIO.LOW)

def move_backward():
    GPIO.output(in1, GPIO.LOW)
    GPIO.output(in2, GPIO.HIGH)
    GPIO.output(in3, GPIO.LOW)
    GPIO.output(in4, GPIO.HIGH)

def turn_left():
    GPIO.output(in1, GPIO.LOW)
    GPIO.output(in2, GPIO.HIGH)
    GPIO.output(in3, GPIO.HIGH)
    GPIO.output(in4, GPIO.LOW)

def turn_right():
    GPIO.output(in1, GPIO.HIGH)
    GPIO.output(in2, GPIO.LOW)
    GPIO.output(in3, GPIO.LOW)
    GPIO.output(in4, GPIO.HIGH)

def stop():
    for pin in [in1, in2, in3, in4]:
        GPIO.output(pin, GPIO.LOW)

# === Camera Setup ===
camera = cv2.VideoCapture(0)

def gen_frames():
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            _, buffer = cv2.imencode('.jpg', frame)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

# === Flask App ===
app = Flask(__name__)

html_page = """
<!DOCTYPE html>
<html>
<head>
    <title>Robot Control</title>
    <style>
        body { text-align: center; background: #222; color: white; }
        video { border: 3px solid white; width: 70%; }
        button { padding: 20px; margin: 10px; font-size: 20px; }
    </style>
</head>
<body>
    <h1>Robot Control</h1>
    <video autoplay="true" id="videoFeed"></video><br>
    <img src="{{ url_for('video_feed') }}">

    <div>
        <button onclick="move('forward')">Forward (W)</button><br>
        <button onclick="move('left')">Left (A)</button>
        <button onclick="move('stop')">Stop (Space)</button>
        <button onclick="move('right')">Right (D)</button><br>
        <button onclick="move('backward')">Backward (S)</button>
    </div>

    <script>
        function move(direction) {
            fetch('/move?dir=' + direction);
        }

        document.addEventListener('keydown', function(event) {
            switch(event.key.toLowerCase()) {
                case 'w': move('forward'); break;
                case 's': move('backward'); break;
                case 'a': move('left'); break;
                case 'd': move('right'); break;
                case ' ': move('stop'); break;
            }
        });

        document.addEventListener('keyup', function(event) {
            move('stop');
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(html_page)

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/move')
def move():
    direction = request.args.get('dir')
    if direction == "forward":
        move_forward()
    elif direction == "backward":
        move_backward()
    elif direction == "left":
        turn_left()
    elif direction == "right":
        turn_right()
    else:
        stop()
    return ('', 204)

if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=5000)
    finally:
        GPIO.cleanup()
