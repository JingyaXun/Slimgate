import os
import sys
from termios import tcflush, TCIOFLUSH
import serial, time
from time import sleep
import RPi.GPIO as GPIO
from gpiozero import Button

# GPIO setup
motor_output_pin = 18 #active on high
alarm_pin = 23 #active on low
GPIO.setmode(GPIO.BCM)
GPIO.setup(motor_output_pin, GPIO.OUT)
GPIO.output(motor_output_pin, GPIO.HIGH)
GPIO.setup(alarm_pin, GPIO.OUT)
GPIO.output(alarm_pin, GPIO.HIGH)

button = Button(22)
gateState = 0
piggyback = 0
orientation = 1

# front sensor-array sensors_up
#ser1 = serial.Serial('/dev/cu.usbmodem1421', 115200)
#ser2 = serial.Serial('/dev/cu.usbmodem1411', 115200)

# connect directly to rasp pi
ser1 = serial.Serial('/dev/ttyACM0', 115200) # upper left sensor arr
ser2 = serial.Serial('/dev/ttyACM1', 115200) # upper right sensor arr
ser3 = serial.Serial() # lower left sensor arr
ser4 = serial.Serial() # lower right sensor arr

#ser3 = serial.Serial('/dev/ttyUSB1', 115200)
ser3.write('T')
ser3.write('P')

#ser2 = serial.Serial('/dev/ttyACM3', 115200)

time.sleep(0.1)

ser1.flushInput()
ser2.flushInput()
ser3.flushInput()
ser4.flushInput()

# initialize variables
sensors_up = [0,0,0,0,0] #represents five zones
sensors_down = [0,0,0,0,0]
smartCard = 0
gate = 0
pFlag = 0 #potential piggyback
piggyback = 0
button_disabled = 0;
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

def piggyback_check(sensors_up sensors_down, pFlag,piggyback, alarm):
        f = open("data.txt", "a")
	f.write("PIGGYBACK"+str(sensors_up))
	f.write("\n")
	f.close()
	#print(type(sensors_up[0]))
	#print(sensors_up[0])
	if sensors_up[0] == 1 and sensors_down[0] == 1:
		pFlag = 1
	if pFlag == 1 and sensors_up[1] == 1 and sensors_down[1] == 1:
                piggyback = 1
                alarm = 1
        else:
                pFlag = 0
        
	return piggyback, alarm

def luggage_check(sensors_up, sensors_down):
        isLuggage = 0
        for i in len(sensors_up):
                if sensors_up[i] == 0 and sensors_down[i] == 1:
                        isLuggage = 1
        return isLuggage

def safety_check(sensors_up, sensors_down):
        if sensors_up[2] == 0 and sensors_down[2] == 0:
                return true
        else:
                return false

def all_clear(sensors_up, sensors_down):
        if sensors_up[0] == 0 and sensors_up[1] == 0 and sensors_up[2] == 0 and sensors_up[3] == 0 and sensors_up[4] == 0 and \
        sensors_down[0] == 0 and sensors_down[1] == 0 and sensors_down[2] == 0 and sensors_down[3] == 0 and sensors_down[4] == 0:
                return true
        else:
                return false

Running = True

print('Gate Running')
print('Zones are as follows:')
print('-----------------')
print('| 1 | 2 | 3 | 4 | 5 |')

#Loop to gather readings
while Running:
	#Get readings every 0.01 seconds
	time.sleep(0.01)

	#trigger card tag if button is pressed
	if not button.is_pressed: # button active on low
                if button_disabled == 0:
                        if smartCard == 0:
                                smartCard = 1
                                startCardTimer = True
                        button_disabled = 1

	#Turn on alarm if alarm var is 1
	if alarm == 1:
                if piggyback == 1:
			if sensors_up[0] == 0 and sensors_up[1] == 0:
				pFlag = 0
				piggyback = 0
				alarm = 0
				GPIO.output(alarm_pin, GPIO.HIGH)
			GPIO.output(alarm_pin, GPIO.LOW)
		if all_clear(sensors_up, sensors_down):
                        pFlag, piggyback, alarm = 0
			GPIO.output(alarm_pin, GPIO.HIGH)
			if startIdleTimer == True:
				idleTimer = 0
				startIdleTimer = False
			if startGateTimer == True:
				gateTimer = 0
				startGateTimer = False
		else:
                        GPIO.output(alarm_pin, GPIO.LOW)	

#Timer rules
	if startCardTimer == True:
		cardTimer += 1
		# while loop runs every 0.1 seconds, 10 = roughly 1 sec(not accounting for program runtime)
		if cardTimer >= 200:
			startCardTimer = False
			smartCard = 0
			cardTimer = 0
	#idleTimer
	if startIdleTimer == True:
		idleTimer += 1
		if idleTimer >= 100:
			alarm = 1
			currState = 1

	#second timer for if gate is open too long
	if startGateTimer == True:
		gateTimer += 1
		if gateTimer >= 350:
			alarm = 1

	#Get sensor readings from all serial devices
	sensorArray1 = ser1.readline()
	sensorArray2 = ser2.readline()
        sensorArray3 = ser3.readline()
        sensorArray4 = ser4.readline()
        
	sensor1_up = str(sensorArray1).split(",")
	sensor2_up =str(sensorArray2).split(",")
	sensor1_up[-1] = sensor1_up[-1].strip()
	sensor2_up[-1] = sensor2_up[-1].strip()

        sensor1_down = str(sensorArray1).split(",")
	sensor2_down =str(sensorArray2).split(",")
	sensor1_down[-1] = sensor1_up[-1].strip()
	sensor2_down[-1] = sensor2_up[-1].strip()
	
	print(sensor1_up)
	#print(len(sensor1_up))
	print(sensor2_up)
	#print(len(sensor2_up))
       
	#check if serial reading is the right length, else flush
	if ((len(sensor1_up) < 14) or (len(sensor2_up) < 14)):
		ser1.flushInput()
		ser2.flushInput()
		continue

	#set the zones in array sensors_up[] according to hardware sensor readings
	try:
		if(int(sensor1_up[3]) == 1):
			sensors_up[0] = 1
		else:
			sensors_up[0] = 0

		if(int(sensor1_up[1]) == 1):
			sensors_up[1] = 1
		else:
			sensors_up[1] = 0
		
		#if(int(sensor1_up[5]) == 1 and int(sensor2_up[5]) == 1):
                #        sensors_up[2] = 1
                #else:
                #        sensors_up[2] = 0
                
                if(int(sensor1_up[5]) == 1):
                        sensors_up[2] = 1
                else:
                        sensors_up[2] = 0
                
                if (int(sensor2_up[1]) == 1):
			sensors_up[3] = 1
		else:
			sensors_up[3] = 0

		if (int(sensor2_up[3]) == 1):
			sensors_up[4] = 1
		else:
			sensors_up[4] = 0
		
		print(sensors_up)
		print("current state: " + str(currState))
		print("######################################\n")
        
	except (ValueError, IndexError):
		continue
	
	#Set state rules
	if currState == 1:
		if sensors_up[0] == 1:
			startIdleTimer = False
			idleTimer = 0
			currState = 2
		elif (sensors_up[1] or sensors_up[2] or sensors_up[3] == 1):
			startIdleTimer = True
	elif currState == 2:
		startIdleTimer = True
		if sensors_up[1] == 1:
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
		# open gate
		GPIO.output(motor_output_pin, GPIO.LOW)
		print("GATE OPEN")
		if incrementLock == 0:
			visitors += 1
			incrementLock = 1
		if sensors_up[2] == 1:
			startIdleTimer = False
			idleTimer = 0
			currState = 5
		#piggyback, alarm = piggyback_check(sensors_up, pFlag, piggyback, alarm)
	elif currState == 5:
		startGateTimer = True
		if sensors_up[2] == 0:
			startGateTimer = False
			gateTimer = 0
			currState = 6
		#piggyback, alarm = piggyback_check(sensors_up, pFlag, piggyback, alarm)
	elif currState == 6:
		if sensors_up[3] == 1:
			currState = 7
		piggyback, alarm = piggyback_check(sensors_up, pFlag, piggyback, alarm)
	elif currState == 7:
		if sensors_up[4] == 1:
			currState = 8
		piggyback, alarm = piggyback_check(sensors_up, pFlag, piggyback, alarm)
	elif currState == 8:
		startIdleTimer = True
		if all_clear(sensors_up, sensors_down):
                       # close gate
                        gate = 0
                        GPIO.output(motor_output_pin, GPIO.HIGH)
                        print("GATE CLOSE")
                        if incrementLock == 1:
                                incrementLock = 0
			currState = 1
			button_disabled = 0
			smartcard = 0
                piggyback, alarm = piggyback_check(sensors_up, pFlag, piggyback, alarm)

	#Writes information to data.txt (for debugging purpose)
        f = open("data.txt", "a")
	f.write(str(sensors_up))
	f.write(str(currState) + " ")
	f.write(str(piggyback) + " ")
	f.write(str(alarm) + " ")
	f.write("\n")
	f.close()

	#flush inputs
	ser1.flushInput()
	ser2.flushInput()
	ser3.flushInput()
	ser4.flushInput()

