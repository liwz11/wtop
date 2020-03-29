# /usr/bin/env python2.7
# Author: liwz11


import os, time, json, threading, subprocess
import socket, fcntl, struct

from argparse import ArgumentParser

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
	print('[+] monitor the system\'s CPU and memory, the specified interface\'s bandwidth and connections.')

	ibytes_cmd = "ifconfig %s | grep 'bytes' | cut -d ':' -f2 | cut -d ' ' -f1" % iface
	obytes_cmd = "ifconfig %s | grep 'bytes' | cut -d ':' -f3 | cut -d ' ' -f1" % iface
	conn_cmd   = "netstat -n | awk '/%s:/ {++S[$NF]} END {for(a in S) print a, S[a]}' | grep 'ESTABLISHED' | cut -d ' ' -f2" % addr

	while True:
		t1 = time.time()
		ibytes1 = int(popen_command(ibytes_cmd))
		obytes1 = int(popen_command(obytes_cmd))

		time.sleep(1)

		t2 = time.time()
		ibytes2 = int(popen_command(ibytes_cmd))
		obytes2 = int(popen_command(obytes_cmd))

		conn = popen_command(conn_cmd)

		if ibytes1 == None or obytes1 == None or ibytes2 == None or obytes2 == None or conn == None:
			continue

		'+++++++++++++++++++++++++++++++++++++++++++++++++++++++++'

		ibw = int(round((ibytes2 - ibytes1) * 8 / (t2 - t1))) # bps
		obw = int(round((obytes2 - obytes1) * 8 / (t2 - t1))) # bps

		if conn == '':
			conn = 0
		else:
			conn = int(conn)

		t = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t2))
		performance = { 'ibw':ibw, 'obw':obw, 'conn':conn, 't': t }
		print(performance)


def get_ip_addr(ifname):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    addr = fcntl.ioctl(sock.fileno(), 0x8915, struct.pack('256s', ifname[:15]))[20:24]
    return socket.inet_ntoa(addr)


if __name__ == '__main__':
	parser = ArgumentParser(description='Capture linux\'s CPU, memory, bandwidth and connections and show in html page, just like the top tool.')
	parser.add_argument('--iface', default='eth0', help='specify an interface and monitor it, default \'eth0\'')
	args = parser.parse_args()

	iface = args.iface
	addr = get_ip_addr(iface)

	
	monitor_thread = threading.Thread(target=monitor, args=(iface, addr, ))
	monitor_thread.setDaemon(True)
	monitor_thread.start()
	
	time.sleep(100)

	