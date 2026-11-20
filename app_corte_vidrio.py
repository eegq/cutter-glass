from datetime import datetime
import io
import os
import matplotlib.image as mpimg
import matplotlib.patches as patches
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from rectpack import GuillotineBssfSas, newPacker
import streamlit as st

# ==========================================
# 0. CONFIGURACIÓN DE EMPRESA Y RUTAS
# ==========================================
NOMBRE_EMPRESA = "ALUMTECNIC ESTRUCTURAS EN ALUMINIO VIDRIO Y ACERO S.A.S."
SUBTITULO_EMPRESA = "Corte y Producción — Control de Calidad"
RUTA_LOGO = "logo.png"
CARPETA_SALIDA_LOCAL = r"G:\Mi unidad\PYTHON PROJECTS\CUTTER\Generados"
UNIDAD = "cm"
MAX_PLANCHAS = 20

st.set_page_config(
    page_title="Optimizador de Corte de Vidrio",
    page_icon="🪟",
    layout="centered",
)


def construir_nombre_archivo(nombre_orden: str, correlativo: int = 1):
  numeracion = f"{correlativo:03d}"
  fecha_archivo = datetime.now().strftime("%Y-%m-%d")
  caracteres_invalidos = r'\/:*?"<>|'
  orden_limpia = "".join(
      c for c in nombre_orden if c not in caracteres_invalidos
  ).strip()
  if not orden_limpia:
    orden_limpia = "SIN_ORDEN"
  return f"{numeracion}_{fecha_archivo}_{orden_limpia}.pdf", numeracion


def guardar_en_carpeta_local_si_existe(nombre_orden: str, pdf_bytes: bytes):
  """Guarda en la unidad G: solo si la unidad/carpeta existe en el entorno actual."""
  unidad_g = os.path.splitdrive(CARPETA_SALIDA_LOCAL)[0] + "\\"
  if not os.path.exists(unidad_g):
    return None, None

  try:
    os.makedirs(CARPETA_SALIDA_LOCAL, exist_ok=True)
    archivos_pdf = [
        f
        for f in os.listdir(CARPETA_SALIDA_LOCAL)
        if f.lower().endswith(".pdf")
    ]
    correlativo = len(archivos_pdf) + 1
    nombre_archivo, numeracion = construir_nombre_archivo(
        nombre_orden, correlativo
    )
    ruta_final = os.path.join(CARPETA_SALIDA_LOCAL, nombre_archivo)
    with open(ruta_final, "wb") as f:
      f.write(pdf_bytes)
    return ruta_final, numeracion
  except Exception:
    return None, None


def generar_pdf_bytes(
    numeracion: str,
    nombre_orden: str,
    responsable: str,
    plancha_ancho: float,
    plancha_alto: float,
    espesor: str,
    margen: float,
    permitir_rotacion: bool,
    piezas_pedidas: list,
):
  fecha_hora_gen = datetime.now().strftime("%d/%m/%Y %H:%M")
  ancho_util = plancha_ancho - (2 * margen)
  alto_util = plancha_alto - (2 * margen)

  if ancho_util <= 0 or alto_util <= 0:
    return (
        None,
        0,
        0,
        "El margen de refilado es mayor o igual al tamaño de la plancha.",
    )

  packer = newPacker(pack_algo=GuillotineBssfSas, rotation=permitir_rotacion)

  for ancho, alto, cantidad, nombre in piezas_pedidas:
    for _ in range(cantidad):
      packer.add_rect(ancho, alto, rid=nombre)

  for _ in range(MAX_PLANCHAS):
    packer.add_bin(ancho_util, alto_util)

  packer.pack()

  planchas_usadas = [b for b in packer if len(b) > 0]
  total_piezas_pedidas = sum(p[2] for p in piezas_pedidas)
  total_piezas_acomodadas = sum(len(b) for b in planchas_usadas)

  if total_piezas_acomodadas == 0:
    return (
        None,
        0,
        total_piezas_pedidas,
        "Ninguna pieza cabe en la plancha especificada.",
    )

  colores = [
      "#d8f3dc",
      "#caf0f8",
      "#ade8f4",
      "#90e0ef",
      "#bee9e8",
      "#b7e4c7",
      "#e2ece9",
      "#cddafd",
  ]
  peso_por_m2 = float(espesor) * 2.5

  logo_img = None
  if os.path.exists(RUTA_LOGO):
    try:
      logo_img = mpimg.imread(RUTA_LOGO)
    except Exception:
      logo_img = None

  buffer_pdf = io.BytesIO()

  with PdfPages(buffer_pdf) as pdf:
    for num_plancha, plancha in enumerate(planchas_usadas, start=1):
      fig = plt.figure(figsize=(11.69, 8.27), dpi=300)

      marco_hoja = patches.Rectangle(
          (0.025, 0.03),
          0.95,
          0.94,
          transform=fig.transFigure,
          fill=False,
          edgecolor="#ced4da",
          lw=1.2,
      )
      fig.patches.append(marco_hoja)

      ax_logo = fig.add_axes([0.04, 0.85, 0.14, 0.10])
      ax_logo.axis("off")
      if logo_img is not None:
        ax_logo.imshow(logo_img)
      else:
        ax_logo.text(
            0.5,
            0.5,
            "LOGO\nEMPRESA",
            ha="center",
            va="center",
            fontsize=8.5,
            fontweight="bold",
            color="#6c757d",
            bbox=dict(
                boxstyle="round,pad=0.6",
                facecolor="#f8f9fa",
                edgecolor="#adb5bd",
                linestyle="--",
            ),
        )

      ax_empresa = fig.add_axes([0.19, 0.85, 0.48, 0.10])
      ax_empresa.axis("off")
      ax_empresa.text(
          0.5,
          0.74,
          NOMBRE_EMPRESA,
          ha="center",
          va="center",
          fontsize=12.5,
          fontweight="bold",
          color="#023047",
      )
      ax_empresa.text(
          0.5,
          0.46,
          SUBTITULO_EMPRESA,
          ha="center",
          va="center",
          fontsize=8.8,
          color="#495057",
      )
      ax_empresa.text(
          0.5,
          0.16,
          f"PLANO DE CORTE VIDRIO {espesor} mm — PLANCHA #{num_plancha} DE"
          f" {len(planchas_usadas)}",
          ha="center",
          va="center",
          fontsize=9.5,
          fontweight="bold",
          color="#0077b6",
      )

      ax_control = fig.add_axes([0.68, 0.85, 0.28, 0.10])
      ax_control.axis("off")
      texto_control = (
          f"REGISTRO N.° : {numeracion}\n"
          f"ORDEN        : {nombre_orden}\n"
          f"FECHA        : {fecha_hora_gen}\n"
          f"RESPONSABLE  : {responsable}"
      )
      ax_control.text(
          0.0,
          0.5,
          texto_control,
          ha="left",
          va="center",
          fontsize=8.0,
          family="monospace",
          bbox=dict(
              boxstyle="round,pad=0.5",
              facecolor="#f1f8fc",
              edgecolor="#0077b6",
              lw=1.1,
          ),
      )

      linea_sup = plt.Line2D(
          [0.04, 0.96],
          [0.835, 0.835],
          transform=fig.transFigure,
          color="#0077b6",
          lw=1.2,
      )
      fig.lines.append(linea_sup)

      ax_plano = fig.add_axes([0.08, 0.24, 0.84, 0.55])
      margen_x = plancha_ancho * 0.04
      margen_y = plancha_alto * 0.08
      ax_plano.set_xlim(-margen_x, plancha_ancho + margen_x * 1.6)
      ax_plano.set_ylim(-margen_y * 0.6, plancha_alto + margen_y * 1.4)
      ax_plano.set_aspect("equal", adjustable="box")
      ax_plano.set_anchor("C")
      ax_plano.axis("off")

      ax_plano.add_patch(
          patches.Rectangle(
              (plancha_ancho * 0.008, -plancha_alto * 0.012),
              plancha_ancho,
              plancha_alto,
              facecolor="#dee2e6",
              edgecolor="none",
          )
      )

      ax_plano.add_patch(
          patches.Rectangle(
              (0, 0),
              plancha_ancho,
              plancha_alto,
              facecolor="#f8f9fa",
              edgecolor="#212529",
              lw=1.8,
          )
      )

      y_cota = plancha_alto + (plancha_alto * 0.045)
      ax_plano.annotate(
          "",
          xy=(0, y_cota),
          xytext=(plancha_ancho, y_cota),
          arrowprops=dict(arrowstyle="<->", color="#495057", lw=1.1),
      )
      ax_plano.text(
          plancha_ancho / 2,
          y_cota + (plancha_alto * 0.015),
          f"LARGO TOTAL: {plancha_ancho:g} {UNIDAD}",
          ha="center",
          va="bottom",
          fontsize=8.5,
          fontweight="bold",
          color="#212529",
      )

      x_cota = plancha_ancho + (plancha_ancho * 0.025)
      ax_plano.annotate(
          "",
          xy=(x_cota, 0),
          xytext=(x_cota, plancha_alto),
          arrowprops=dict(arrowstyle="<->", color="#495057", lw=1.1),
      )
      ax_plano.text(
          x_cota + (plancha_ancho * 0.012),
          plancha_alto / 2,
          f"ANCHO: {plancha_alto:g} {UNIDAD}",
          ha="left",
          va="center",
          rotation=90,
          fontsize=8.5,
          fontweight="bold",
          color="#212529",
      )

      if margen > 0:
        ax_plano.add_patch(
            patches.Rectangle(
                (margen, margen),
                ancho_util,
                alto_util,
                fill=False,
                edgecolor="#d90429",
                linestyle="--",
                lw=1,
            )
        )

      area_utilizada_cm2 = 0

      for idx, rect in enumerate(plancha):
        pos_x = rect.x + margen
        pos_y = rect.y + margen
        w_real = rect.width
        h_real = rect.height
        area_utilizada_cm2 += w_real * h_real

        color = colores[idx % len(colores)]
        ax_plano.add_patch(
            patches.Rectangle(
                (pos_x, pos_y),
                w_real,
                h_real,
                facecolor=color,
                edgecolor="#023047",
                lw=1.3,
                alpha=0.92,
            )
        )

        ratio_w = w_real / plancha_ancho
        ratio_h = h_real / plancha_alto
        factor_min = min(ratio_w * 1.4, ratio_h * 1.8)

        if factor_min < 0.16:
          tam_fuente = 5.8
        elif factor_min < 0.25:
          tam_fuente = 7.0
        elif factor_min < 0.35:
          tam_fuente = 8.2
        else:
          tam_fuente = 9.2

        ax_plano.text(
            pos_x + w_real / 2,
            pos_y + h_real / 2,
            f"{rect.rid}\n{w_real:g} x {h_real:g} {UNIDAD}",
            ha="center",
            va="center",
            fontsize=tam_fuente,
            fontweight="bold",
            color="#03045e",
        )

      ax_info = fig.add_axes([0.04, 0.05, 0.92, 0.16])
      ax_info.axis("off")

      area_total_cm2 = plancha_ancho * plancha_alto
      area_total_m2 = area_total_cm2 / 10_000
      area_util_m2 = area_utilizada_cm2 / 10_000
      aprovechamiento = (area_utilizada_cm2 / area_total_cm2) * 100
      desperdicio = 100 - aprovechamiento
      peso_cortes_kg = area_util_m2 * peso_por_m2

      resumen_texto = (
          f"FICHA TÉCNICA DE PRODUCCIÓN — ORDEN: {nombre_orden} | ESPESOR:"
          f" {espesor} mm (PLANCHA #{num_plancha} DE {len(planchas_usadas)})\n"
          "──────────────────────────────────────────────────────────────────────────────────────────────────────────────────\n"
          f"• Plancha Base     : {plancha_ancho:g} x {plancha_alto:g} {UNIDAD}"
          f" ({area_total_m2:.2f} m²)    |   Margen Refilado : {margen:g}"
          f" {UNIDAD}\n"
          f"• Paños Cortados   : {len(plancha)} en esta hoja (Total orden:"
          f" {total_piezas_acomodadas}/{total_piezas_pedidas} paños)    |  "
          f" Peso Neto Vidrio: {peso_cortes_kg:.1f} kg\n"
          f"• Aprovechamiento  : {aprovechamiento:.1f}% ({area_util_m2:.2f} m²)"
          f"         |   Sobrante / Retal: {desperdicio:.1f}%"
      )

      ax_info.text(
          0.5,
          0.5,
          resumen_texto,
          ha="center",
          va="center",
          fontsize=8.8,
          family="monospace",
          bbox=dict(
              boxstyle="round,pad=0.7",
              facecolor="#f8fdff",
              edgecolor="#90e0ef",
              lw=1.2,
          ),
      )

      pdf.savefig(fig)
      plt.close(fig)

  buffer_pdf.seek(0)
  return (
      buffer_pdf.getvalue(),
      total_piezas_acomodadas,
      total_piezas_pedidas,
      None,
  )


# ==========================================
# INTERFAZ WEB / MÓVIL (STREAMLIT)
# ==========================================
st.title("🪟 Corte de Vidrio (cm)")
st.caption("Generador de planos A4 para taller — Web / Móvil")

with st.form("form_corte"):
  col1, col2 = st.columns(2)
  with col1:
    nombre_orden = st.text_input(
        "Nombre / N.° de Orden", placeholder="Ej. OT-045"
    )
  with col2:
    responsable = st.text_input(
        "Responsable", placeholder="Ej. Carlos Pérez"
    )

  col3, col4, col5 = st.columns(3)
  with col3:
    plancha_ancho = st.number_input(
        "Largo plancha (cm)", min_value=1.0, value=345.0, step=1.0
    )
  with col4:
    plancha_alto = st.number_input(
        "Ancho plancha (cm)", min_value=1.0, value=230.0, step=1.0
    )
  with col5:
    espesor = st.selectbox("Espesor (mm)", options=["4", "6", "8"], index=1)

  col6, col7 = st.columns(2)
  with col6:
    margen = st.number_input(
        "Margen refilado (cm)", min_value=0.0, value=0.0, step=0.5
    )
  with col7:
    permitir_rotacion = st.checkbox("Permitir rotar 90°", value=True)

  st.markdown("**Cortes solicitados (uno por línea)**")
  st.caption("Formato: `ANCHOxALTOxCANTIDAD Nombre` — Ej: `55x84x4 Ventana`")
  cortes_texto = st.text_area(
      "Lista de piezas",
      value="55x84x4 Paño A\n45x83x4 Paño B",
      height=120,
      label_visibility="collapsed",
  )

  enviar = st.form_submit_button("Generar Plano A4 PDF", use_container_width=True)

if enviar:
  piezas = []
  errores_linea = []

  for idx, linea in enumerate(cortes_texto.splitlines(), start=1):
    linea_limpia = linea.strip()
    if not linea_limpia:
      continue
    try:
      bloques = linea_limpia.split(maxsplit=1)
      medidas = bloques[0].lower().replace(" ", "").split("x")
      nombre = bloques[1].strip() if len(bloques) > 1 else f"Paño {idx}"
      if len(medidas) != 3:
        raise ValueError
      w = float(medidas[0])
      h = float(medidas[1])
      cant = int(medidas[2])
      if w <= 0 or h <= 0 or cant <= 0:
        raise ValueError
      piezas.append((w, h, cant, nombre))
    except ValueError:
      errores_linea.append(f"Línea {idx}: '{linea_limpia}'")

  if errores_linea:
    st.error(
        "Revisa el formato de estas líneas:\n" + "\n".join(errores_linea)
    )
  elif not piezas:
    st.warning("Ingresa al menos un corte antes de generar el PDF.")
  else:
    orden_final = nombre_orden.strip() or "SIN_ORDEN"
    resp_final = responsable.strip() or "No especificado"

    # Primero generamos el PDF con correlativo base; si existe carpeta local, se calcula allí
    pdf_bytes_temp, _, _, _ = generar_pdf_bytes(
        numeracion="001",
        nombre_orden=orden_final,
        responsable=resp_final,
        plancha_ancho=plancha_ancho,
        plancha_alto=plancha_alto,
        espesor=espesor,
        margen=margen,
        permitir_rotacion=permitir_rotacion,
        piezas_pedidas=piezas,
    )

    ruta_local, numeracion_real = (
        guardar_en_carpeta_local_si_existe(orden_final, pdf_bytes_temp)
        if pdf_bytes_temp
        else (None, "001")
    )

    pdf_bytes, acomodadas, pedidas, error_msg = generar_pdf_bytes(
        numeracion=numeracion_real or "001",
        nombre_orden=orden_final,
        responsable=resp_final,
        plancha_ancho=plancha_ancho,
        plancha_alto=plancha_alto,
        espesor=espesor,
        margen=margen,
        permitir_rotacion=permitir_rotacion,
        piezas_pedidas=piezas,
    )

    if error_msg:
      st.error(error_msg)
    else:
      if ruta_local and pdf_bytes:
        try:
          with open(ruta_local, "wb") as f:
            f.write(pdf_bytes)
          st.success(f"Guardado en carpeta local:\n`{ruta_local}`")
        except Exception:
          pass

      nombre_descarga, _ = construir_nombre_archivo(
          orden_final, int(numeracion_real or "1")
      )

      if acomodadas < pedidas:
        st.warning(
            f"Se acomodaron {acomodadas} de {pedidas} piezas solicitadas."
        )

      st.download_button(
          label="⬇️ Descargar PDF en este dispositivo",
          data=pdf_bytes,
          file_name=nombre_descarga,
          mime="application/pdf",
          use_container_width=True,
      )
