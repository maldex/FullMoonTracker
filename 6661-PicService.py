#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os, random, time, pprint, threading, logging, base64
import cv2, numpy, queue, threading, time
from yattag import Doc

from pprint import pprint

from flask import Flask, request, Response, render_template, send_from_directory, send_file, abort, redirect
os.environ["DISPLAY"] = "poseidon:0"
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"
vcap = cv2.VideoCapture("rtsp://127.0.0.1:8554/cam", cv2.CAP_FFMPEG)  #"rtmp://10.83.6.197/cam"


# bufferless VideoCapture
class VCOBJ:  
# https://stackoverflow.com/questions/43665208/how-to-get-the-latest-frame-from-capture-device-camera-in-opencv
  def __init__(self, source):
    self.cap = cv2.VideoCapture(source)
    self.q = queue.Queue()
    t = threading.Thread(target=self._reader)
    t.daemon = True
    t.start()

  # read frames as soon as they are available, keeping only most recent one
  def _reader(self):
    while True:
      ret, frame = self.cap.read()
      if not ret:
        print("read empty frame")
        break
      if not self.q.empty():
        try:
          self.q.get_nowait()   # discard previous (unprocessed) frame
        except queue.Empty:
          pass
      self.q.put(frame)
      time.sleep(0.1)   # simulate time between events
      cv2.imshow("frame", frame)
      #if chr(cv2.waitKey(1)&255) == 'q':
#    break

  def read(self):
    return self.q.get()

cap = VCOBJ("rtsp://127.0.0.1:8554/cam")


app = Flask(__name__, static_url_path='')
app.logger.setLevel(logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)


@app.route("/pic.jpeg")
def pic_jpeg():
    frame = cap.read()
    ret, buffer = cv2.imencode('.jpg', frame)
    frame = buffer.tobytes()
    return Response(frame, mimetype='image/jpeg')
    
@app.route("/",methods=['POST', 'GET'])
def index():
    doc, tag, text = Doc().tagtext()

    with tag('h2'):
        text("Get Data Area")

    with tag('big'):
        with tag('a', ('href', '/pic.jpeg')):
            text('get full pic')
        
    with tag('hr'):
        pass
    with tag('h2'):
        text("request.environ")
    with tag('pre'):
        for k, v in request.environ.items():
            doc.asis(str(k) + ': ' + str(v) + os.linesep)
    return Response(doc.getvalue(), mimetype='text/html;charset=UTF-8')

if __name__ == "__main__":
#  time.sleep(0.5)   # simulate time between events
#  frame = cap.read()
#  cv2.imshow("frame", frame)
#  if chr(cv2.waitKey(1)&255) == 'q':
#    break
  logging.info("starting flask")
  app.run(host='0.0.0.0', port=6660, debug=False)