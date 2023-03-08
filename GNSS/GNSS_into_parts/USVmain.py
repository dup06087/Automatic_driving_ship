import _thread
import math
import queue
import socket
import threading
import time
from haversine import haversine

#from matplotlib import pyplot as plt

class boat:
	def __init__(self):
		self.end = 0
		self.flag_exit = False
		self.destLat = []
		self.destLng = []

		for i in range(20):
			self.destLat.append('0')
			self.destLng.append('0')  ################initialize target destination list

		self.kp_heading = 1.9
		# ki_heading=0.0000000003
		self.ki_heading = 0.0000000002
		self.kd_heading = 0.0000003
		self.P_term_heading = 0
		self.I_term_heading = 0
		self.D_term_heading = 0
		self.err_prev = 0
		self.time_prev = 0
		self.pid_heading_max = 250
		self.pid_heading_min = 0
		self.slowdis = 15
		self.stopdis = 2
		self.savedt = 0
		self.kp_dis = 8

		QUEUE_SIZE = 30
		self.mq = queue.Queue(QUEUE_SIZE)
		self.sendToMbedQ = queue.Queue(QUEUE_SIZE)
		self.heading = 0
		self.latnow = 0
		self.lngnow = 0
		self.sendToPc = ""

		self.destindex_max = 20
		self.isready = False
		self.isdriving = False
		self.isfirst = True
		# enddriving="0"
		self.driveindex = 0
		self.recDataPc1 = "0x6,DX,37.13457284,127.98545235,SELF,0,0x3"

		#################initialize socket#################33
		# ip = '172.20.10.10' # RPi4 ip address
		self.ip = "localhost"
		# ser = serial.Serial('/dev/ttyAMA2',115200) # MBed Serial Communication Port
		self.port = 5001
		# 소켓 초기화
		self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		# 소켓 에러처리
		# self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		# self.server_socket.bind((self.ip, self.port))
		self.server_socket.connect(("localhost", 5001))
		# self.server_socket.listen()

	def pid_heading(self, err_heading):  # heading direction PID
		if self.isfirst:  ## Set first dt, err_prev, I_term_heading
			dt = 0.015
			self.err_prev = 0
			self.I_term_heading = 0
			self.isfirst = False
		time_now = time.time()
		dt = time_now - self.time_prev
		self.P_term_heading = self.kp_heading * err_heading
		self.I_term_heading += self.ki_heading * err_heading * dt
		self.D_term_heading = self.kd_heading * self.err_prev / dt
		PID_heading = self.P_term_heading + self.I_term_heading + self.D_term_heading
		self.err_prev = err_heading
		self.time_prev = time_now
		return int(abs(PID_heading))

	def azimuth(self, latnow,lngnow,lattarget,lngtarget): # compute azimuth
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

	def pid_dis(self, dis):
		P_term=self.kp_dis*dis
		return int(P_term)

	def get_data_main(self): #NMEA data
		while True:
			print("executed def")
			NMEA_data = self.server_socket.recv(1024).decode()
			if not NMEA_data:
				print("Nope")
				break
			data = eval(NMEA_data)
			# print(data)
			self.latnow = data["latitude"]
			self.lngnow = data["longitude"]
			self.heading = data["heading"]
			# xsens.getmeasure()
			# if xsens.newData == True:
			# 	xsens.newData = False
			# 	xsens.parseData()
			# 	heading=round(xsens.quat[2],2)
			# 	latnow=xsens.gps[0]
			# 	lngnow=xsens.gps[1]
				## got heading, latnow, lngnow
			recDataImu=str(self.heading)+','+str(self.latnow)+','+str(self.lngnow)
			print(recDataImu)
			#global self.flag_exit
			if self.flag_exit:
				break

	def data_processing(self):
		while True:
			self.recDataPc=self.recDataPc1.split(',')
			dis=0
			if self.heading<0:
				heading_360= -self.heading
			else:
				heading_360=abs(self.heading-360)
			heading_360=round(heading_360,2)
			azim_deg_raw=0
			if (self.recDataPc[1] == "DX"): # save latest target point
					lasttarlat = str(self.recDataPc[2])
					lasttarlng = str(self.recDataPc[3])
					mode = self.recDataPc[4]
				#######################################orders from pc
					if self.recDataPc[5] == "RE":
						# xsens.resetyaw()
						pass
					elif self.recDataPc[5] == "CD": # clear destination
						# global isfirst
						self.isfirst = True
						self.isready=False
						self.isdriving=False
						for i in range(self.destindex_max):
							self.destLat[i]='0'
							self.destLng[i]='0'
							destindex=0
						mode="SELF"
						motorright=1500
						motorleft=1500
					elif self.recDataPc[5] == "RD": # ready (save destination)
						isready = True
					elif self.recDataPc[5] == "DR": # auto drive mode
						isdriving = True
					elif self.recDataPc[5] == "SI": # save log
						# xsens.setnorotation()
						pass
					if mode=="SELF": # self drive mode
						mode = "1"
						motorright = 1500
						motorleft = 1500
						destindex=0
						self.isready=False
						self.isdriving=False

					elif mode=="AUTO": # auto mode
						mode = "2"
						motorright=1500
						motorleft=1500
						if self.isready: # ready mode : collect waypoints
							if destindex==0:
								if self.destLat[destindex]!=lasttarlat or self.destLng[destindex]!=lasttarlng:
									self.destLat[destindex]=lasttarlat
									self.destLng[destindex]=lasttarlng
									destindex+=1
							else:
								if self.destLat[destindex-1]!=lasttarlat or self.destLng[destindex-1]!=lasttarlng:
									self.destLat[destindex]=lasttarlat
									self.destLng[destindex]=lasttarlng
									destindex+=1
							driveindex=0
							timestarting=time.time()
						if self.isdriving: # autodrive mode
							enddriving="0"
							motorright=1750
							motorleft=1750
							isready=False
							if (self.destLat[driveindex]!=0 or self.destLng[driveindex]!=0):
								timenow=time.time() # plotting time
								azim_deg_raw= self.azimuth(self.latnow,self.lngnow,float(self.destLat[driveindex]),float(self.destLng[driveindex]))
								if azim_deg_raw<0:
									azim_deg=360+azim_deg_raw
								else:
									azim_deg=azim_deg_raw
								dis=haversine((self.latnow,self.lngnow),(float(self.destLat[driveindex]),float(self.destLng[driveindex])),unit="m")
								goalAng=round(azim_deg,2)

								if heading_360<180 and goalAng>180+heading_360:
									err_heading=-((360-goalAng)+heading_360)
								elif heading_360>=180 and goalAng<heading_360-180:
									err_heading=goalAng+360-heading_360
								else:
									err_heading=goalAng-heading_360 # goalAng-heading(-180~180)
								PID_heading=self.pid_heading(err_heading)
								PID_dis=self.pid_dis(dis)
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
									if dis>self.stopdis and dis<self.slowdis:
										motorright-=(PID_dis+pwm_chai)
										motorleft-=PID_dis
										if motorright<1500:
											motorright=1500
									elif dis<=self.stopdis:
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
									if dis>self.stopdis and dis<self.slowdis:
										motorright-=PID_dis
										motorleft-=(PID_dis+pwm_chai)
										if motorleft<1500:
											motorleft=1500
									elif dis<=self.stopdis:
										motorright=1500
										motorleft=1500
										driveindex+=1

			sendToMbed = "S"+mode+","+"%d" % motorleft+","+"%d" % motorright+"E"
			# global sendToPc
			self.sendToPc = hex(6)+ ","+"DX"+","+"%.2f" % (self.heading)+ "," + "%.8f" % (self.latnow)+ "," + "%.8f" % (self.lngnow)+ "," + str(motorleft)+","+str(motorright)+","+"%.2f"%(dis)+","+"%.2f"%(azim_deg_raw)+","+hex(3)
			self.sendToMbedQ.put(sendToMbed)
			# #global self.flag_exit
			if self.flag_exit:
				break

	def mbed_serial_com_main(self, ser): # rasp > mbed
		while True:
			#print("serial communication")
			sendToMbed=self.sendToMbedQ.get(True,2)
			ser.write(sendToMbed.encode())
			#print(sendToMbed)
			# #global self.flag_exit
			if self.flag_exit:
				break

	def socket_com_main(self, client_socket, addr): # rasp > pc
		while True:
			try:
				data = client_socket.recv(1024)
				if not data:
					print('Disconnected by ' + addr[0], ':', addr[1])
					break
				self.recDataPc1 = data.decode()
				client_socket.send(self.sendToPc.encode())
				# #global self.flag_exit
				if self.flag_exit:
					break
			except ConnectionResetError as e:
				print("Disconnected by", addr[0], ':', addr[1])
				print(f"e: {e}")

	def thread_start(self):
		while True:
			print("executed")
			if self.end == 1:
				break
			print("going1")
			# self.cs, self.addr = self.server_socket.accept()

			print("done?")
			try:
				t1 = threading.Thread(target=self.get_data_main)
				t1.start()
				t2 = threading.Thread(target=self.data_processing)
				t2.start()
				# t3 = threading.Thread(target=self.socket_com_main, args=(self.server_socket, self.addr))
				# t3.start()
				# t4 = threading.Thread(target=self.mbed_serial_com_main(self.ser))
				# t4.start()

			except queue.Empty:
				print("Queue is Empty")
			except KeyboardInterrupt:
				print("Ctrl+C Pressed.")
				#global self.flag_exit
				self.flag_exit = True
				t1.join()
				t2.join()
				# t3.join()
				# t4.join()
	
			print("Ok")

			# threading.Thread(target = self.GNSS_serial_com_main)
			print("def executed")

Boat = boat()
Boat.thread_start()