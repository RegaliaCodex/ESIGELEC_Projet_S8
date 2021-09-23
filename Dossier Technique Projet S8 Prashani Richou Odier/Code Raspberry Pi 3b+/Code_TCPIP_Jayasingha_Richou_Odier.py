	#!/usr/bin/env python2

#RICHOU Jacques | ODIER Raphael | JAYASINGHA Prashani

#imports of libraries
from csv import reader
import csv
import socket
import sys
from time import sleep

# Create a  TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect the socket to the port where the server is listening
server_address = ('0.0.0.0', 1202)
print >>sys.stderr, 'connecting to %s port %s' % server_address
sock.bind(server_address)
sock.listen(1)

#read csv file
#list  = []
#with open('test.csv','r') as csvfile:
#    for row  in csvfile:
#        reader = csv.reader(csvfile, delimiter = '\n')
#        list.append(str(row))


#connection to the client
while True:
    connection, client_address = sock.accept()
    print >>sys.stderr, 'waiting for connection'
    try:
       print >>sys.stderr, 'connection from', client_address
       #opening the csv file
       with open ('test.csv', 'r') as csv_file:
         csv_reader = csv.reader(csv_file, delimiter = '\n')
         #reading the csv file line by line
         for row in csv_reader:
            #adding the read line to a variable without the brackets
            message = str(row)[1:-1]
            #sending the read line
            print >>sys.stderr, 'sending "%s"' % message
            connection.send(message)
            sleep(1)

    finally:
          print >>sys.stderr, 'closing socket'
          connection.close()


