# ATAQUE CDP DoS
## 1 | Objetivo del Laboratorio
El objetivo de este laboratorio es evaluar la resiliencia y el comportamiento de un conmutador (**Switch**) de red frente a un ataque de Denegación de Servicio (**DoS**) por inundación de tablas mediante el protocolo **CDP** (*Cisco Discovery Protocol*). Este escenario permite analizar cómo el desbordamiento de memoria puede degradar significativamente el rendimiento del dispositivo de red o, en casos críticos, provocar su colapso total.

## 2 | Topología de la red
La topología representa una red de laboratorio estructurada bajo una arquitectura jerárquica simple, donde todos los dispositivos internos coexisten en la VLAN 89. La red cuenta con servicios automáticos de asignación de direccionamiento IP (DHCP) administrados por un enrutador dedicado, y salida a redes externas (Internet) a través de un enrutador de borde con traducción de direcciones.
![image_alt](https://github.com/labcruzmesson-cyber/Attack-01---CDP-DoS/blob/ba8ca3d9d065fc90f76bdcf317c5a8342a4e5253/Topologia.png)
### A. Hardware y Dispositivos
La infraestructura física y los nodos que componen la topología se distribuyen según sus roles funcionales en la red:
* **Dispositivos de Enrutamiento (Capa 3):**
  * `R-Edge`: Enrutador de borde perimetral encargado de la salida a redes externas.
  * `R-DHCP`: Enrutador dedicado exclusivamente a la administración y distribución de direccionamiento IP dinámico en la red local.
* **Dispositivos de Conmutación (Capa 2):**
  * `SW-CORE`: Switch central (Núcleo) que interconecta los enrutadores y distribuye el tráfico hacia los switches de acceso.
  * `SW-1` y `SW-2`: Switches de acceso encargados de proveer conectividad directa a los nodos finales.
* **Dispositivos Finales (Hosts):**
  * `Kali`: Estación de trabajo orientada del atacante.
  * `VPC-1` y `VPC-2`: Computadoras virtuales de escritorio (Virtual PCs) que actúan como usuarios finales de la red.
  * `Net`: Nube que simula el entorno de red externa o Internet.
### B. Componentes de Software
Entorno lógico y sistemas operativos que corren sobre la infraestructura:
* **Sistemas Operativos de Red:** Software basado en emulación de Cisco (IOS) para la gestión y ejecución de protocolos de red (CDP, DHCP, NAT, Routing) en los routers y switches.
* **Sistemas Operativos de Hosts:**
  * `Kali Linux` instalado en la estación atacante.
  * OS ligero (`VPCS`) en las terminales de usuario para pruebas de conectividad básica (Ping, Traceroute).
### C. Segmentación y Parámetros de Red
Definición del direccionamiento lógico, segmentación LAN y salida a Internet:
* **Segmento de Red Interno:** `192.168.89.0/24` (Máscara de subred `255.255.255.0`).
* **VLAN Configurada:** VLAN 89, segmento único donde coexisten de forma nativa todos los dispositivos internos, switches (vía SVI) y routers.
* **Puerta de Enlace (Default Gateway):** `192.168.89.254` (Configurada en la interfaz `Gi0/1` de `R-Edge`). Es el nodo encargado de recibir todo el tráfico interno con destino externo y realizar NAT/PAT para darle salida hacia Internet.
### D. Interfaces Utilizadas
| Dispositivo Origen | Interfaz Local | Dispositivo Destino | Interfaz Remota |
| :--- | :--- | :--- | :--- |
| **R-Edge** | Gi0/0<br>Gi0/1 | Net (Nube)<br>SW-CORE | —<br>Gi0/0 |
| **R-DHCP** | Gi0/0 | SW-CORE | Gi0/3 |
| **SW-CORE** | Gi0/0<br>Gi0/3<br>Gi0/1<br>Gi0/2 | R-Edge<br>R-DHCP<br>SW1<br>SW2 | Gi0/1<br>Gi0/0<br>Gi0/0<br>Gi0/0 |
| **SW-1** | Gi0/0<br>Gi0/1<br>Gi0/2 | SW-CORE<br>Kali<br>VPC-1 | Gi0/1<br>e0<br>eth0 |
| **SW-2** | Gi0/0<br>Gi0/1 | SW-CORE<br>VPC-2 | Gi0/2<br>eth0 |
| **Kali** | e0 | SW1 | Gi0/1 |
| **VPC-1** | eth0 | SW1 | Gi0/2 |
| **VPC-2** | eth0 | SW2 | Gi0/1 |

## 3 | Objetivo del script
El script tiene como finalidad automatizar la generación masiva y el envío continuo de tramas **CDP** modificadas con datos aleatorios (direcciones MAC, direcciones IP, nombres de dispositivo, plataformas y puertos de origen). Al enviar estas tramas falsas a alta velocidad, se busca llenar la tabla de vecinos CDP del switch objetivo, simulando un ataque de **CDP Flooding**.

## 4 | Parámetros usados
El script define y utiliza los siguientes parámetros para controlar el ataque:
* **INTERFACE (Obligatorio, vía `-i` o `--interface`):** Especifica la interfaz de red local del host Linux desde la cual se inyectarán las tramas hacia el switch.
* **INTERVAL (Opcional, vía `--interval`, por defecto `0.01`):** Determina el tiempo de espera en segundos entre el envío de cada paquete. Un valor de 0.01 equivale a una tasa aproximada de 100 paquetes por segundo (pkt/s). Puede modificarse al ejecutar el script para aumentar o disminuir la velocidad del ataque.
* **PACKET_COUNT (Opcional, vía `-c` o `--count`, por defecto `0`):** Define la cantidad total de paquetes a enviar. El valor 0 está configurado para un bucle infinito (el ataque no se detiene hasta que el usuario lo interrumpa manualmente).
* **Campos CDP Dinámicos:** Dentro de la función `build_cdp_packet()`, se generan valores aleatorios para simular dispositivos reales en cada ciclo:
  * `src_mac`: Dirección MAC origen aleatoria para saturar la tabla de direcciones del switch.
  * `device_id`: Nombre aleatorio del dispositivo de 12 caracteres.
  * `platform`: Modelo o plataforma de hardware aleatoria de 8 caracteres.
  * `software_ver`: Versión de software ficticia basada en una cadena alfanumérica aleatoria.
  * `ip_addr`: Dirección IPv4 aleatoria.
  * `iface`: Identificador de puerto de origen aleatorio para simular que los paquetes provienen de diferentes interfaces físicas del supuesto vecino.

 ## 5 | Requisitos para utilizar la herramienta
Para que el script se ejecute correctamente se deben cumplir las siguientes condiciones:
* **Privilegios de Administrador:** El script debe ser ejecutado obligatoriamente como root (`sudo`), ya que requiere acceso directo a la interfaz de red para la inyección de tramas en la capa de enlace (Raw Sockets). El código verifica esto al validar que el UID del usuario sea igual a 0.
* **Intérprete Python:** Contar con Python 3 instalado en el sistema.
* **Librería Scapy:** Tener instalada la biblioteca de manipulación de paquetes `scapy` (específicamente la versión 2.5.0 o compatible).
* **Módulo Contrib de CDP:** El script requiere la carga explícita del componente de extensión para CDP mediante `load_contrib("cdp")`.
* **Módulo Argparse:** Contar con la librería estándar `argparse` incorporada en Python para poder gestionar y capturar correctamente los argumentos introducidos por el usuario desde la terminal (`-i`, `--interval`, `-c`).
* **Conexión Física/Lógica:** El host debe estar conectado directamente a un puerto del switch (ej. `Gi0/1`) donde el protocolo CDP se encuentre activo.

## 6 | Documentación del funcionamiento del script
El script es una herramienta de automatización de pruebas de penetración desarrollada en Python 3 utilizando la librería Scapy. Su funcionamiento se divide en cuatro fases principales distribuidas de forma cíclica:

### 1. Fase de Inicialización y Validación
* **Validación de Privilegios:** Al ejecutarse, el script verifica mediante el sistema operativo que el usuario cuente con permisos de superusuario (`root`). Si el UID no es 0, el programa detiene su ejecución inmediatamente para evitar fallos en la inyección de paquetes.
* **Procesamiento de Argumentos:** A través del módulo `argparse`, el script captura los parámetros dinámicos introducidos por el usuario en la terminal (Interfaz, Intervalo y Contador de paquetes).
* **Carga de Extensiones:** Se importa dinámicamente el módulo nativo de Scapy para soporte del protocolo CDP (`load_contrib("cdp")`), permitiendo al script interpretar y construir las cabeceras específicas de Cisco.

### 2. Fase de Construcción Dinámica del Paquete (Función `build_cdp_packet`)
Por cada ciclo de ejecución, el script ensambla un paquete desde cero apilando las capas de la siguiente manera:
* **Capa de Enlace:** Se genera una dirección MAC de origen aleatoria y se establece la MAC de destino en `01:00:0c:cc:cc:cc` (dirección multicast oficial utilizada por Cisco para anuncios CDP).
* **Encapsulación LLC/SNAP:** Se añaden las cabeceras de control de enlace lógico (LLC) y el protocolo de acceso a subred (SNAP) con el OUI de Cisco (`00000c`) y el PID de CDP (`2000`), requerimiento indispensable para que un switch real acepte la trama.
* **Payload CDPv2:** Se genera un mensaje CDP versión 2 con un tiempo de vida (TTL) de 180 segundos. Dentro de este payload, se inyectan campos (TLVs) completamente aleatorios en cada iteración: nombre de dispositivo, plataforma, versión de software, una dirección IP falsa y un puerto de origen aleatorio (simulando interfaces del rango GigabitEthernet0/0 al 0/9).

### 3. Fase de Inyección e Inundación (Función `cdp_flood`)
* **Bucle de Envío:** El script entra en un bucle (`while True`) donde utiliza la función `sendp()` de Scapy para enviar la trama armada directamente a la capa 2 a través de la interfaz de red especificada (ej. `eth0`).
* **Control de Tasa:** Tras enviar cada paquete, el script duerme durante el tiempo definido en el parámetro `INTERVAL` (por defecto 0.01 segundos) para regular la velocidad del ataque.
* **Monitoreo:** Cada vez que el contador interno acumula 500 paquetes, el script calcula el tiempo transcurrido y despliega en la consola una métrica de rendimiento mostrando la cantidad de paquetes enviados y la tasa promedio de paquetes por segundo (pkt/s).

### 4. Fase de Finalización Controlada
El flujo del script termina bajo dos condiciones:
* **Límite Alcanzado:** Si el usuario configuró un número específico de paquetes (`--count`), el bucle se rompe automáticamente al alcanzar dicha cifra.
* **Interrupción Manual:** Si el ataque está en modo infinito, el script captura la señal de teclado `Ctrl+C` (`KeyboardInterrupt`). En ambos casos, el programa realiza un cierre limpio mostrando en pantalla el resumen estadístico total del ataque (paquetes totales, tiempo transcurrido y tasa promedio).

## 7 | Contra-medidas
Para mitigar la efectividad de un ataque de inundación CDP (CDP Flooding) y proteger los recursos de memoria y procesamiento de los dispositivos de conmutación, se documentan las siguientes tres estrategias de defensa implementadas directamente desde la interfaz de línea de comandos de los switches.
### 1. Deshabilitar el Protocolo a Nivel Global
Esta medida anula por completo el procesamiento de tramas CDP en todo el dispositivo. Es la opción recomendada cuando la topología de red está consolidada y no requiere del descubrimiento dinámico de vecinos ni de la automatización de parámetros de energía (Power over Ethernet) para teléfonos IP.
```plaintext
no cdp run
```

### 2. Deshabilitar CDP por Interfaz
En caso de que se necesite CDP para la comunicación entre switches o teléfonos IP, se debe deshabilitar específicamente en los puertos de acceso (donde se conectan los usuarios finales o potenciales atacantes):
```plaintext
interface gigabitethernet 0/1
 no cdp enable
```
### 3. Implementar Port Security
Para limitar el impacto del script (el cual cambia constantemente la dirección MAC de origen), se puede activar la seguridad de puerto para restringir el número de direcciones MAC permitidas en esa interfaz:
```plaintext
switchport port-security
switchport port-security maximum 3
switchport port-security violation shutdown
```
Esto provocará que el puerto se deshabilite automáticamente (err-disable) en cuanto el script comience a enviar tramas con MACs aleatorias.
