import _thread
import math
import queue
import socket
import struct
import sys
import threading
import time
import json
import serial
from matplotlib import pyplot as plt

end=0
from haversine import haversine
#from matplotlib import pyplot as plt

flag_exit=False
destLat = []
destLng = []

for i in range(20):
	destLat.append('0')
	destLng.append('0') ################initialize target destination list

kp_heading=1.9
#ki_heading=0.0000000003
ki_heading=0.0000000002
kd_heading=0.0000003
P_term_heading=0
I_term_heading=0
D_term_heading=0
err_prev=0
time_prev=0
pid_heading_max=250
pid_heading_min=0
slowdis=15
stopdis=2
savedt=0

def pid_heading(err_heading): # heading direction PID
	global prev_heading,isfirst,I_term_heading,time_prev,err_prev
	global P_term_heading,I_term_heading,D_term_heading
	if isfirst:  ## Set first dt, err_prev, I_term_heading
		dt =0.015
		err_prev=0
		I_term_heading = 0
		isfirst=False
	time_now=time.time()
	dt=time_now-time_prev
	P_term_heading=kp_heading*err_heading
	I_term_heading+=ki_heading*err_heading*dt
	D_term_heading=kd_heading*err_prev/dt
	PID_heading=P_term_heading+I_term_heading+D_term_heading
	err_prev=err_heading
	time_prev=time_now
	#print('ERR:'+str(err_heading))
	#print('ERR_prev:'+str(err_prev))
	#print('P:'+str(P_term))
	#print('I:'+str(I_term_heading))
	#print('D:'+str(D_term))
	#print('elapsedtime:'+str(dt))
	#print(abs(PID_heading))
	return int(abs(PID_heading))

def azimuth(latnow,lngnow,lattarget,lngtarget): # compute azimuth
	lat1=math.radians(latnow)
	lat2=math.radians(lattarget)
	lng1=math.radians(lngnow)
	lng2=math.radians(lngtarget)
	y=math.sin(lng2-lng1)*math.cos(lat2)
	x=math.cos(lat1)*math.sin(lat2)-math.sin(lat1)*math.cos(lat2)*math.cos(lng2-lng1)
	z=math.atan2(y,x)
	azim_rad=math.atan2(y,x)
	azim_deg=math.degrees(azim_rad)
	return azim_deg
	
kp_dis=8

def pid_dis(dis):
	P_term=kp_dis*dis
	return int(P_term)

QUEUE_SIZE=30
mq=queue.Queue(QUEUE_SIZE)
sendToMbedQ=queue.Queue(QUEUE_SIZE)
heading=0
latnow=0
lngnow=0
sendToPc=""
def get_data_main():
	while True:
		print("executed def")
		global heading,latnow,lngnow
		NMEA_data = GNSS_socket.recv(1024).decode()
		if not NMEA_data:
			print("Nope")
			break
		data = eval(NMEA_data)
		# print(data)
		latnow = data["latitude"]
		lngnow = data["longitude"]
		heading = data["heading"]
		# xsens.getmeasure()
		# if xsens.newData == True:
		# 	xsens.newData = False
		# 	xsens.parseData()
		# 	heading=round(xsens.quat[2],2)
		# 	latnow=xsens.gps[0]
		# 	lngnow=xsens.gps[1]
			## got heading, latnow, lngnow
		recDataImu=str(heading)+','+str(latnow)+','+str(lngnow)
		print(recDataImu)
		global flag_exit
		if flag_exit:
			break

destindex_max=20
isready = False
isdriving = False
isfirst=True
#enddriving="0"
driveindex=0
recDataPc1="0x6,DX,37.13457284,127.98545235,SELF,0,0x3"

def data_processing():
	global isready,isdriving,isfirst
	global heading,latnow,lngnow
	global driveindex#, enddriving
	global recDataPc1
	while True:
		recDataPc=recDataPc1.split(',')
		dis=0
		if heading<0:
			heading_360= -heading
		else:
			heading_360=abs(heading-360) 
		heading_360=round(heading_360,2)
		azim_deg_raw=0
		if (recDataPc[1] == "DX"): # save latest target point
				lasttarlat = str(recDataPc[2])
				lasttarlng = str(recDataPc[3])
				mode = recDataPc[4]
			#######################################orders from pc
				if recDataPc[5] == "RE":
					# xsens.resetyaw()
					pass
				elif recDataPc[5] == "CD": # clear destination
					global isfirst
					isfirst = True
					isready=False
					isdriving=False
					for i in range(destindex_max):
						destLat[i]='0'
						destLng[i]='0'
						destindex=0
					mode="SELF"
					motorright=1500
					motorleft=1500
				elif recDataPc[5] == "RD": # ready (save destination)
					isready = True
				elif recDataPc[5] == "DR": # auto drive mode
					isdriving = True
				elif recDataPc[5] == "SI": # save log
					# xsens.setnorotation()
					pass
				if mode=="SELF": # self drive mode
					mode = "1"
					motorright = 1500
					motorleft = 1500
					destindex=0
					isready=False
					isdriving=False

				elif mode=="AUTO": # auto mode
					mode = "2"
					motorright=1500
					motorleft=1500
					if isready: # ready mode : collect waypoints
						if destindex==0:
							if destLat[destindex]!=lasttarlat or destLng[destindex]!=lasttarlng:
								destLat[destindex]=lasttarlat
								destLng[destindex]=lasttarlng
								destindex+=1
						else:
							if destLat[destindex-1]!=lasttarlat or destLng[destindex-1]!=lasttarlng:
								destLat[destindex]=lasttarlat
								destLng[destindex]=lasttarlng
								destindex+=1
						driveindex=0
						timestarting=time.time()
					if isdriving: # autodrive mode
						enddriving="0"
						motorright=1750
						motorleft=1750
						isready=False
						if (destLat[driveindex]!=0 or destLng[driveindex]!=0):
							timenow=time.time() # plotting time
							azim_deg_raw=azimuth(latnow,lngnow,float(destLat[driveindex]),float(destLng[driveindex]))
							if azim_deg_raw<0:
								azim_deg=360+azim_deg_raw
							else:
								azim_deg=azim_deg_raw
							dis=haversine((latnow,lngnow),(float(destLat[driveindex]),float(destLng[driveindex])),unit="m")
							goalAng=round(azim_deg,2)
							
							if heading_360<180 and goalAng>180+heading_360:
								err_heading=-((360-goalAng)+heading_360)
							elif heading_360>=180 and goalAng<heading_360-180:
								err_heading=goalAng+360-heading_360
							else:
								err_heading=goalAng-heading_360 # goalAng-heading(-180~180)
							PID_heading=pid_heading(err_heading)
							PID_dis=pid_dis(dis)
							pwm_chai=PID_heading*2
							if err_heading>0: # Going Right
								motorleft+=PID_heading
								motorright-=PID_heading
								if motorright>2000:
									motorright=2000
								elif motorleft>2000:
									motorleft=2000
								elif motorright<1500:
									motorright=1500
								elif motorleft<1500:
									motorleft=1500
								if dis>stopdis and dis<slowdis:
									motorright-=(PID_dis+pwm_chai)
									motorleft-=PID_dis
									if motorright<1500:
										motorright=1500
								elif dis<=stopdis:
									motorright=1500
									motorleft=1500
									driveindex+=1
							else:
								motorleft-=PID_heading # Going Left
								motorright+=PID_heading
								if motorright>2000:
									motorright=2000
								elif motorleft>2000:
									motorleft=2000
								elif motorright<1500:
									motorright=1500
								elif motorleft<1500:
									motorleft=1500
								if dis>stopdis and dis<slowdis:
									motorright-=PID_dis
									motorleft-=(PID_dis+pwm_chai)
									if motorleft<1500:
										motorleft=1500
								elif dis<=stopdis:
									motorright=1500
									motorleft=1500
									driveindex+=1

		sendToMbed = "S"+mode+","+"%d" % motorleft+","+"%d" % motorright+"E"
		global sendToPc
		sendToPc = hex(6)+ ","+"DX"+","+"%.2f" % (heading)+ "," + "%.8f" % (latnow)+ "," + "%.8f" % (lngnow)+ "," + str(motorleft)+","+str(motorright)+","+"%.2f"%(dis)+","+"%.2f"%(azim_deg_raw)+","+hex(3)
		sendToMbedQ.put(sendToMbed)
		global flag_exit
		if flag_exit:
			break
 
def mbed_serial_com_main(ser): # rasp > mbed
	while True:
		#print("serial communication")
		sendToMbed=sendToMbedQ.get(True,2)
		ser.write(sendToMbed.encode())
		#print(sendToMbed)
		global flag_exit
		if flag_exit:
			break

def socket_com_main(client_socket,addr): # rasp > pc
	while True:
		global ip,port
		global sendToPc,recDataPc1
		try:
			data = client_socket.recv(1024)
			if not data:
				print('Disconnected by ' + addr[0], ':', addr[1])
				break
			recDataPc1 = data.decode()
			client_socket.send(sendToPc.encode())
			global falg_exit
			if flag_exit:
				break
		except ConnectionResetError as e:
			print("Disconnected by", addr[0], ':', addr[1])
			print(f"e: {e}")

#################initialize socket#################33

#time.sleep(10)
# ip = '172.20.10.10' # RPi4 ip address
ip = "localhost"
# ser = serial.Serial('/dev/ttyAMA2',115200) # MBed Serial Communication Port
port = 5000
# 소켓 초기화
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# 소켓 에러처리
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((ip, port))
server_socket.listen()

GNSS_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
GNSS_socket.connect(("localhost", 5001))

def main():
	#print("Thread and Message Queue Example")
	try:
		t1=threading.Thread(target=get_data_main)
		t1.start()
		t2=threading.Thread(target=data_processing)
		t2.start()
		t3=threading.Thread(target=socket_com_main,args=(server_socket,addr))
		t3.start()
		t4=threading.Thread(target=mbed_serial_com_main(ser))
		t4.start()
	except queue.Empty:
		print("Queue is Empty")
	except KeyboardInterrupt:
		print("Ctrl+C Pressed.")
		global flag_exit
		flag_exit=True
		t1.join()
		t2.join()
		# t4.join()
print('server start')

if __name__=="__main__":
	# xsens=UART()
	while True:
		print("executed")
		if end==1:
			break
		print("done?")
		main()
		print("Ok")
		cs,addr = server_socket.accept()
		_thread.start_new_thread(socket_com_main, (cs,addr))
		print("def executed")