FROM python:3.6.1-alpine
RUN pip install flask
RUN pip install pymysql
RUN pip install os
RUN pip install ibm-cos-sdk
RUN pip install pyodbc
