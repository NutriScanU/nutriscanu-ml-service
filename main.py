
from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib

import pandas as pd
from collections import Counter  # 💥 IMPORTANTE para /recommend

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": [
    "https://nutriscanu-frontend-v2-f6cghrgghtfgdqah.brazilsouth-01.azurewebsites.net"
]}}, supports_credentials=True)


# Cargar el modelo ML con pipeline incluido
modelo_ml = joblib.load('pipeline_modelo_xgboost_balanceado.pkl')

# Cargar sistema de recomendación
sistema_recomendacion = joblib.load('sistema_recomendacion_grafo.pkl')
G = sistema_recomendacion['grafo']
df_dataset = sistema_recomendacion['dataset']

# Etiquetas del modelo
CLASES = ['Healthy', 'Diabetes', 'Anemia', 'Ambos']

# Columnas esperadas
COLUMNAS_MODELO = [
    'age', 'gender', 'bmi', 'hbA1c', 'blood_glucose_level',
    'hemoglobin', 'insulin', 'triglycerides',
    'hematocrit', 'red_blood_cells', 'smoking_history'
]

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()
        print("📥 Datos recibidos en Flask /predict:", data)

        # Verifica que estén todas las columnas esperadas
        for col in COLUMNAS_MODELO:
            if col not in data:
                return jsonify({"error": f"Falta el campo: {col}"}), 400

        # Crear DataFrame para el modelo
        row = {
            'age': float(data['age']),
            'gender': data['gender'],
            'bmi': float(data['bmi']),
            'hbA1c': float(data['hbA1c']),
            'blood_glucose_level': float(data['blood_glucose_level']),
            'hemoglobin': float(data['hemoglobin']),
            'insulin': float(data['insulin']),
            'triglycerides': float(data['triglycerides']),
            'hematocrit': float(data['hematocrit']),
            'red_blood_cells': float(data['red_blood_cells']),
            'smoking_history': data['smoking_history']
        }

        df = pd.DataFrame([row])
        print("🔎 DataFrame limpio listo para predecir:\n", df)

        # Obtener predicción y probabilidades
        probas = modelo_ml.predict_proba(df)[0]
        pred = modelo_ml.predict(df)[0]
        condicion = CLASES[pred]

        # Redondear a 2 decimales y convertir a porcentaje
        probabilidades = {
            CLASES[i]: round(float(prob) * 100, 2)  # ✅ conversión explícita
            for i, prob in enumerate(probas)
        }


        print(f"📊 Resultado: {condicion} con probabilidades: {probabilidades}")

        return jsonify({
            'condition': condicion,
            'probabilities': probabilidades
        })

    except Exception as e:
        print("❌ ERROR EN FLASK /predict:", str(e))
        return jsonify({'error': str(e)}), 500


@app.route('/recommend', methods=['POST'])
def recommend():
    try:
        data = request.get_json()
        print("📥 Datos recibidos en Flask /recommend:", data)

        if 'input' not in data or not isinstance(data['input'], list):
            return jsonify({'error': 'El campo "input" debe ser una lista válida'}), 400

        respuestas = data['input']
        if len(respuestas) < 2:
            return jsonify({'error': 'Se requieren al menos la condición y 1 hábito'}), 400

        conteo_categorias = Counter()
        for valor in respuestas:
            if G.has_node(valor):
                for vecino in G.neighbors(valor):
                    if G.nodes[vecino].get('tipo') == 'output':
                        conteo_categorias[vecino] += 1

        if not conteo_categorias:
            return jsonify({'recommendations': ['No se encontró una recomendación clara']}), 200

        top_recomendaciones = [cat for cat, _ in conteo_categorias.most_common(1)]
        return jsonify({'recommendations': top_recomendaciones})

    except Exception as e:
        print("❌ ERROR EN FLASK /recommend:", str(e))
        return jsonify({'error': str(e)}), 500

@app.route('/ping', methods=['GET'])
def ping():
    print("✅ Recibido ping desde backend")
    return jsonify({"flask": "conectado", "mensaje": {"message": "Flask está activo 🔥"}})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000, debug=True)

