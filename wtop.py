# /usr/bin/env python2.7
# Author: liwz11


import os, time, json, re, threading, subprocess
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

