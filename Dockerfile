FROM python:3.7.8-buster

RUN apt update && apt install -y tesseract-ocr
RUN pip install pytube3 opencv-python pytesseract numpy google-api-python-client scikit-image

RUN mkdir /app
ADD fraud_detector.py /app/

ENTRYPOINT [ "python", "/app/fraud_detector.py"]
