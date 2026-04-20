Autor: **Hugo Vargas**
Contacto: **hu.ce.va.ba@gmail.com** | www.linkedin.com/in/hucevaba
Github: **hucevaba1**

# Explorador de participación electoral

[Ver aplicación en Streamlit](https://exploradorparticipacion-hb.streamlit.app/)

Aplicación interactiva desarrollada con **Streamlit** para explorar la participación electoral en México a nivel nacional, estatal y municipal, así como para visualizar estimaciones municipales de participación para 2027.

## Sobre el proyecto

Este proyecto forma parte de mi portafolio como analista de datos. Su objetivo es transformar datos públicos electorales en visualizaciones interactivas que permitan analizar patrones de participación y abstención en México de manera clara, accesible y útil para la exploración.

La aplicación permite:

- explorar la participación electoral a nivel **nacional**, **estatal** y **municipal**
- consultar **tablas**, **gráficas** y **mapas interactivos**
- comparar trayectorias de participación a lo largo del tiempo
- analizar la participación según **sexo**, **edad** y **tipo de sección**
- visualizar una **estimación municipal de participación para 2027** mediante modelos predictivos

## Fuente de datos

Los datos utilizados provienen de los **Conteos Censales de Participación Ciudadana 2009–2024** del **Instituto Nacional Electoral (INE)**.

## Funcionalidades principales

### Explorador
La sección **Explorador** permite consultar información para:

- **País**
  - métricas nacionales de participación y abstención
  - resumen por estado
  - gráfica de participación por entidad federativa
  - mapa nacional por estado
  - series de tiempo por estado
  - evolución de la participación según categorías

- **Estados**
  - métricas estatales de participación y abstención
  - resumen por municipio
  - gráfica de participación por municipio
  - mapa municipal del estado
  - series de tiempo municipales
  - evolución de la participación según categorías dentro del estado

### Modelo predictivo
La sección **Modelo predictivo** permite:

- seleccionar una entidad federativa
- visualizar un mapa municipal con la **participación estimada para 2027**
- consultar intervalos de predicción aproximados
- revisar la comparación entre modelos
- explorar coeficientes y diagnósticos visuales para cada método de predicción

## Tecnologías utilizadas

- Python
- Streamlit
- pandas
- GeoPandas
- Plotly
- Altair
- scikit-learn
- PyArrow

## Ejecución local

```bash
git clone https://github.com/hucevaba1/explorador_participacion.git
cd explorador_participacion
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m streamlit run streamlit_app.py
```

## Notas
- La aplicación consume artefactos **.parquet** previamente procesados para mejorar tiempos de carga.
- Las geometrías fueron simplificadas para optimizar el render de mapas en producción.
- Algunos municipios pueden aparecer **sin estimación en el modelo predictivo** cuando no existe suficiente información **histórica** comparable para generar el pronóstico.
