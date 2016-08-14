import socket, sys, re, math, struct, random, os

def calc_point(c, max_iter):
	z = 0
	cur_iter = 0
	while cur_iter < max_iter:
		z = z**2 + c
		if z.real**2 + z.imag**2 > 4:
			return cur_iter
		cur_iter +=1
	return 0

def LOG(str):
	print str

def calc_mandelbrot_area(center, radius, max_iter, resolution, area):
	filename = "/tmp/temp_file_%s.dat" % random.randint(0,10000)
	if os.path.exists(filename):
		filename = "/tmp/temp_file_%s.dat" % random.randint(0,10000)

	LOG("Started calculation...")
	LOG("Center: {}".format(repr(center)))
	LOG("Area: {},{} offset {},{}".format(area[0], area[1],area[2],area[3]))

	f = open(filename, 'w')

	phi = math.atan(resolution[1]*1.0/resolution[0])

	x1 = math.cos(phi)* radius
	y1 = math.sin(phi)* radius

	real_min, real_max, imag_max, imag_min = center.real-x1, center.real+x1, center.imag+y1, center.imag-y1

	vpp_real = (real_max-real_min)* 1.0/resolution[0]
	vpp_imag = (imag_max-imag_min)* 1.0/resolution[1]


	for x_pix in range(area[2], area[2]+area[0]):
		for y_pix in range(area[3], area[3]+area[1]):
			point_z = complex(
				vpp_real*x_pix + real_min,
				vpp_imag*y_pix + imag_min,
			)
			t = calc_point(point_z, max_iter)
			f.write(struct.pack("H", t))

	LOG("Done")

	f.close()
	return filename


if len(sys.argv) < 2:
	print "usage: %s port" % (sys.argv[0])
	exit()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind( ("", int(sys.argv[1])) )
s.listen(0)

while 1:
	try:
		conn, addr = s.accept()
		LOG("Got connection from %s:%d" % addr)

		data = conn.recv(1024)
		m = re.match(r'^x=(\d+) y=(\d+) c=([\d\+\-\.ji]+) r=([\d\.]+) iter=(\d+) area=(\d+)[x\*](\d+)\+(\d+)\+(\d+)', data)
		if m:
			resolution = (
				int(m.groups()[0]),
				int(m.groups()[1])
			)
			center = complex(m.groups()[2])
			radius = float(m.groups()[3])
			max_iter = int(m.groups()[4])
			area = [int(i) for i in m.groups()[5:9]]

			tempfile = calc_mandelbrot_area(center, radius, max_iter, resolution, area)
			f = open(tempfile, 'r')
			conn.send(f.readline())

			try:
				i = 0
				while i < 2*area[0]*area[1]:
					data = f.read(8192)
					conn.send(data)
					i += 8192
			except:
				pass



		else:
			conn.send("Query malformed!")



	except KeyboardInterrupt:
		conn.close()
		break



s.close()
