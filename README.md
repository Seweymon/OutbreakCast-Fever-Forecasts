# 🌡️ OutbreakCast — AI-Driven Fever Outbreak Prediction  
**Microlabs Hackathon 2025 | AI + Pharma = Smarter, Faster, Safer Healthcare**

OutbreakCast is an **AI-powered fever outbreak prediction system** that forecasts **dengue, chikungunya, and enteric fever** across Indian districts up to **4 weeks in advance**.  
Built for the **Microlabs Hackathon 2025**, it empowers public-health teams to act early, allocate resources, and save lives.

---

## 🚀 What It Does
- Predicts district-level fever trends using AI, weather, and epidemiological data  
- Generates **risk bands (Green / Amber / Red)** for quick outbreak alerts  
- Provides an **interactive Streamlit dashboard** for analysis and visualization  
- Scales easily for real-time monitoring and decision support  

---

## 🧠 Tech Stack
**Languages / Libraries:** Python · Pandas · NumPy · scikit-learn · XGBoost  
**Dashboard:** Streamlit · Altair  
**Environment:** Jupyter / Google Colab  

---

## 📊 Data Sources
- **IDSP Weekly Outbreak Reports** – [idsp.mohfw.gov.in](https://idsp.mohfw.gov.in)  
- **NCVBDC (Vector Borne Diseases Data)** – [ncvbdc.mohfw.gov.in](https://ncvbdc.mohfw.gov.in)  
- **IMD / NASA IMERG** – Rainfall and temperature datasets  
- **Census 2011** – Population baselines  

---

## ⚙️ How to Run
```bash
git clone https://github.com/Seweymon/OutbreakCast-Fever-Forecasts.git
cd OutbreakCast-Fever-Forecasts
pip install -r requirements.txt
streamlit run app.py
