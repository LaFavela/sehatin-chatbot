from langchain_core.prompts import ChatPromptTemplate
from calculate import calculate_bmi, calculate_bmr, calculate_tdee
from retriever import food_retriever
import time
import json
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

load_dotenv()

model = OllamaLLM(
    model="llama3.2:3b",
    base_url=os.getenv("OLLAMA_URL")
)

template = """
Kamu adalah asisten chatbot yang cerdas dan ramah, bertugas membantu pengguna dalam hal informasi diet dan memberikan rekomendasi makanan yang tepat, akurat, dan disesuaikan dengan 'Data Pengguna'.

Ikuti petunjuk ini dengan sangat hati-hati:

- Semua jawaban dan rekomendasi makanan **hanya boleh** berdasarkan data makanan (`context`) yang diberikan dan permintaan pengguna.
- **Jangan** menggunakan pengetahuan umum atau tambahan di luar `context`.
- Jika makanan yang dibutuhkan tidak tersedia di `context`, berikan jawaban bahwa rekomendasi terbatas hanya pada data yang tersedia.
- Variasikan pilihan makanan, jangan mengulang makanan yang sama di waktu makan yang berbeda.
- Berikan rekomendasi makanan yang seimbang antara sayuran, daging maupun buah-buahan
- pertimbangkan saran dan permintaan pengguna
- Jawaban harus singkat, padat, dan sedikit penjelasan.

Format jawaban HARUS mengikuti struktur berikut:

SARAPAN (08:00)
- [KODE:XXXX] Nama Makanan (jumlah) - kalori
- [KODE:XXXX] Nama Makanan (jumlah) - kalori

MAKAN SIANG (12:30)
- [KODE:XXXX] Nama Makanan (jumlah) - kalori
- [KODE:XXXX] Nama Makanan (jumlah) - kalori

MAKAN MALAM (18:30)
- [KODE:XXXX] Nama Makanan (jumlah) - kalori
- [KODE:XXXX] Nama Makanan (jumlah) - kalori

Contoh format yang benar:
SARAPAN (08:00)
- [KODE:BP007] Ganyong (100g) - 100 kkal
- [KODE:DP016] Selada Rebus (100g) - 20 kkal

MAKAN SIANG (12:30)
- [KODE:DP012] Kacang Panjang (100g) - 30 kkal
- [KODE:DP020] Sayuran Bergizi (2 gelas) - 140 kkal

MAKAN MALAM (18:30)
- [KODE:CP009] Kacang Merah Segar (100g) - 144 kkal
- [KODE:BP007] Ganyong Rebus (100g) - 100 kkal

Ketentuan berdasarkan BMI pengguna:
- Jika BMI > 25 (obesitas):
  - Sarankan untuk menurunkan kebutuhan kalori secara bertahap.
  - Pilih makanan rendah kalori, tinggi serat, dan kaya nutrisi dari `context`.
- Jika BMI < 18.5 (underweight):
  - Sarankan untuk meningkatkan kebutuhan kalori.
  - Pilih makanan padat gizi, tinggi protein, dan kalori sehat dari `context`.
- Jika 18.5 <= BMI < 25 (normal):
  - Sarankan untuk mempertahankan pola makan seimbang dengan makanan dari `context`.

Data pengguna: 
- Kalori harian: {tdee}
- BMI: {BMI}
- Profil: {profile}

Context makanan tersedia:
{food_data}

Permintaan pengguna: {input}
"""

prompt = ChatPromptTemplate.from_template(template)
chain = prompt | model

def parse_food_recommendations(response, user_id):
    recommendations = []
    current_date = datetime.now().date()
    
    # Define meal times
    meal_times = {
        "SARAPAN": "08:00",
        "MAKAN SIANG": "12:30",
        "MAKAN MALAM": "18:30"
    }
    
    # Split response into lines
    lines = response.split('\n')
    current_meal = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check if line contains meal time
        for meal, time in meal_times.items():
            if meal in line:
                current_meal = meal
                break
                
        # Look for food code pattern [KODE:XXXX]
        code_match = re.search(r'\[KODE:(\w+)\]', line)
        if code_match and current_meal:
            code = code_match.group(1)
            # Extract food name and portion (everything between the code and the dash)
            food_info = line.split('[KODE:')[1].split(']')[1].split('-')[0].strip()
            # food_name = food_info.split('(')[0].strip()
            
            # Create datetime for the meal
            meal_time = datetime.strptime(meal_times[current_meal], "%H:%M").time()
            meal_datetime = datetime.combine(current_date, meal_time)
            
            recommendations.append({
                "food_id": code,
                "user_id": user_id,
                "schedule_at": meal_datetime.strftime("%Y-%m-%d %H:%M:%S")
            })
    
    return recommendations

def ask_ai_recomendation(name, activity, weight, height, age, gender, question):
    bmi = calculate_bmi(weight, height)
    bmr = calculate_bmr(weight, height, age, gender)
    tdee = calculate_tdee(activity, bmr)
    profile = f"{gender}, {age} tahun, {height}cm, {weight}kg, {activity}, {name}"
    
    food_data = food_retriever.invoke(question)
    
    # Measure response time
    start_time = time.time()
    # Create the prompt
    prompt_value = prompt.format_messages(
        input=question,
        tdee=tdee,
        BMI=bmi,
        profile=profile,
        food_data=food_data
    )
    # Stream the response
    response = ""
    for chunk in model.stream(prompt_value):
        print(chunk, end="", flush=True)
        response += chunk
    print()  # Add newline at the end
    
    # Parse and print JSON recommendations
    recommendations = parse_food_recommendations(response, "id_user_1")
    print("\nJSON Output:")
    print(json.dumps(recommendations, indent=2, ensure_ascii=False))
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Response time: {elapsed_time:.2f} seconds")
    return response, recommendations

while True:
    question = input("Masukkan pertanyaan: ")
    if question == "q":
        break
    response, recommendations = ask_ai_recomendation("Raihan", "Normal", 77, 165, 25, "Pria", question)