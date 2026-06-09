import socket
import subprocess
import re
import platform
import ipaddress
from PyQt5.QtCore import QThread, pyqtSignal


class ARPScanner(QThread):
    scan_finished = pyqtSignal(list)
    scan_progress = pyqtSignal(int, int)

    def __init__(self, network=None):
        super().__init__()
        self.network = network
        self._stop_flag = False

    def stop(self):
        self._stop_flag = True

    def get_local_network(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            ip_parts = local_ip.split('.')
            return f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.0/24"
        except Exception as e:
            print(f"Error getting local network: {e}")
            return "192.168.1.0/24"

    @staticmethod
    def ping_host(ip, timeout=1):
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        wait_param = '-w' if platform.system().lower() == 'windows' else '-W'
        timeout_ms = str(timeout * 1000 if platform.system().lower() == 'windows' else timeout)
        command = ['ping', param, '1', wait_param, timeout_ms, ip]
        try:
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout + 1)
            return result.returncode == 0
        except Exception:
            return False

    @staticmethod
    def get_arp_table():
        devices = {}
        try:
            if platform.system().lower() == 'windows':
                result = subprocess.run(['arp', '-a'], capture_output=True, text=True)
                lines = result.stdout
            else:
                result = subprocess.run(['arp', '-n'], capture_output=True, text=True)
                lines = result.stdout

            mac_pattern = r'([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})'
            ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'

            for line in lines.split('\n'):
                ip_matches = re.findall(ip_pattern, line)
                mac_matches = re.findall(mac_pattern, line)
                if ip_matches and mac_matches:
                    ip = ip_matches[0]
                    mac_match = mac_matches[0]
                    mac = ''.join(mac_match) if isinstance(mac_match, tuple) else mac_match
                    if mac.lower() not in ('ff-ff-ff-ff-ff-ff', 'ff:ff:ff:ff:ff:ff', '00-00-00-00-00-00', '00:00:00:00:00:00'):
                        devices[ip] = mac
        except Exception as e:
            print(f"Error getting ARP table: {e}")
        return devices

    def scan_with_scapy(self, network):
        devices = []
        try:
            from scapy.all import ARP, Ether, srp

            arp = ARP(pdst=network)
            ether = Ether(dst="ff:ff:ff:ff:ff:ff")
            packet = ether / arp

            result, _ = srp(packet, timeout=2, verbose=0)

            for sent, received in result:
                if self._stop_flag:
                    break
                devices.append({
                    'ip': received.psrc,
                    'mac': received.hwsrc,
                    'name': received.psrc
                })
        except ImportError:
            return None
        except Exception as e:
            print(f"Scapy scan error: {e}")
            return None
        return devices

    def scan_with_ping_arp(self, network):
        devices = []
        try:
            net = ipaddress.ip_network(network, strict=False)
            hosts = list(net.hosts())
            total = len(hosts)

            for i, host in enumerate(hosts, 1):
                if self._stop_flag:
                    break
                ip_str = str(host)
                self.scan_progress.emit(i, total)
                if self.ping_host(ip_str, timeout=0.5):
                    pass

            arp_table = self.get_arp_table()

            for ip, mac in arp_table.items():
                if str(ipaddress.ip_address(ip)) in [str(h) for h in hosts]:
                    devices.append({
                        'ip': ip,
                        'mac': mac,
                        'name': ip
                    })
        except Exception as e:
            print(f"Ping/ARP scan error: {e}")
        return devices

    def run(self):
        if self.network is None:
            self.network = self.get_local_network()

        devices = self.scan_with_scapy(self.network)

        if devices is None:
            devices = self.scan_with_ping_arp(self.network)

        self.scan_finished.emit(devices)
