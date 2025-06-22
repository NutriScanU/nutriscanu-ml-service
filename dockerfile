# Imagen base ligera con Python 3.10
FROM python:3.10-slim

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia solo el archivo de dependencias primero
COPY requirements.txt .

# Instala las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del código fuente al contenedor
COPY . .

# Expone el puerto que usará la aplicación (ajustable)
EXPOSE 8000

# Comando para iniciar la app (ajustar si usas Flask en vez de FastAPI)
CMD ["python", "main.py"]

