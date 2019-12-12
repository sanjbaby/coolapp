FROM python:3.6.1-alpine
RUN pip install --upgrade pip
RUN pip install flask
RUN pip install pymysql
RUN pip install ibm-cos-sdk
RUN apk add --no-cache g++ libc-dev unixodbc-dev
RUN pip install pyodbc
