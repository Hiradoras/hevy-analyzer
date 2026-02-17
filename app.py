import streamlit as st
import pandas as pd
import plotly.express as px

# Sayfa Ayarı
st.set_page_config(page_title="Antrenman Analizi", layout="wide")

st.title("🏋️ Powerbuilding Gelişim Takibi")

# 1. Veri Yükleme Alanı
uploaded_file = st.file_uploader("Hevy CSV dosyanı buraya yükle", type="csv")

if uploaded_file is not None:
    # Veriyi Oku
    df = pd.read_csv(uploaded_file)
    
    # Tarih formatını düzelt
    df['start_time'] = pd.to_datetime(df['start_time'])
    
    # Sidebar: Egzersiz Seçimi
    st.sidebar.header("Filtrele")
    egzersiz_listesi = df['exercise_title'].unique()
    secilen_egzersiz = st.sidebar.selectbox("Egzersiz Seç:", egzersiz_listesi)
    
    # Veriyi Filtrele
    filtered_df = df[df['exercise_title'] == secilen_egzersiz]
    
    # 2. Metrik Hesaplama (Basit 1RM Formülü: Ağırlık * (1 + (Tekrar/30)))
    filtered_df['1RM_Estimate'] = filtered_df['weight_kg'] * (1 + (filtered_df['reps'] / 30))
    
    # En iyi setleri bul (Her gün için en yüksek 1RM)
    daily_max = filtered_df.groupby('start_time')['1RM_Estimate'].max().reset_index()

    # 3. Grafikler
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(f"{secilen_egzersiz} - 1RM Gelişimi")
        fig_pr = px.line(daily_max, x='start_time', y='1RM_Estimate', markers=True)
        st.plotly_chart(fig_pr, use_container_width=True)
        
    with col2:
        st.subheader("Toplam Hacim (Set x Tekrar x Ağırlık)")
        # Hacim hesapla
        filtered_df['volume'] = filtered_df['weight_kg'] * filtered_df['reps']
        daily_volume = filtered_df.groupby('start_time')['volume'].sum().reset_index()
        fig_vol = px.bar(daily_volume, x='start_time', y='volume')
        st.plotly_chart(fig_vol, use_container_width=True)

    # İstatistik Tablosu
    st.write("Son Antrenman Verileri:")
    st.dataframe(filtered_df[['start_time', 'set_index', 'weight_kg', 'reps', 'rpe']].tail(10))

else:
    st.info("Lütfen Hevy'den indirdiğin CSV dosyasını yükle.")
