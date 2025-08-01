import streamlit as st
import pandas as pd
import yfinance as yf
import time
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Configuración de la página
st.set_page_config(
    page_title="📊 Dashboard Financiero Avanzado",
    layout="wide",
    page_icon="📈",
    initial_sidebar_state="expanded"
)

# Parámetros iniciales WACC
Rf = 0.0435  # Tasa libre de riesgo
Rm = 0.085   # Retorno esperado del mercado
Tc = 0.21    # Tasa impositiva corporativa

def calcular_wacc_y_roic(ticker):
    """
    Calcula el WACC y el ROIC de una empresa usando únicamente datos de yfinance,
    e incluye una evaluación de si la empresa está creando valor (Relación ROIC-WACC).
    """
    try:
        empresa = yf.Ticker(ticker)
        
        # Pausa para evitar bloqueos de Yahoo Finance
        time.sleep(1)  # Esperamos 1 segundo entre las solicitudes
        
        # Información básica
        market_cap = empresa.info.get('marketCap', 0)  # Capitalización de mercado (valor de mercado del patrimonio)
        beta = empresa.info.get('beta', 1)  # Beta de la empresa
        rf = 0.02  # Tasa libre de riesgo (asumida como 2%)
        equity_risk_premium = 0.05  # Prima de riesgo del mercado (asumida como 5%)
        ke = rf + beta * equity_risk_premium  # Costo del capital accionario (CAPM)
        
        balance_general = empresa.balance_sheet
        deuda_total = balance_general.loc['Total Debt'].iloc[0] if 'Total Debt' in balance_general.index else 0
        efectivo = balance_general.loc['Cash And Cash Equivalents'].iloc[0] if 'Cash And Cash Equivalents' in balance_general.index else 0
        patrimonio = balance_general.loc['Common Stock Equity'].iloc[0] if 'Common Stock Equity' in balance_general.index else 0
        
        estado_resultados = empresa.financials
        gastos_intereses = estado_resultados.loc['Interest Expense'].iloc[0] if 'Interest Expense' in estado_resultados.index else 0
        ebt = estado_resultados.loc['Ebt'].iloc[0] if 'Ebt' in estado_resultados.index else 0
        impuestos = estado_resultados.loc['Income Tax Expense'].iloc[0] if 'Income Tax Expense' in estado_resultados.index else 0
        ebit = estado_resultados.loc['EBIT'].iloc[0] if 'EBIT' in estado_resultados.index else 0

        # Pausa después de obtener datos financieros
        time.sleep(1)
        
        # Calcular Kd (costo de la deuda)
        kd = gastos_intereses / deuda_total if deuda_total != 0 else 0

        # Calcular tasa de impuestos efectiva
        tasa_impuestos = impuestos / ebt if ebt != 0 else 0.21  # Asume 21% si no hay datos
        
        # Calcular WACC
        total_capital = market_cap + deuda_total
        wacc = ((market_cap / total_capital) * ke) + ((deuda_total / total_capital) * kd * (1 - tasa_impuestos))
        
        # Calcular ROIC
        nopat = ebit * (1 - tasa_impuestos)  # NOPAT
        capital_invertido = patrimonio + (deuda_total - efectivo)  # Capital Invertido
        roic = nopat / capital_invertido if capital_invertido != 0 else 0
        
        # Calcular Relación ROIC-WACC
        diferencia_roic_wacc = roic - wacc
        creando_valor = roic > wacc  # Determina si está creando valor

        return wacc, roic, diferencia_roic_wacc
        
    except Exception as e:
        st.error(f"Error al calcular WACC y ROIC para {ticker.upper()}: {e}")
        return None, None, None

# Función para obtener los datos financieros de cada ticker
def obtener_datos_financieros(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        bs = stock.balance_sheet
        fin = stock.financials
        cf = stock.cashflow

        # Datos básicos
        price = info.get("currentPrice")
        name = info.get("longName", ticker)
        sector = info.get("sector", "N/D")
        country = info.get("country", "N/D")
        industry = info.get("industry", "N/D")

        # Ratios de valoración
        pe = info.get("trailingPE")
        pb = info.get("priceToBook")
        dividend = info.get("dividendRate")
        dividend_yield = info.get("dividendYield")
        payout = info.get("payoutRatio")
        
        # Ratios de rentabilidad
        roa = info.get("returnOnAssets")
        roe = info.get("returnOnEquity")
        
        # Ratios de liquidez
        current_ratio = info.get("currentRatio")
        quick_ratio = info.get("quickRatio")
        
        # Ratios de deuda
        ltde = info.get("longTermDebtToEquity")
        de = info.get("debtToEquity")
        
        # Margenes
        op_margin = info.get("operatingMargins")
        profit_margin = info.get("profitMargins")
        
        # Flujo de caja
        fcf = cf.loc["Free Cash Flow"].iloc[0] if "Free Cash Flow" in cf.index else None
        shares = info.get("sharesOutstanding")
        pfcf = price / (fcf / shares) if fcf and shares else None
        
        # Llamada a la nueva función para obtener WACC y ROIC
        wacc, roic, diferencia_roic_wacc = calcular_wacc_y_roic(ticker)

        return {
            "Ticker": ticker,
            "Nombre": name,
            "Sector": sector,
            "País": country,
            "Industria": industry,
            "Precio": price,
            "P/E": pe,
            "P/B": pb,
            "P/FCF": pfcf,
            "Dividend Year": dividend,
            "Dividend Yield %": dividend_yield,
            "Payout Ratio": payout,
            "ROA": roa,
            "ROE": roe,
            "Current Ratio": current_ratio,
            "Quick Ratio": quick_ratio,
            "LtDebt/Eq": ltde,
            "Debt/Eq": de,
            "Oper Margin": op_margin,
            "Profit Margin": profit_margin,
            "WACC": wacc,
            "ROIC": roic,
            "Creación de Valor (WACC vs ROIC)": diferencia_roic_wacc,
        }
    except Exception as e:
        return {"Ticker": ticker, "Error": str(e)}

# Interfaz de usuario
def main():
    st.title("📊 Dashboard de Análisis Financiero Avanzado")
    
    # Sidebar con configuración
    with st.sidebar:
        st.header("⚙️ Configuración")
        tickers_input = st.text_area(
            "🔎 Ingresa tickers (separados por coma)", 
            "AAPL, MSFT, GOOGL, AMZN, TSLA",
            help="Ejemplo: AAPL, MSFT, GOOG"
        )
        max_tickers = st.slider("Número máximo de tickers", 1, 100, 50)
        
        st.markdown("---")
        st.markdown("**Parámetros WACC**")
        global Rf, Rm, Tc
        Rf = st.number_input("Tasa libre de riesgo (%)", min_value=0.0, max_value=20.0, value=4.35) / 100
        Rm = st.number_input("Retorno esperado del mercado (%)", min_value=0.0, max_value=30.0, value=8.5) / 100
        Tc = st.number_input("Tasa impositiva corporativa (%)", min_value=0.0, max_value=50.0, value=21.0) / 100
    
    # Procesamiento de tickers
    tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()][:max_tickers]
    
    if st.button("🔍 Analizar Acciones", type="primary"):
        if not tickers:
            st.warning("Por favor ingresa al menos un ticker")
            return
            
        resultados = {}
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Procesamos los tickers en lotes de 10
        batch_size = 10
        for batch_start in range(0, len(tickers), batch_size):
            batch_end = min(batch_start + batch_size, len(tickers))
            batch_tickers = tickers[batch_start:batch_end]
            
            for i, t in enumerate(batch_tickers):
                status_text.text(f"⏳ Procesando {t} ({batch_start + i + 1}/{len(tickers)})...")
                resultados[t] = obtener_datos_financieros(t)
                progress_bar.progress((batch_start + i + 1) / len(tickers))
                time.sleep(1)  # Para evitar bloqueos de la API
            
        status_text.text("✅ Análisis completado!")
        time.sleep(0.5)
        status_text.empty()
        progress_bar.empty()
        
        # Mostrar resultados
        if resultados:
            datos = list(resultados.values())
            
            # Filtramos empresas con errores
            datos_validos = [d for d in datos if "Error" not in d]
            if not datos_validos:
                st.error("No se pudo obtener datos válidos para ningún ticker")
                return
                
            df = pd.DataFrame(datos_validos)
            
            # Sección 1: Resumen General
            st.header("📋 Resumen General")
            
            # Formatear columnas porcentuales
            porcentajes = ["Dividend Yield %", "ROA", "ROE", "Oper Margin", "Profit Margin", "WACC", "ROIC"]
            for col in porcentajes:
                if col in df.columns:
                    df[col] = df[col].apply(lambda x: f"{x:.2%}" if pd.notnull(x) else "N/D")
            
            columnas_mostrar = [
                "Ticker", "Nombre", "Sector", "Precio", "P/E", "P/B", "P/FCF", 
                "Dividend Yield %", "ROE", "Debt/Eq", "Profit Margin", "WACC", "ROIC", "Creación de Valor (WACC vs ROIC)"
            ]
            
            st.dataframe(
                df[columnas_mostrar].dropna(how='all', axis=1),
                use_container_width=True,
                height=400
            )
            
            # Sección 2: Análisis de Valoración
            st.header("💰 Análisis de Valoración")
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Ratios de Valoración")
                fig, ax = plt.subplots(figsize=(10, 4))
                df_plot = df[["Ticker", "P/E", "P/B", "P/FCF"]].set_index("Ticker").apply(pd.to_numeric, errors='coerce')
                df_plot.plot(kind="bar", ax=ax, rot=45)
                ax.set_title("Comparativa de Ratios de Valoración")
                ax.set_ylabel("Ratio")
                st.pyplot(fig)
                plt.close()
                
            with col2:
                st.subheader("Dividendos")
                fig, ax = plt.subplots(figsize=(10, 4))
                df_plot = df[["Ticker", "Dividend Yield %"]].set_index("Ticker")
                df_plot["Dividend Yield %"] = df_plot["Dividend Yield %"].replace("N/D", 0)
                df_plot["Dividend Yield %"] = df_plot["Dividend Yield %"].str.rstrip("%").astype("float")
                df_plot.plot(kind="bar", ax=ax, rot=45, color="green")
                ax.set_title("Rendimiento de Dividendos (%)")
                ax.set_ylabel("Dividend Yield %")
                st.pyplot(fig)
                plt.close()
            
            # Sección 3: Rentabilidad y Eficiencia
            st.header("📈 Rentabilidad y Eficiencia")
            
            tabs = st.tabs(["ROE vs ROA", "Margenes", "WACC vs ROIC"])
            
            with tabs[0]:
                fig, ax = plt.subplots(figsize=(10, 5))
                df_plot = df[["Ticker", "ROE", "ROA"]].set_index("Ticker")
                df_plot["ROE"] = df_plot["ROE"].str.rstrip("%").astype("float")
                df_plot["ROA"] = df_plot["ROA"].str.rstrip("%").astype("float")
                df_plot.plot(kind="bar", ax=ax, rot=45)
                ax.set_title("ROE vs ROA (%)")
                ax.set_ylabel("Porcentaje")
                st.pyplot(fig)
                plt.close()
                
            with tabs[1]:
                fig, ax = plt.subplots(figsize=(10, 5))
                df_plot = df[["Ticker", "Oper Margin", "Profit Margin"]].set_index("Ticker")
                df_plot["Oper Margin"] = df_plot["Oper Margin"].str.rstrip("%").astype("float")
                df_plot["Profit Margin"] = df_plot["Profit Margin"].str.rstrip("%").astype("float")
                df_plot.plot(kind="bar", ax=ax, rot=45)
                ax.set_title("Margen Operativo vs Margen Neto (%)")
                ax.set_ylabel("Porcentaje")
                st.pyplot(fig)
                plt.close()
                
            with tabs[2]:
                fig, ax = plt.subplots(figsize=(10, 5))
                for _, row in df.iterrows():
                    wacc = float(row["WACC"].rstrip("%")) if row["WACC"] != "N/D" else None
                    roic = float(row["ROIC"].rstrip("%")) if row["ROIC"] != "N/D" else None
                    
                    if wacc and roic:
                        color = "green" if roic > wacc else "red"
                        ax.bar(row["Ticker"], roic, color=color, alpha=0.6, label="ROIC")
                        ax.bar(row["Ticker"], wacc, color="gray", alpha=0.3, label="WACC")
                
                ax.set_title("Creación de Valor: ROIC vs WACC (%)")
                ax.set_ylabel("Porcentaje")
                ax.legend()
                st.pyplot(fig)
                plt.close()
            
            # Sección 4: Análisis de Deuda
            st.header("🏦 Estructura de Capital y Deuda")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Apalancamiento")
                fig, ax = plt.subplots(figsize=(10, 5))
                df_plot = df[["Ticker", "Debt/Eq", "LtDebt/Eq"]].set_index("Ticker")
                df_plot = df_plot.apply(pd.to_numeric, errors='coerce')
                df_plot.plot(kind="bar", stacked=True, ax=ax, rot=45)
                ax.axhline(1, color="red", linestyle="--")
                ax.set_title("Deuda/Patrimonio")
                ax.set_ylabel("Ratio")
                st.pyplot(fig)
                plt.close()
                
            with col2:
                st.subheader("Liquidez")
                fig, ax = plt.subplots(figsize=(10, 5))
                df_plot = df[["Ticker", "Current Ratio", "Quick Ratio", "Cash Ratio"]].set_index("Ticker")
                df_plot = df_plot.apply(pd.to_numeric, errors='coerce')
                df_plot.plot(kind="bar", ax=ax, rot=45)
                ax.axhline(1, color="green", linestyle="--")
                ax.set_title("Ratios de Liquidez")
                ax.set_ylabel("Ratio")
                st.pyplot(fig)
                plt.close()
            
            # Sección 5: Crecimiento
            st.header("🚀 Crecimiento Histórico")
            
            growth_metrics = ["Revenue Growth", "EPS Growth", "FCF Growth"]
            df_growth = df[["Ticker"] + growth_metrics].set_index("Ticker")
            df_growth = df_growth * 100  # Convertir a porcentaje
            
            fig, ax = plt.subplots(figsize=(12, 6))
            df_growth.plot(kind="bar", ax=ax, rot=45)
            ax.axhline(0, color="black", linewidth=0.8)
            ax.set_title("Tasas de Crecimiento Anual (%)")
            ax.set_ylabel("Crecimiento %")
            st.pyplot(fig)
            plt.close()
            
            # Sección 6: Análisis Individual
            st.header("🔍 Análisis por Empresa")
            
            selected_ticker = st.selectbox("Selecciona una empresa", df["Ticker"].unique())
            empresa = df[df["Ticker"] == selected_ticker].iloc[0]
            
            st.subheader(f"Análisis Detallado: {empresa['Nombre']}")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Precio", f"${empresa['Precio']:,.2f}" if empresa['Precio'] else "N/D")
                st.metric("P/E", empresa['P/E'])
                st.metric("P/B", empresa['P/B'])
                
            with col2:
                st.metric("ROE", empresa['ROE'])
                st.metric("ROIC", empresa['ROIC'])
                st.metric("WACC", empresa['WACC'])
                
            with col3:
                st.metric("Deuda/Patrimonio", empresa['Debt/Eq'])
                st.metric("Margen Neto", empresa['Profit Margin'])
                st.metric("Dividend Yield", empresa['Dividend Yield %'])
            
            # Gráfico de creación de valor individual
            st.subheader("Creación de Valor")
            fig, ax = plt.subplots(figsize=(6, 4))
            if empresa['ROIC'] != "N/D" and empresa['WACC'] != "N/D":
                roic_val = float(empresa['ROIC'].rstrip("%"))
                wacc_val = float(empresa['WACC'].rstrip("%"))
                color = "green" if roic_val > wacc_val else "red"
                
                ax.bar(["ROIC", "WACC"], [roic_val, wacc_val], color=[color, "gray"])
                ax.set_title("Creación de Valor (ROIC vs WACC)")
                ax.set_ylabel("%")
                st.pyplot(fig)
                plt.close()
                
                if roic_val > wacc_val:
                    st.success("✅ La empresa está creando valor (ROIC > WACC)")
                else:
                    st.error("❌ La empresa está destruyendo valor (ROIC < WACC)")
            else:
                st.warning("Datos insuficientes para análisis ROIC/WACC")

if __name__ == "__main__":
    main()
