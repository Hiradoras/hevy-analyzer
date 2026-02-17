import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# Sayfa Ayarı
st.set_page_config(page_title="Antrenman Analizi", layout="wide")

st.title("🏋️ Powerbuilding Gelişim Takibi")
st.markdown("---")

# 1. Veri Yükleme Alanı
uploaded_file = st.file_uploader("Hevy CSV dosyanı buraya yükle", type="csv")

if uploaded_file is not None:
    # Veriyi Oku ve Ön İşleme
    try:
        df = pd.read_csv(uploaded_file)
        df['start_time'] = pd.to_datetime(df['start_time'])
        
        # Hacim ve 1RM Hesapla (Eğer sütunlar varsa)
        if all(col in df.columns for col in ['weight_kg', 'reps']):
             df['volume'] = df['weight_kg'] * df['reps']
             df['1RM_Estimate'] = df['weight_kg'] * (1 + (df['reps'] / 30))
        else:
            st.error("CSV dosyasında 'weight_kg' ve 'reps' sütunları bulunamadı. Lütfen doğru dosyayı yüklediğinden emin ol.")
            st.stop()

        # ---- SIDEBAR FİLTRELERİ ----
        st.sidebar.header("Filtreleme Seçenekleri")
        
        # Zaman Aralığı Filtresi
        time_range_option = st.sidebar.selectbox(
            "Zaman Aralığı Seç:",
            ["Tüm Zamanlar", "Son 3 Ay", "Son 6 Ay", "Son 1 Yıl", "Bu Yıl"]
        )
        
        now = datetime.now()
        if time_range_option == "Son 3 Ay":
            start_date = now - timedelta(days=90)
        elif time_range_option == "Son 6 Ay":
            start_date = now - timedelta(days=180)
        elif time_range_option == "Son 1 Yıl":
            start_date = now - timedelta(days=365)
        elif time_range_option == "Bu Yıl":
            start_date = datetime(now.year, 1, 1)
        else: # Tüm Zamanlar
            start_date = df['start_time'].min()
            
        filtered_df_time = df[df['start_time'] >= start_date]

        # Egzersiz Filtresi (Zamanla filtrelenmiş veri üzerinden)
        egzersiz_listesi = filtered_df_time['exercise_title'].unique()
        default_ix = 0
        if "Bench Press (Barbell)" in egzersiz_listesi:
             default_ix = list(egzersiz_listesi).index("Bench Press (Barbell)")
             
        secilen_egzersiz = st.sidebar.selectbox("Egzersiz Seç (1RM Grafiği İçin):", egzersiz_listesi, index=default_ix)
        
        # Seçilen Egzersiz için Veri
        filtered_df_exercise = filtered_df_time[filtered_df_time['exercise_title'] == secilen_egzersiz]
        
        # ---- GRAFİK HAZIRLAMA ----
        
        # Grafik 1: 1RM Gelişimi (Seçilen Egzersiz)
        daily_max_1rm = filtered_df_exercise.groupby(filtered_df_exercise['start_time'].dt.date)['1RM_Estimate'].max().reset_index()
        fig_pr = px.line(
            daily_max_1rm, 
            x='start_time', 
            y='1RM_Estimate', 
            markers=True,
            title=f"{secilen_egzersiz} - Tahmini 1RM Gelişimi",
            labels={'start_time': 'Tarih', '1RM_Estimate': '1RM (kg)'},
            template="plotly_white" # Daha temiz bir tema
        )
        fig_pr.update_traces(line_color='#1f77b4', marker_size=8, line_width=3)
        fig_pr.update_layout(hovermode="x unified") # Fare üzerine gelince tüm veriyi göster
        
        # Grafik 2: Toplam Hacim (Seçilen Egzersiz)
        daily_volume_exercise = filtered_df_exercise.groupby(filtered_df_exercise['start_time'].dt.date)['volume'].sum().reset_index()
        fig_vol_exercise = px.bar(
            daily_volume_exercise,
            x='start_time',
            y='volume',
            title=f"{secilen_egzersiz} - Antrenman Başına Hacim",
            labels={'start_time': 'Tarih', 'volume': 'Toplam Hacim (kg)'},
            template="plotly_white",
            color='volume', # Hacme göre renk değiştir
            color_continuous_scale=px.colors.sequential.Blues # Mavi tonları
        )
        fig_vol_exercise.update_layout(hovermode="x unified")

        # Grafik 3: Kas Grubu Dağılımı (Tüm Egzersizler - Seçilen Zaman Aralığında)
        # 'muscle_group' sütununun varlığını kontrol et
        if 'muscle_group' in filtered_df_time.columns:
             muscle_group_volume = filtered_df_time.groupby('muscle_group')['volume'].sum().reset_index()
             fig_muscle = px.pie(
                 muscle_group_volume,
                 values='volume',
                 names='muscle_group',
                 title=f"Kas Grubu Hacim Dağılımı ({time_range_option})",
                 template="plotly_white",
                 hole=0.4 # Donut chart görünümü
             )
             fig_muscle.update_traces(textposition='inside', textinfo='percent+label')
        else:
            fig_muscle = None
            st.warning("Kas grubu analizi için CSV dosyasında 'muscle_group' sütunu bulunamadı.")

        # ---- GÖRÜNTÜLEME ----
        
        # Üst Kısım: Seçilen Egzersiz Grafikleri
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(fig_pr, use_container_width=True)
        with col2:
            st.plotly_chart(fig_vol_exercise, use_container_width=True)

        st.markdown("---")

        # Alt Kısım: Genel Analiz ve Tablo
        col3, col4 = st.columns([1, 2]) # Grafiğe daha az, tabloya daha çok yer ver
        
        with col3:
             if fig_muscle:
                  st.plotly_chart(fig_muscle, use_container_width=True)
             else:
                  st.write("Kas grubu verisi yok.")

        with col4:
            st.subheader(f"{secilen_egzersiz} - Son Antrenman Verileri")
            st.dataframe(
                filtered_df_exercise[['start_time', 'set_index', 'weight_kg', 'reps', 'rpe', '1RM_Estimate']].tail(10).style.format({'1RM_Estimate': '{:.1f}'})
            )

    except Exception as e:
        st.error(f"Bir hata oluştu: {e}")
        st.info("Lütfen Hevy'den indirilen standart bir CSV dosyası yüklediğinden emin ol.")

else:
    st.info("Analize başlamak için lütfen Hevy'den indirdiğin CSV dosyasını yukarıya yükle.")
