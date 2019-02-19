import os
import sys
from termios import tcflush, TCIOFLUSH
import serial, time
#from gpiozero import Button
from time import sleep

#button = Button(18)
gateState = 0
piggyback = 0
orientation = 1

# front sensor-array sensors
ser1 = serial.Serial('/dev/cu.usbmodem1421', 115200)
ser2 = serial.Serial('/dev/cu.usbmodem1411', 115200)
#ser1 = serial.Serial('/dev/ttyUSB0', 115200)
#ser2 = serial.Serial('/dev/ttyUSB1', 115200)
#ser2 = serial.Serial('/dev/ttyACM3', 115200)
time.sleep(0.1)

ser1.flushInput()
ser2.flushInput()

#initialize motor arduino
#ser3 = serial.Serial('/dev/ttyACM2', 115200)
#time.sleep(0.1)

# initialize variables
sensors = [0,0,0,0,0] #represents five zones
smartCard = 0
gate = 0
pFlag = 0 #potential piggyback
piggyback = 0
shortFlag = 0
alarm = 0
incrementLock = 0

# timing variables
startCardTimer = False
startIdleTimer = False
startGateTimer = False
cardTimer = 0
idleTimer = 0
gateTimer = 0

#Current state of the machine
currState = 1

#Number of visitors
visitors = 0

#Helper functions
def int_check(s):
	try:
		s = s.strip()
		return int(s) if s else 0
	except(ValueError):
		pass

#Piggyback Detection
def piggyback_check(sensors):
	if sensors[0] == 1 and piggyback == 0:
		pFlag = 1
	if sensors[1] == 1 and piggyback == 1:
		piggyback = 1
		alarm = 1
	if sensors[0] == 0 and sensors[1] == 0:
		pFlag = 0
		piggyback = 0

Running = True

print('Gate Running')
#print('Zones are as follows:')
#print('-----------------')
#print('| 1 | 2 | 3 | 4 | 5 |')
#print('-----------------')

#Loop to gather readings
while Running:
	#Get readings every 0.01 seconds
	time.sleep(0.01)

	#trigger card tag if button is pressed
	'''if button.is_pressed:
		if (sensors[2] == 0 and sensors[3] == 0):
			if smartCard == 1:
				cardTimer = 0
			elif smartCard == 0:
				smartCard = 1
				currState = 4
				startCardTimer = True'''

	#turn on timer if safe flag 1
	if gate == 1 or shortFlag == 1:
		startGateTimer = True
	else:
		gateTimer = 0
		startGateTimer = False

	#Turn on alarm if alarm var is 1
	if alarm == 1:
		if piggyback == 1:
			if sensors[0] == 0 and sensors[1] == 0:
				pFlag = 0
				piggyback = 0
				alarm = 0
		elif sensors[0] == 0 and sensors[1] == 0 and sensors[2] == 0 and sensors[3] == 0 and sensors[4] == 0:
			alarm = 0
			if startIdleTimer == True:
				idleTimer = 0
				startIdleTimer = False
			if startGateTimer == True:
				gateTimer = 0
				startGateTimer = False
		else:
			print("ALARM")

#Timer rules
	if startCardTimer == True:
		cardTimer += 1
		# while loop runs every 0.1 seconds, 10 = roughly 1 sec(not accounting for program runtime)
		if cardTimer >= 100:
			startCardTimer = False
			smartCard = 0
			cardTimer = 0
	#idleTimer
	if startIdleTimer == True:
		idleTimer += 1
		if idleTimer >= 100:
#			startIdleTimer = False
#			sensors = [0,0,0,0,0,0]
#			smartCard = 0
			alarm = 1
			currState = 1

	#second timer for if gate is open too long
	if startGateTimer == True:
		gateTimer += 1
		if gateTimer >= 100:
			alarm = 1

	#Get sensor readings from all serial devices
	sensorArray1 = ser1.readline()
	sensorArray2 = ser2.readline()
	#teraranger1 = ser4.readline()
	#teraranger2 = ser5.readline()

	sensor1 = str(sensorArray1).split(',')
	sensor2 =str(sensorArray2).split(',')

	print(sensor1)
	print(sensor2)

	#Convert serial readings to int
	#tera1 = int_check(str(teraranger1).strip())
	#tera2 = int_check(str(teraranger2).strip())

	#check if serial reading is the right length, else flush
	if ((len(sensor1) < 12) or (len(sensor2) < 12)):
		ser1.flushInput()
		ser2.flushInput()
		continue

	#set the zones in array sensors[] according to hardware sensor readings
	try:
		if((int(sensor2[1]) + int(sensor1[2])) == 0):
			shortFlag = 0
		else:
			shortFlag = 1

		if(int(sensor1[1]) == 1):
			sensor[0] = 1
		else:
			sensor[0] = 0

		if(int(sensor1[2]) == 1):
			sensors[1] = 1
		else:
			sensors[1] = 0

		if (int(sensor2[1]) == 1):
			sensors[2] = 1
		else:
			sensors[2] = 0

		if (int(sensor2[2]) == 1):
			sensors[3] = 1
		else:
			sensors[3] = 0

	except (ValueError, IndexError):
		continue

	#Set orientation
	if orientation == 0:
		sensors = sensors[::-1]
		#piggybackThreshold = tera2
	#else:
		#piggybackThreshold = tera1

	#Piggyback Detection
        #if (currState == 5 or currState == 6):
        #        if (piggybackThreshold > 220 and piggybackThreshold < 500):
        #                piggyback = 1
        #if sensors[0] == 0 and sensors[1] == 0 and sensors[2] == 0 and sensors[3] == 0 and shortFlag == 0:
        #        piggyback = 0


	#Set state rules
	if currState == 1:
		if sensors[0] == 1:
			startIdleTimer = False
			idleTimer = 0
			currState = 2 #set currState = 2 when sensor[1] = 1???
		elif (sensors[1] or sensors[2] or sensors[3] == 1):
			startIdleTimer = True
	elif currState == 2:
		startIdleTimer = True
		if sensors[1] == 1:
			startIdleTimer = False
			idleTimer = 0
			currState = 3
	elif currState == 3:
		startIdleTimer = True
		if smartCard == 1: #contactless card reader
			startIdleTimer = False
			idleTimer = 0
			currState = 4
	elif currState == 4:
		startIdleTimer = True
		startGateTimer = True
		gate = 1
		ser3.write("o")
		if incrementLock == 0:
			visitors += 1
			incrementLock = 1
		if sensors[2] == 1:
			startIdleTimer = False
			idleTimer = 0
			currState = 5
	elif currState == 5:
		startGateTimer = True
		if sensors[2] == 0:
			startGateTimer = False
			gateTimer = 0
			currState = 6
		#piggyback Algorithm
		piggyback_check(sensors)
	elif currState == 6:
		smartCard = 0
		if sensors[3] == 1:
			currState = 7
		#piggyback Algorithm
		piggyback_check(sensors)
	elif currState == 7:
		if sensors[4] == 1:
			currState = 8
		piggyback_check(sensors)
	elif currState == 8:
		gate = 0
		ser3.write("c")
		if incrementLock == 1:
			incrementLock = 0
		startIdleTimer = True
		if sensors [3] == 0:
			currState = 1

	#Writes information to data.txt to use with flask server
	f = open('data.txt', 'w')
	printstr = str(sensors[0]) + str(sensors[1]) + str(sensors[2]) + str(sensors[3]) + str(gate) + str(smartCard) + str(currState) + str(shortFlag) + str(orientation) + str(piggyback)
	f.write(printstr)
	f.write("\n")
	f.write(str(visitors))
	f.close()

	#For debugging only
	#print('gate:' + str(gate) + ' sensors:' + str(sensors[0]) + str(sensors[1]) + str(sensors[2]) + str(sensors[3]) + ' card:' + str(smartCard) + ' state:' + str(currState) + " flag:" + str(shortFlag))

	#flush inputs
	ser1.flushInput()
	ser2.flushInput()
	#ser4.flushInput()
	#ser5.flushInput()
