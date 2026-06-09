import socket
import struct
import re


class WOLSender:
    @staticmethod
    def validate_mac(mac_address):
        pattern = r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$'
        return re.match(pattern, mac_address) is not None

    @staticmethod
    def format_mac(mac_address):
        return mac_address.replace(':', '').replace('-', '')

    @staticmethod
    def send_magic_packet(mac_address, broadcast_ip='255.255.255.255', port=9):
        if not WOLSender.validate_mac(mac_address):
            raise ValueError(f"Invalid MAC address: {mac_address}")

        mac_hex = WOLSender.format_mac(mac_address)
        mac_bytes = bytes.fromhex(mac_hex)
        magic_packet = b'\xff' * 6 + mac_bytes * 16

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        try:
            sock.sendto(magic_packet, (broadcast_ip, port))
            return True
        except Exception as e:
            print(f"Error sending WOL packet: {e}")
            return False
        finally:
            sock.close()

    @staticmethod
    def send_magic_packets(mac_addresses, broadcast_ip='255.255.255.255', port=9):
        results = {}
        for mac in mac_addresses:
            results[mac] = WOLSender.send_magic_packet(mac, broadcast_ip, port)
        return results
