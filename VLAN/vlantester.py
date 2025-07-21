import os
import sys
from scapy.all import ARP, Ether, srp
import socket

def is_root():
    return os.geteuid() == 0

def resolve_hostname(ip):
    try:
        return socket.gethostbyaddr(ip)[0]
    except:
        return "unknown"

def scan_lan(network="192.168.1.0/24"):
    print(f"Сканирование сети {network}...")

    try:
        arp = ARP(pdst=network)
        ether = Ether(dst="ff:ff:ff:ff:ff:ff")
        packet = ether / arp

        result = srp(packet, timeout=2, verbose=0)[0]

        devices = []
        for sent, received in result:
            devices.append({
                'ip': received.psrc,
                'mac': received.hwsrc,
                'hostname': resolve_hostname(received.psrc)
            })

        return devices
    except PermissionError:
        print("❌ Недостаточно прав для отправки пакетов. Запусти скрипт с sudo.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Ошибка при сканировании: {e}")
        sys.exit(1)

def print_devices(devices):
    print("\nОбнаруженные устройства:\n")
    print("{:<16} {:<20} {:<40}".format("IP", "MAC", "Имя"))

    for d in devices:
        print("{:<16} {:<20} {:<40}".format(
            d['ip'],
            d['mac'],
            d['hostname']
        ))

# --- MAIN ---
if not is_root():
    print("❌ Этот скрипт требует запуска с правами root (sudo).")
    sys.exit(1)

devices = scan_lan()
print_devices(devices)
