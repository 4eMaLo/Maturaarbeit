import socket, sys, re, struct, select
from PIL import Image, ImageDraw
import time

class Worker:
	data_pointer = 0
	data_buffer = ""

	data_received = 0

	def __init__(self, conn, resolution, center, radius, max_iter):
		self.conn = conn

		self.resolution = resolution
		self.center = center
		self.radius = radius
		self.max_iter = max_iter

	def start_job(self,  area):
		self.area = area
		query = "x={} y={} c={} r={} iter={} area={}x{}+{}+{}".format(
			self.resolution[0], self.resolution[1],
			repr(self.center)[1:-1], # Removes the brackets
			self.radius,
			self.max_iter,
				area[0],
				area[1],
				area[2],
				area[3]
		)
		addr = self.conn.getpeername()
		print "%s:%d - %s" % (addr[0], addr[1], query)
		self.conn.send(query)

	def recv_data(self):
		while len(self.data_buffer) < 2*self.area[0]*self.area[1]:
			self.data_buffer += self.conn.recv(8192)

		self.data_received = 1

	def buffer_get(self):
		temp = struct.unpack("H", self.data_buffer[self.data_pointer:self.data_pointer+2])[0]
		self.data_pointer += 2
		return temp

	def fileno(self):
		return self.conn.fileno()






if len(sys.argv) < 6:
	print "usage: %s resolution center radius maxiter addresses..."

	print " example:"
	print "   resolution: 512x512"
	print "   center:     -0.5+0i"
	print "   radius:     2.0"
	print "   maxiter:    64"
	print "   address:    [IP]:[Port]"
	exit(1)




# ---- Parse parameters -------------------------------------------------------
m = re.match(r'^(\d+)[x\*](\d+)', sys.argv[1])
if m:
	resolution = int(m.group(1)), int(m.group(2))
else:
	print "Invalid resolution"
	exit(1)

m = re.match(r'^(-?\d+\.?\d*)\+?(-?\d+\.?\d*)i', sys.argv[2])
if m:
	center = complex( float(m.group(1)), float(m.group(2)) )
else:
	print "Invalid center"
	exit(1)

m = re.match(r'^(\d+\.?\d*)', sys.argv[3])
if m:
	radius = float(m.group(1))
else:
	print "Invalid radius"
	exit(1)

m = re.match(r'^(\d+)', sys.argv[4])
if m:
	max_iter = int(m.group(1))
else:
	print "Invalid maximum iterations"
	exit(1)
# -----------------------------------------------------------------------------



worker_addr_list = []
for addr in sys.argv[5:]:
	m = re.match(r'^(.*)\:(\d+)', addr)
	if m:
		worker_addr_list.append(( m.group(1),int(m.group(2)) ))


worker_list = []
for addr in worker_addr_list:
	conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	conn.connect(addr)
	temp = Worker(conn, resolution, center, radius, max_iter)
	worker_list.append(temp)
ind = 0
worker_count = len(worker_list)
width = resolution[0]
height = resolution[1]/worker_count

job_start_time = time.time()

while ind < worker_count:
	if ind == worker_count -1 :
		worker_list[ind].start_job(
			(width, resolution[1]-height*(worker_count-1), 0, ind*height)
		)
	else:
		worker_list[ind].start_job(
			(width, height, 0, ind * height)
		)
	ind+=1


im = Image.new("RGB", resolution, "black")
pixels = im.load()


all_data_received = False
while not all_data_received:
	read = select.select( worker_list, [], [] )[0]
	for obj in read:
		obj.recv_data()


	if sum([obj.data_received for obj in worker_list]) == len(worker_list):
		all_data_received = True


job_stop_time = time.time()
for worker in worker_list:
	area = worker.area

	for x_pix in range(area[2],area[2]+area[0]):
		for y_pix in range(area[3],area[3]+area[1]):
			pix_value = int(worker.buffer_get() * 1.0/max_iter * 255)
			pixels[x_pix,y_pix] = ( pix_value, pix_value, pix_value )


print "Calculation Time:", job_stop_time - job_start_time
im.save("test_image.png", "PNG")



for worker in worker_list:
	worker.conn.close()


im.show()
