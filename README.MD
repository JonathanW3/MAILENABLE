### 🚀 Comandos para correr el programa

1. **Clonar o preparar el proyecto en tu máquina:**

```bash
mkdir email_xml_service && cd email_xml_service
```

2. **Crear el entorno virtual (opcional pero recomendado):**

```bash
python3 -m venv venv
source venv/bin/activate   # En Linux / Mac
venv\Scripts\activate      # En Windows
```

3. **Instalar dependencias necesarias:**
   Crea un archivo `requirements.txt` con:

```txt
python-dotenv
jinja2
```

E instala:

```bash
pip install -r requirements.txt
```

4. **Configurar las variables de entorno:**
   Copia el archivo `.env` proporcionado a la raíz del proyecto y ajusta los valores de correo, usuario y contraseña según tu entorno.

5. **Ejecutar una sola vez el servicio (sin intervalo):**
   Este comando leerá el buzón y procesará los correos una sola vez y luego terminará:

```bash
python main.py --mode service --interval 0
```

6. **Ejecutar en modo servicio continuo (con intervalo de verificación):**

```bash
python main.py --mode service --interval 30
```

7. **Ejecutar pruebas de envío de correos:**

* Probar el template de procesamiento:

```bash
python main.py --mode test --test-type processing
```

* Probar el template de cliente:

```bash
python main.py --mode test --test-type client
```

* Probar ambos:

```bash
python main.py --mode test --test-type both
```

* Probar Modo Monitor:

# Buscar por remitente específico
python main.py --mode monitor --email-sender "remitente@ejemplo.com"

# Buscar por asunto específico  
python main.py --mode monitor --email-subject "Factura electrónica"

# Buscar por ambos criterios (más específico)
python main.py --mode monitor --email-sender "sri@sri.gob.ec" --email-subject "AUTORIZADO"


✅ Con `--interval 0` el programa procesa solo una vez y termina (ideal para pruebas rápidas). Con intervalos mayores a 0 se queda en modo monitoreo.
