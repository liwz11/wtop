# /usr/bin/env python2.7
# Author: liwz11


import os, time, json, re, threading, subprocess
import urllib, socket, fcntl, struct

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from argparse import ArgumentParser


class MyHTTPHandler(BaseHTTPRequestHandler):
	def setup(self):
		self.timeout = 2 # avoid request timeout. it works! short timeout as there is only 1 thread
		BaseHTTPRequestHandler.setup(self)
	
	def do_GET(self):
		root_dir = './html/'
		temp = self.path.split('?')
		path = temp[0]
		pram = ''
		if len(temp) > 1:
			pram = urllib.unquote(temp[1])

		if path == '/':
			path = '/index.html'

		try:
			content_type = 'text/html'
			if path.endswith('.js'):
				content_type = 'application/javascript'
			elif path.endswith('.css'):
				content_type = 'text/css'

			if '..' in path:
				self.send_error(400, 'Bad Request')

			elif path == '/get_data':
				self.send_response(200)
				self.send_header('Content-Type', content_type)
				self.end_headers()

				max_num = 3000
				if pram.endswith('t=0'):
					max_num = 10000
				
				t = time.strftime("%Y-%m-%d", time.localtime(time.time())) + ' 00:00:00'
				temp = pram.split('t=')
				if len(temp) > 1 and len(temp[1]) == len(t):
					t = temp[1]
				date = t.split(' ')[0].replace('-', '')

				res_list = []
				
				with open('./logs/%s.log' % date, 'r') as f:
					for line in f:
						performance = json.loads(line.strip())
						if len(res_list) >= max_num:
							break
						if performance['t'] <= t:
							continue
						res_list.append(performance)

				self.wfile.write(json.dumps(res_list))

			elif path == '/mychart.js':
				f = open(root_dir + path)
				self.send_response(200)
				self.send_header('Content-Type', content_type)
				self.end_headers()

				global http_conf

				js_text = f.read()
				js_text = js_text.replace('[DOMAIN]', http_conf['domain'])
				js_text = js_text.replace('[PORT]', str(http_conf['port']))
				js_text = js_text.replace('[INTERVAL]', str(http_conf['interval']))
				js_text = js_text.replace('[TIMEOUT]', str(http_conf['timeout']))
				self.wfile.write(js_text)
				f.close()

			else:
				f = open(root_dir + path)
				self.send_response(200)
				self.send_header('Content-Type', content_type)
				self.end_headers()
				self.wfile.write(f.read())
				f.close()

		except Exception as e:
			if 'Broken pipe' not in str(e):
				self.send_error(404, 'File Not Found: %s' % path)
			else:
				print('Error: Connection reset by client peer.')

def popen_command(command):
    try:
        #print('command: %s' % command)
        p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = p.communicate()
        #print('output: ++%s++' % output.strip())
        return output.strip()
    except Exception as e:
        print('%s\nError on popen: %s' % (str(e), command))
        return None


def monitor(iface, addr):
	print('[+] monitor the system\'s performance.\n')

	byte_cmd = "ifconfig %s" % iface
	conn_cmd   = "netstat -n | awk '/%s:/ {++S[$NF]} END {for(a in S) print a, S[a]}' | grep 'ESTABLISHED' | cut -d ' ' -f2" % addr

	while True:
		t1 = time.time()
		bytes1 = popen_command(byte_cmd)
		time.sleep(1)
		t2 = time.time()
		bytes2 = popen_command(byte_cmd)
		conn = popen_command(conn_cmd)

		if bytes1 == None or bytes2 == None or conn == None:
			continue

		'+++++++++++++++++++++++++++++++++++++++++++++++++++++++++'

		find_bytes = re.findall('bytes[: \t]([0-9]*)', bytes1)
		ibytes1 = int(find_bytes[0])
		obytes1 = int(find_bytes[1])

		find_bytes = re.findall('bytes[: \t]([0-9]*)', bytes2)
		ibytes2 = int(find_bytes[0])
		obytes2 = int(find_bytes[1])

		ibw = round((ibytes2 - ibytes1) * 8 / (t2 - t1) / 1000000, 6) # Mbps
		obw = round((obytes2 - obytes1) * 8 / (t2 - t1) / 1000000, 6) # Mbps

		if conn == '':
			conn = 0
		else:
			conn = int(conn)

		t = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t2))
		performance = { 'ibw':ibw, 'obw':obw, 'conn':conn, 't': t }
		
		if not os.path.exists('./logs'):
			os.mkdir('./logs')

		date = t.split(' ')[0].replace('-', '')
		with open('./logs/%s.log' % date, 'a') as f:
			f.write(json.dumps(performance))
			f.write('\n')


def get_ip_addr(ifname):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    addr = fcntl.ioctl(sock.fileno(), 0x8915, struct.pack('256s', ifname[:15]))[20:24]
    return socket.inet_ntoa(addr)


if __name__ == '__main__':
	parser = ArgumentParser(description='monitor system\'s performance and display it with html, just like \'top\'.')
	parser.add_argument('--iface', default='eth0', help='specify an interface and monitor it, default \'eth0\'')
	parser.add_argument('--domain', default='', help='the http server domain, default addr')
	parser.add_argument('--addr', default='127.0.0.1', help='the http server addr, default \'127.0.0.1\'')
	parser.add_argument('--port', default=8642, type=int, help='the tmap server port, default 8642')
	parser.add_argument('--interval', default=5, type=int, help='the interval to get data in mychart.js, default 5s')
	parser.add_argument('--timeout', default=5, type=int, help='the timeout to get data in mychart.js, default 5s')
	args = parser.parse_args()

	iface = args.iface
	addr = get_ip_addr(iface)

	http_conf = {}
	http_conf['domain']   = args.domain
	http_conf['addr']     = args.addr
	http_conf['port']     = args.port
	http_conf['interval'] = args.interval
	http_conf['timeout']  = args.timeout

	if http_conf['domain'] == '':
		http_conf['domain'] = http_conf['addr']

	print('')
	
	monitor_thread = threading.Thread(target=monitor, args=(iface, addr, ))
	monitor_thread.setDaemon(True)
	monitor_thread.start()

	try:
		server = HTTPServer((http_conf['addr'], http_conf['port']), MyHTTPHandler)
		print('[+] start an HTTP server on %s:%d\n' % (http_conf['addr'], http_conf['port']))
		server.serve_forever()
	except Exception as e:
		server.socket.close()

