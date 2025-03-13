import streamlit as st
import os
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import geopandas as gpd
import contextily as ctx
from matplotlib.colors import LinearSegmentedColormap
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import time

current_dir = os.path.dirname(os.path.abspath(__file__))

csv_path = os.path.join(current_dir, 'main_data.csv')

main_data = pd.read_csv(csv_path)

main_data["datetime"] = pd.to_datetime(main_data["datetime"])
main_data["Hour"] = main_data["datetime"].dt.hour
main_data["month_year"] = main_data["datetime"].dt.to_period("M").astype(str)

pollutants = ["PM2.5", "PM10", "SO2", "NO2", "CO", "O3"]
stations = main_data["station"].unique()

st.title('Proyek Analisis Data: Air Quality Dataset')

st.write("""
        Nama        : Siti Nurbayanah\n
        Email       : sitinurbayanah24@gmail.com\n
        ID Dicoding : MC222D5X1273""")

tab1, tab2, tab3, tab4 = st.tabs(["Pertanyaan 1", "Pertanyaan 2", "Pertanyaan 3", "Pertanyaan 4"])

with st.sidebar:
    st.header("Pengaturan Tab 1")
    selected_station_tab1 = st.selectbox("Pilih stasiun:", stations if len(stations) > 0 else ["Tidak ada stasiun"])
    selected_pollutants_tab1 = st.multiselect("Pilih polutan:", pollutants, default=["PM2.5"])
with tab1:
    st.header("Bagaimana pola perubahan polutan sepanjang waktu?")
    
    if not selected_pollutants_tab1:
        st.warning("Pilih minimal satu polutan.")
    else:
        station_data = main_data[main_data["station"] == selected_station_tab1]

        if station_data.empty:
            st.warning(f"Tidak ada data untuk stasiun {selected_station_tab1}. Pilih stasiun lain.")
        else:
            station_monthly = station_data.groupby("month_year")[selected_pollutants_tab1].mean().reset_index()
            station_monthly = station_monthly.sort_values("month_year")
            
            fig, ax = plt.subplots(figsize=(12, 6))
            for pollutant in selected_pollutants_tab1:
                sns.lineplot(data=station_monthly, x="month_year", y=pollutant, label=pollutant, marker="o", ax=ax)

            ax.set_title(f"Tren Polutan Per Bulan di {selected_station_tab1}")
            ax.set_xlabel("Bulan")
            ax.set_ylabel("Konsentrasi (µg/m³)")
            plt.xticks(rotation=45)
            ax.legend(title="Polutan")
            ax.grid(True)
            st.pyplot(fig)

with tab2:
    st.header("Bagaimana distribusi polusi udara di berbagai lokasi, lalu tempat mana yang memiliki polutan tertinggi?")
    
    main_data["datetime"] = pd.to_datetime(main_data["datetime"])
    pollutants = ["PM2.5", "PM10", "SO2", "NO2", "CO", "O3"]

    station_avg = main_data.groupby("station")[pollutants].mean().reset_index()
    station_avg["total_pollution"] = station_avg[pollutants].sum(axis=1)
    highest_station = station_avg.loc[station_avg["total_pollution"].idxmax(), "station"]

    melted_data = station_avg.melt(id_vars=["station"], var_name="pollutant", value_name="concentration")

    fig, ax = plt.subplots(figsize=(14, 6))
    sns.barplot(data=melted_data, x="station", y="concentration", hue="pollutant", palette="tab10", ax=ax)
    ax.set_title("Perbandingan Rata-rata Konsentrasi Polutan di Setiap Stasiun")
    ax.set_xlabel("Stasiun")
    ax.set_ylabel("Konsentrasi (µg/m³)")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45)

    for label in ax.get_xticklabels():
        if label.get_text() == highest_station:
            label.set_color("red")
            label.set_fontweight("bold")

    ax.legend(title="Polutan")
    ax.grid(axis="y", linestyle="--", alpha=0.7)
    st.pyplot(fig)

with st.sidebar:
    st.header("Pengaturan Tab 3")
    selected_pollutant_tab4 = st.selectbox("Pilih polutan:", pollutants)
with tab3:
    st.header("Bagaimana perbedaan kualitas udara antara pagi, siang, dan malam?")
    
    hourly_avg = main_data.groupby("Hour")[selected_pollutant_tab4].mean()
    best_hour = hourly_avg.idxmin()
    worst_hour = hourly_avg.idxmax()
    best_value = hourly_avg.min()
    worst_value = hourly_avg.max()
    morning_avg = hourly_avg[6:12].mean()
    afternoon_avg = hourly_avg[12:18].mean()
    night_avg = pd.concat([hourly_avg[18:24], hourly_avg[0:6]]).mean()

    fig, ax = plt.subplots(figsize=(12, 6))

    ax.plot(hourly_avg.index, hourly_avg.values, marker="o", linestyle="-", color="blue", label=f"{selected_pollutant_tab4} per jam")
    ax.axvspan(6, 12, color="yellow", alpha=0.2, label=f"Pagi (Rata-rata: {morning_avg:.2f})")
    ax.axvspan(12, 18, color="orange", alpha=0.2, label=f"Siang (Rata-rata: {afternoon_avg:.2f})")
    ax.axvspan(18, 24, color="purple", alpha=0.2, label=f"Malam")
    ax.axvspan(0, 6, color="purple", alpha=0.2)

    ax.scatter(best_hour, best_value, color="green", s=100, zorder=5, 
            label=f"Terbaik: Jam {best_hour}:00 ({best_value:.2f})")
    ax.scatter(worst_hour, worst_value, color="red", s=100, zorder=5, 
            label=f"Terburuk: Jam {worst_hour}:00 ({worst_value:.2f})")

    ax.set_xlabel("Jam dalam Sehari")
    ax.set_ylabel(f"Rata-rata {selected_pollutant_tab4}")
    ax.set_title(f"Perbandingan {selected_pollutant_tab4} Berdasarkan Waktu")
    ax.set_xticks(range(0, 24, 2))
    ax.grid(alpha=0.3)
    ax.legend(loc="upper right")

    st.pyplot(fig)
    st.markdown(f"""
    ###Perbandingan {selected_pollutant_tab4}:
    - **Pagi**: {morning_avg:.2f} µg/m³
    - **Siang**: {afternoon_avg:.2f} µg/m³
    - **Malam**: {night_avg:.2f} µg/m³  

    **Kualitas Udara Terbaik**: Jam {best_hour}:00 ({best_value:.2f} µg/m³)  
    **Kualitas Udara Terburuk**: Jam {worst_hour}:00 ({worst_value:.2f} µg/m³)
    """)
    
with tab4:
    st.subheader("Visualisasi Kategori Kualitas Udara per Stasiun Berdasarkan Polutan")
    
    try:
        # Import libraries
        from geopy.geocoders import Nominatim
        from geopy.extra.rate_limiter import RateLimiter
        import geopandas as gpd
        import contextily as ctx
        import matplotlib.pyplot as plt
        
        # Setup geocoder with rate limiting and error handling
        geolocator = Nominatim(user_agent="geo_lookup", timeout=10)
        geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1, max_retries=5)

        # Handle cache file
        cache_file = "geocoding_cache.csv"
        try:
            if os.path.exists(cache_file):
                cache = pd.read_csv(cache_file)
            else:
                cache = pd.DataFrame(columns=["station", "latitude", "longitude"])
        except Exception as e:
            st.warning(f"Tidak dapat mengakses cache: {e}")
            cache = pd.DataFrame(columns=["station", "latitude", "longitude"])

        def get_coordinates(station_name):
            if station_name in cache["station"].values:
                row = cache[cache["station"] == station_name].iloc[0]
                return row["latitude"], row["longitude"]
            try:
                location = geocode(station_name + ", China")
                if location:
                    cache.loc[len(cache)] = [station_name, location.latitude, location.longitude]
                    try:
                        cache.to_csv(cache_file, index=False)
                    except Exception as e:
                        st.warning(f"Tidak dapat menyimpan cache: {e}")
                    return location.latitude, location.longitude
                else:
                    return None, None
            except Exception as e:
                st.warning(f"Error geocoding {station_name}: {e}")
                return None, None

        # Load data
        file_path = "main_data.csv"
        if not os.path.exists(file_path):
            st.error(f"File tidak ditemukan: {file_path}")
            st.stop()
            
        if 'main_data' not in locals() or 'main_data' not in st.session_state:
            try:
                main_data = pd.read_csv(file_path)
                if 'main_data' not in st.session_state:
                    st.session_state.main_data = main_data
            except Exception as e:
                st.error(f"Error membaca file: {e}")
                st.stop()
        else:
            main_data = st.session_state.main_data if 'main_data' in st.session_state else locals()['main_data']
            
        # Convert datetime column
        if "datetime" in main_data.columns:
            main_data["datetime"] = pd.to_datetime(main_data["datetime"])

        # Get stations and their coordinates
        stations = main_data["station"].unique()
        station_coords = pd.DataFrame(stations, columns=["station"])
        
        geocoding_status = st.empty()
        with st.spinner("Mendapatkan koordinat stasiun..."):
            coord_results = [get_coordinates(station) for station in station_coords["station"]]
        
        station_coords["latitude"] = [lat for lat, lon in coord_results]
        station_coords["longitude"] = [lon for lat, lon in coord_results]
        
        # Merge coordinates with main data
        main_data = main_data.merge(station_coords, on="station", how="left")

        # Filter data for last week if datetime column exists
        if "datetime" in main_data.columns:
            latest_date = main_data["datetime"].max()
            one_week_data = main_data[main_data["datetime"] >= (latest_date - pd.DateOffset(weeks=1))]
        else:
            one_week_data = main_data

        # Clean and convert coordinate data
        one_week_data.loc[:, "longitude"] = pd.to_numeric(one_week_data["longitude"], errors="coerce")
        one_week_data.loc[:, "latitude"] = pd.to_numeric(one_week_data["latitude"], errors="coerce")
        one_week_data = one_week_data.dropna(subset=["longitude", "latitude"])
        one_week_data = one_week_data[
            (one_week_data["longitude"] != float("inf")) & 
            (one_week_data["longitude"] != float("-inf")) &
            (one_week_data["latitude"] != float("inf")) & 
            (one_week_data["latitude"] != float("-inf"))
        ]

        # Function to visualize pollutant data
        def visualize_pollutant(data, pollutant="PM2.5"):
            aqi_standards = {
                "PM2.5": {
                    "Baik": 12.0,
                    "Sedang": 35.4,
                    "Tidak Sehat untuk Kelompok Sensitif": 55.4,
                    "Tidak Sehat": 150.4,
                    "Sangat Tidak Sehat": 250.4,
                    "Berbahaya": float('inf')
                },
                "PM10": {
                    "Baik": 54.0,
                    "Sedang": 154.0,
                    "Tidak Sehat untuk Kelompok Sensitif": 254.0,
                    "Tidak Sehat": 354.0,
                    "Sangat Tidak Sehat": 424.0,
                    "Berbahaya": float('inf')
                },
                "SO2": {
                    "Baik": 35.0,
                    "Sedang": 75.0,
                    "Tidak Sehat untuk Kelompok Sensitif": 185.0,
                    "Tidak Sehat": 304.0,
                    "Sangat Tidak Sehat": 604.0,
                    "Berbahaya": float('inf')
                },
                "NO2": {
                    "Baik": 53.0,
                    "Sedang": 100.0,
                    "Tidak Sehat untuk Kelompok Sensitif": 360.0,
                    "Tidak Sehat": 649.0,
                    "Sangat Tidak Sehat": 1249.0,
                    "Berbahaya": float('inf')
                },
                "CO": {
                    "Baik": 4.4,
                    "Sedang": 9.4,
                    "Tidak Sehat untuk Kelompok Sensitif": 12.4,
                    "Tidak Sehat": 15.4,
                    "Sangat Tidak Sehat": 30.4,
                    "Berbahaya": float('inf')
                },
                "O3": {
                    "Baik": 54.0,
                    "Sedang": 70.0,
                    "Tidak Sehat untuk Kelompok Sensitif": 85.0,
                    "Tidak Sehat": 105.0,
                    "Sangat Tidak Sehat": 200.0,
                    "Berbahaya": float('inf')
                }
            }
            
            def get_category(value, pollutant_standards):
                for category, threshold in pollutant_standards.items():
                    if value <= threshold:
                        return category
                return "Data Tidak Tersedia"
            
            # Calculate average pollutant value for each station
            station_avg_pollutant = data.groupby("station")[pollutant].mean().reset_index()
            station_avg_pollutant = station_avg_pollutant.merge(station_coords, on="station", how="left")
            
            # Check if we have valid data for the map
            if station_avg_pollutant.empty or station_avg_pollutant["latitude"].isnull().all() or station_avg_pollutant["longitude"].isnull().all():
                st.warning("Tidak ada data koordinat yang valid untuk visualisasi.")
                return None
            
            # Create GeoDataFrame for mapping
            try:
                gdf_stations = gpd.GeoDataFrame(
                    station_avg_pollutant, 
                    geometry=gpd.points_from_xy(station_avg_pollutant["longitude"], station_avg_pollutant["latitude"]), 
                    crs="EPSG:4326"
                )
                
                # Transform coordinates to web mercator for compatibility with basemap
                gdf_stations = gdf_stations.to_crs(epsg=3857)
            except Exception as e:
                st.error(f"Error membuat GeoDataFrame: {e}")
                return None
            
            # Categorize air quality based on pollutant value
            gdf_stations["kategori_udara"] = gdf_stations[pollutant].apply(
                lambda x: get_category(x, aqi_standards[pollutant])
            )
            
            # Define colors for each air quality category
            category_colors = {
                "Baik": "#00e400",
                "Sedang": "#ffff00",
                "Tidak Sehat untuk Kelompok Sensitif": "#ff7e00",
                "Tidak Sehat": "#ff0000",
                "Sangat Tidak Sehat": "#8F3F97",
                "Berbahaya": "#7e0023",
                "Data Tidak Tersedia": "#999999"
            }
            gdf_stations["color"] = gdf_stations["kategori_udara"].map(category_colors)
            
            # Create the map
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # Plot points for each category with appropriate color
            for category, color in category_colors.items():
                subset = gdf_stations[gdf_stations["kategori_udara"] == category]
                if not subset.empty:
                    subset.plot(
                        ax=ax,
                        color=color,
                        markersize=100,
                        alpha=0.8,
                        edgecolor="black",
                        label=category
                    )
            
            # Add basemap
            try:
                ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron)
            except Exception as e:
                st.warning(f"Tidak dapat menambahkan basemap: {e}")
            
            # Add station labels
            for idx, row in gdf_stations.iterrows():
                ax.annotate(
                    text=f"{row['station']}\n{row[pollutant]:.1f}",
                    xy=(row.geometry.x, row.geometry.y),
                    xytext=(3, 3),
                    textcoords="offset points",
                    fontsize=8,
                    color='black',
                    fontweight='bold',
                    bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.7)
                )
            
            # Add legend
            ax.legend(title="Kategori Kualitas Udara", loc="lower right")
            
            # Add title with appropriate units
            units = {
                "PM2.5": "μg/m³",
                "PM10": "μg/m³",
                "SO2": "μg/m³",
                "NO2": "μg/m³",
                "CO": "mg/m³",
                "O3": "μg/m³"
            }
            
            unit = units.get(pollutant, "")
            plt.title(f"Kategori Kualitas Udara Berdasarkan {pollutant} ({unit}) per Stasiun", fontsize=14)
            plt.tight_layout()
            return fig

        # Show alternative simple map if the complex one fails
        def show_simple_map(data, pollutant):
            st.subheader(f"Peta Sederhana Stasiun Berdasarkan {pollutant}")
            map_data = data.groupby('station')[['latitude', 'longitude', pollutant]].mean().reset_index()
            map_data = map_data.dropna(subset=['latitude', 'longitude'])
            
            if not map_data.empty:
                st.map(map_data, size=map_data[pollutant]/map_data[pollutant].mean()*50)
            else:
                st.warning("Tidak ada data koordinat valid untuk ditampilkan.")

        # Get available pollutants from data
        available_pollutants = [col for col in one_week_data.columns if col in ["PM2.5", "PM10", "SO2", "NO2", "CO", "O3"]]    
        if not available_pollutants:
            st.error("Tidak ada data polutan yang tersedia.")
            st.stop()
        
        # Select pollutant to visualize
        selected_pollutant = st.selectbox(
            "Pilih polutan untuk divisualisasikan:",
            available_pollutants,
            index=0
        )

        # Display the visualization
        if selected_pollutant:
            with st.spinner(f"Menampilkan visualisasi untuk {selected_pollutant}..."):
                try:
                    fig = visualize_pollutant(one_week_data, selected_pollutant)
                    if fig:
                        st.pyplot(fig)
                    else:
                        st.warning("Tidak dapat membuat visualisasi utama. Menampilkan peta alternatif...")
                        show_simple_map(one_week_data, selected_pollutant)
                except Exception as e:
                    st.error(f"Error saat membuat visualisasi: {e}")
                    st.write("Detail error:")
                    st.exception(e)
                    st.warning("Menampilkan peta alternatif...")
                    show_simple_map(one_week_data, selected_pollutant)

    except Exception as e:
        st.error(f"Terjadi kesalahan pada tab visualisasi: {e}")
        st.exception(e)
