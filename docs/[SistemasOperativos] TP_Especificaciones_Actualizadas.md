**S I S T E M A S O P E R A T I V O S Trabajos Prácticos** 

Especificaciones Actualizadas 

| TP 01  | Hack The Box |
| :---- | :---- |
| **TP 02**  | Sistema HIPS |

2026  
**TP 01 — Hack The Box** 

**1\. Descripción** 

Hack The Box (HTB) es una plataforma de pentesting que permite probar habilidades de prueba de  penetración en entornos controlados y legales. El desafío comienza desde el momento de  registrarse, ya que es necesario hackear el propio código de invitación para acceder a la  plataforma. 

El objetivo es comprometer máquinas virtuales documentando cada paso del proceso, identificando  vulnerabilidades con sus CVEs correspondientes, y obteniendo las flags de cada máquina. 

**2\. Objetivo** 

Cada grupo deberá comprometer un total de tres (3) máquinas de Hack The Box: 

| Máquina  | Dificultad  | Estado requerido  | Puntos objetivo |
| ----- | ----- | ----- | ----- |
| Máquina 1  | Easy (Fácil)  | Retired (Retirada)  | User flag \+ Root flag |
| Máquina 2  | Easy (Fácil)  | Retired (Retirada)  | User flag \+ Root flag |
| Máquina 3  | Medium (Media)  | Retired o Active  | Mínimo User flag |

**3\. Restricciones** 

• Solo se permite el trabajo en las máquinas a través de la VPN oficial de HTB. • Queda prohibido compartir flags entre grupos o copiar walkthroughs sin comprensión del  proceso. 

• Toda captura de pantalla debe mostrar claramente la terminal del alumno con el hostname  y el resultado. 

**4\. Actividades de la Clase de Hoy** 

| OBJETIVOS DE HOY: Al terminar la clase de hoy, el grupo debe tener: (1) cuenta en HTB  activa, (2) VPN conectada, (3) tres máquinas elegidas y justificadas, (4) primer escaneo  Nmap de al menos una máquina. |
| :---- |

**Paso 1 — Registro en HTB**  
Ingresar a hackthebox.com/invite y hackear el código de invitación (puede ser que no se solicite en  este año o haya cambiado el desafio, pero sirve de ejemplo): 

1\. Abrir DevTools del navegador (F12) → Consola 

2\. Ejecutar: makeinvite() 

3\. Decodificar el resultado (Base64 y/o ROT13) 

4\. echo 'CODIGO' | base64 \-d → desde terminal 

5\. Ingresar el código decodificado para registrarse 

**Paso 2 — Conexión VPN** 

1\. Dashboard HTB → Access → VPN → Descargar .ovpn 

2\. sudo openvpn archivo.ovpn 

3\. Verificar: ip addr show tun0 (debe mostrar IP 10.10.x.x) 

**Paso 3 — Elección de máquinas** 

Ir a Labs → Machines → filtrar por Difficulty: Easy y Difficulty: Medium. Elegir las 3 máquinas y  documentar para cada una: 

• Nombre y sistema operativo 

• Justificación de por qué se eligió esa máquina 

• IP de la máquina en HTB 

**Paso 4 — Primer escaneo Nmap** 

Ejecutar sobre al menos una máquina elegida y capturar pantalla del resultado: nmap \-sV \-sC \-oN scan\_inicial.txt \<IP\_de\_la\_maquina\> 

**5\. Proceso Metodológico** 

Para cada una de las tres máquinas deben seguir las siguientes fases, documentando cada una  con capturas de pantalla: 

**Fase 1 — Reconocimiento y Escaneo** 

• Escaneo de puertos con Nmap (versiones, scripts NSE) 

• Identificación de servicios y tecnologías en uso 

• Formulación de hipótesis de vectores de ataque 

**Fase 2 — Enumeración** 

• Enumeración de servicios específicos (HTTP, SMB, FTP, SSH, etc.) 

• Herramientas: Gobuster, Nikto, Dirb, SMBclient, enum4linux, entre otras • Búsqueda de vulnerabilidades asociadas en exploit-db.com, cvedetails.com, searchsploit • Identificación de CVEs correspondientes a los servicios detectados  
**Fase 3 — Explotación** 

• Ejecución del exploit o técnica de acceso basada en la vulnerabilidad identificada • Obtención de la flag de usuario (user.txt) 

• Escalada de privilegios e intento de obtener acceso root/administrador (root.txt) • Documentación de todos los comandos ejecutados con su explicación 

**Fase 4 — Análisis de Seguridad del Servidor** 

• Describir los métodos de detección utilizados durante el proceso 

• Proponer cómo ocultar el servidor y sus servicios para prevenir el ataque • Indicar cómo solucionar cada vulnerabilidad explotada 

**6\. Documentos de Entrega** 

| Entregable  | Contenido  | Observaciones |
| ----- | ----- | ----- |
| Informe Word | Documentación completa de las 3 máquinas:  reconocimiento, enumeración, CVEs,   explotación y capturas de pantalla de los  resultados y acciones tomadas. Introducción  con conceptos de seguridad informática. | Obligatorio — sin él no  se habilitan puntos |
| PowerPoint | Presentación con: conceptos de seguridad,  metodología HTB usada, proceso de cada  máquina, resultados y aprendizajes. | Obligatorio — habilitante |

| NOTA SOBRE CAPTURAS: Cada paso debe estar argumentado con capturas de pantalla  que demuestren que el proceso fue realizado por el grupo. En caso de no conseguir  comprometer una máquina, deben documentar todos los intentos realizados. |
| :---- |

**7\. Estructura del Informe** 

El informe Word debe incluir las siguientes secciones por cada máquina:

| \#  | Sección  | Contenido esperado |
| ----- | ----- | ----- |
| 1  | Introducción  | Nombre del grupo, máquinas elegidas, justificación de la  selección de cada una |
| 2  | Reconocimiento y Escaneo  | Comandos Nmap ejecutados, capturas de pantalla, análisis  de servicios detectados |

| \#  | Sección  | Contenido esperado |
| ----- | ----- | ----- |
| 3  | Enumeración  | Herramientas usadas, directorios y usuarios descubiertos,  hallazgos relevantes |
| 4  | Análisis de Vulnerabilidades  | CVEs identificados, referencias consultadas, descripción de  cada vulnerabilidad |
| 5  | Explotación  | Descripción del exploit, comandos utilizados, evidencia del  shell obtenido |
| 6  | Resultados  | Flags obtenidas (pueden censurarse), nivel de acceso  conseguido |
| 7  | Análisis del Servidor  | Métodos de detección, medidas para ocultar servicios,  correcciones propuestas |
| 8  | Reflexión Final  | Dificultades encontradas, aprendizajes, mejoras para futuros  ejercicios |

**8\. Recursos Recomendados** 

• HackTricks: https://book.hacktricks.xyz 

• GTFOBins: https://gtfobins.github.io 

• Exploit-DB: https://exploit-db.com 

• CVE Details: https://cvedetails.com 

• Nmap Reference: https://nmap.org/book/  
**TP 02 — Sistema HIPS** 

Host-based Intrusion Prevention System 

**1\. Descripción** 

Cada grupo deberá desarrollar un sistema completo de detección y prevención de intrusos (HIPS)  basado en host. El sistema debe ser capaz de identificar comportamientos anómalos o potenciales  intrusiones en el sistema, distinguiendo entre comportamientos normales y sospechosos, y tomar  medidas de prevención cuando corresponda. 

El sistema debe correr bajo Rocky en su última versión estable y dicha maquina debe cumplir al  menos con 10 controles de Hardening bien definidos y justificados. 

**2\. Módulos de Detección** 

El sistema debe cubrir los siguientes aspectos de detección. Para cada uno, se debe implementar  tanto la lógica de detección como la acción de prevención correspondiente: 

**i. Integridad de archivos del sistema** 

• Verificar que los binarios del sistema no hayan sido modificados. 

• Detectar modificaciones en /etc/passwd y /etc/shadow comparando con un baseline  guardado de forma segura. 

**ii. Usuarios conectados** 

• Verificar los usuarios que están conectados al sistema y desde qué origen. • Detectar conexiones desde orígenes inusuales o fuera del horario esperado. 

**iii. Sniffers y modo promiscuo** 

• Detectar si el equipo ha entrado en modo promiscuo (interfaz de red). 

• Controlar que no existan herramientas de captura de paquetes en ejecución: tcpdump,  ethereal, wireshark, entre otras. 

• El módulo de prevención debe bloquear o eliminar estas herramientas del sistema. 

**iv. Análisis de archivos de log** 

Examinar los logs del sistema buscando patrones de acceso indebido. Se deben analizar al menos: ◦ Failed Password y Authentication Failure en /var/log/secure y /var/log/messages.   
◦ Errores de carga de páginas desde un mismo IP (posible scanner):    
/var/log/httpd/access.log  
◦ Envío de mails masivos desde una misma cuenta: /var/log/maillog y cola de correo A partir de lo detectado, el módulo de prevención debe poder: bloquear IPs, cambiar contraseña  del usuario, bloquear un usuario, o bajar temporalmente el servicio de correo. 

**v. Cola de correo** 

• Verificar el tamaño de la cola de mails del equipo. 

• Prevención: bloquear IPs o usuarios generadores de correo masivo. 

**vi. Procesos con alto consumo de recursos** 

• Monitorear los procesos que consumen un porcentaje elevado de memoria. • Considerar el tiempo de consumo excesivo como criterio para la acción. • Prevención: terminar el proceso bajo criterio configurable. 

**vii. Directorio /tmp** 

• Verificar que no haya procesos con nombres extraños o scripts ejecutables ubicados en  /tmp. 

• Prevención: eliminar el archivo o moverlo a una carpeta de cuarentena. 

**viii. Ataques DDoS** 

• Detectar ataques de tipo DDoS. El profesor proveerá una muestra de log con ataques de  DDoS a un servicio DNS para calibrar la detección. 

• Prevención: bloquear la IP atacante o bajar el servicio afectado. 

**ix. Archivos cron** 

• Examinar los archivos que se están ejecutando como cron. 

• Identificar tareas programadas con rutas o nombres sospechosos. 

**x. Intentos de acceso no válidos** 

• Detectar intentos repetitivos desde un mismo usuario. 

• Detectar intentos de acceso con múltiples usuarios desde un mismo IP (credential stuffing).

| CRITERIO DE DISTINCIÓN: Se deben realizar análisis que permitan distinguir cuándo algo  es una intrusión real y cuándo puede ser un comportamiento normal del sistema. Por  ejemplo: un proceso web que consume 75% de RAM puede ser completamente normal en  un servidor bajo carga. |
| :---- |

**3\. Módulo de Prevención** 

Las acciones de prevención representan el 30% de la calificación total del TP. El sistema debe  tomar decisiones automatizadas y acompañar cada acción con una notificación por email al  administrador. Ejemplos de acciones: 

| Amenaza detectada  | Acción de prevención  | Notificación |
| ----- | ----- | ----- |
| IP sospechosa de intrusión  | Filtrar con regla de firewall (iptables)  | Email al admin |
| Usuario con múltiples accesos o  envío masivo de mails | Cambiar contraseña generada   aleatoriamente  | Email al admin |
| Aplicación sospechosa   detectada  | Eliminación temporal (kill)  | Email al admin |
| Sniffer activo  | Bloquear o eliminar la herramienta  | Email al admin |
| Archivo sospechoso en /tmp  | Mover a carpeta de cuarentena  | Email al admin |
| Ataque DDoS  | Bloquear IP o bajar servicio  | Email al admin |

**4\. Requisitos Técnicos** 

**4.1 Interfaz Web** 

• El sistema debe contar con una interfaz web básica accedida mediante usuario y  contraseña. 

• La interfaz debe permitir la configuración de los módulos y la revisión de alertas. 

**4.2 Base de datos** 

• Utilizar PostgreSQL (obligatorio). 

• Cuidar los permisos asignados de acceso a la base de datos. 

• Ninguna contraseña puede estar expuesta en los códigos fuente. 

• La Base de Datos debe contar al menos con 7 buenas practicas de Hardening basado en el  CIS Control 

**4.3 Almacenamiento seguro de configuración** 

• Los archivos de comparación o configuración (firmas, perfiles de usuario, contraseñas)  deben estar en una partición o carpeta encriptada, o ser almacenados en la base de datos.  
**4.4 Bitácoras del sistema** 

Los archivos de log del HIPS deben registrarse en el directorio /var/log/hips/. Formato obligatorio: 

| Archivo  | Propósito |
| ----- | ----- |
| alarmas.log  | Todas las alarmas detectadas por los módulos de detección |
| prevención.log  | Todas las acciones tomadas por el módulo de prevención |

Formato de registro de alarmas (obligatorio y en este orden): 

timestamp (dd/mes/yyyy) :: Tipo de Alarma :: IP origen (si disponible) 

Ejemplo: 

29/05/2026 :: FAILED\_LOGIN\_MULTIPLE :: 10.0.0.25 

29/05/2026 :: SNIFFER\_DETECTADO :: N/A 

29/05/2026 :: MODIFICACION\_PASSWD :: N/A 

**4.5 Lenguaje de programación** 

• Libre elección. Debe justificarse en la documentación. 

• Se pueden combinar lenguajes y realizar cuantas llamadas al sistema sean necesarias. 

**5\. Documentación** 

• Manual impreso y digital de uso e instalación: obligatorio y habilitante de la entrega. • El código debe estar adecuadamente comentado y documentado. 

**6\. Sistema de Alertas** 

• Una vez detectada una alarma, el sistema debe registrarla en el log correspondiente. • Toda alarma debe generar un aviso por correo electrónico al administrador y debe ser  visible desde un dashboard en el sistema. 

• Toda decisión del módulo de prevención debe ir acompañada de un mail al administrador. 

**7\. Pruebas** 

• Se deben realizar pruebas para demostrar que el software funciona correctamente. Las  pruebas deben ser lo más automatizadas posibles 

• El grupo debe tener preparado todo el escenario de pruebas para el día de la entrega.  
**9\. Fecha de Entrega**

| FECHA: Una semana antes de cada oportunidad de evaluación (Hasta 2da Oportunidad por  Reglamento del DEI). El grupo deberá tener preparado el escenario de pruebas completo  para el día de la entrega. |
| :---- |

