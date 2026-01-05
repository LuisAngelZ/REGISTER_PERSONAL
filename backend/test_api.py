"""
Script para probar los endpoints de la API
"""
import requests
import json

API_URL = "http://localhost:8000"

print("=" * 60)
print("PRUEBA DE ENDPOINTS - Sistema ZKTeco")
print("=" * 60)

# Test 1: Health Check
print("\n1. Verificar estado de la API...")
try:
    response = requests.get(f"{API_URL}/health")
    print(f"✅ Estado: {response.json()}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 2: Endpoint raíz
print("\n2. Obtener información de la API...")
try:
    response = requests.get(f"{API_URL}/")
    print(f"✅ Respuesta: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 3: Test de conexión ZKTeco
print("\n3. Probar conexión con ZKTeco...")
try:
    response = requests.get(f"{API_URL}/api/zkteco/test-conexion")
    print(f"✅ Respuesta: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 4: Obtener usuarios
print("\n4. Obtener usuarios del dispositivo...")
try:
    response = requests.get(f"{API_URL}/api/zkteco/usuarios")
    print(f"✅ Respuesta: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 5: Obtener registros de asistencia
print("\n5. Obtener registros de asistencia...")
try:
    response = requests.get(f"{API_URL}/api/zkteco/registros-asistencia")
    print(f"✅ Respuesta: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 60)
print("Documentación disponible en:")
print("  - Swagger UI: http://localhost:8000/docs")
print("  - ReDoc: http://localhost:8000/redoc")
print("=" * 60)
