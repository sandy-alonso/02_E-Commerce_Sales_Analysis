# Genera las gráficas del README a partir del dataset limpio
# Se ejecuta desde la carpeta py/: python generar_figuras.py

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

# colores: superficie, textos y series
SUPERFICIE = '#fcfcfb'
TEXTO = '#0b0b0b'
TEXTO_SEC = '#52514e'
GRID = '#e4e3df'
AZUL, NARANJA, AQUA = '#2a78d6', '#eb6834', '#1baf7a'

plt.rcParams.update({
    'figure.facecolor': SUPERFICIE,
    'axes.facecolor': SUPERFICIE,
    'axes.edgecolor': GRID,
    'axes.labelcolor': TEXTO_SEC,
    'axes.titlecolor': TEXTO,
    'axes.titlesize': 13,
    'axes.titleweight': 'bold',
    'axes.titlelocation': 'left',
    'xtick.color': TEXTO_SEC,
    'ytick.color': TEXTO_SEC,
    'font.size': 10.5,
    'axes.spines.top': False,
    'axes.spines.right': False,
})

# cargar dataset limpio
df = pd.read_csv('../data/clean/amazon_sales_clean.csv')
ventas = df[df['venta_valida']].copy()


def guardar(fig, nombre):
    fig.savefig(f'../figures/{nombre}', dpi=160, bbox_inches='tight')
    plt.close(fig)
    print('guardada:', nombre)


# 1. tasa de cancelación por fulfilment
tasa_fulfilment = (df.groupby('fulfilment')['cancelado'].mean() * 100).reindex(['Amazon', 'Merchant'])
fig, ax = plt.subplots(figsize=(6, 4.2))
barras = ax.bar(tasa_fulfilment.index, tasa_fulfilment.values, color=[AZUL, NARANJA], width=0.5,
                 edgecolor=SUPERFICIE, linewidth=2)
for barra, valor in zip(barras, tasa_fulfilment.values):
    ax.text(barra.get_x() + barra.get_width() / 2, valor + 0.4, f'{valor:.2f}%', ha='center', va='bottom', color=TEXTO)
ax.set_title('Tasa de cancelación por fulfilment')
ax.set_ylabel('Pedidos cancelados (%)')
ax.set_ylim(0, 22)
ax.yaxis.grid(True, color=GRID, linewidth=0.8)
ax.set_axisbelow(True)
guardar(fig, '01_cancelacion_por_fulfilment.png')

# 2. ticket promedio por categoría (ventas válidas, excluye Dupatta por tener solo 3 líneas)
ticket_categoria = (
    ventas.loc[ventas['category'] != 'Dupatta']
    .groupby('category')['amount'].mean()
    .sort_values(ascending=True)
)
fig, ax = plt.subplots(figsize=(8, 5))
barras = ax.barh(ticket_categoria.index, ticket_categoria.values, color=AZUL, height=0.6,
                  edgecolor=SUPERFICIE, linewidth=2)
for barra, valor in zip(barras, ticket_categoria.values):
    ax.text(valor + 10, barra.get_y() + barra.get_height() / 2, f'{valor:.0f}', va='center', color=TEXTO)
ax.set_xlim(0, ticket_categoria.max() * 1.18)
ax.set_xlabel('Ticket promedio (INR)')
ax.set_title('Ticket promedio por categoría de producto')
ax.xaxis.grid(True, color=GRID, linewidth=0.8)
ax.set_axisbelow(True)
guardar(fig, '02_ticket_por_categoria.png')

# 3. cancelación por nivel de servicio: total contra dentro de Amazon (paradoja de Simpson)
niveles = ['Expedited', 'Standard']
tasa_total = df.groupby('ship_service_level')['cancelado'].mean() * 100
amazon = df[df['fulfilment'] == 'Amazon']
tasa_amazon = amazon.groupby('ship_service_level')['cancelado'].mean() * 100

x = np.arange(len(niveles))
ancho = 0.32
fig, ax = plt.subplots(figsize=(7.5, 4.5))
barras_total = ax.bar(x - ancho / 2, [tasa_total[n] for n in niveles], width=ancho, color=NARANJA,
                       edgecolor=SUPERFICIE, linewidth=2, label='Total (sin estratificar)')
barras_amazon = ax.bar(x + ancho / 2, [tasa_amazon[n] for n in niveles], width=ancho, color=AZUL,
                        edgecolor=SUPERFICIE, linewidth=2, label='Dentro de Amazon')
for barra, n in zip(barras_total, niveles):
    ax.text(barra.get_x() + barra.get_width() / 2, tasa_total[n] + 0.4, f'{tasa_total[n]:.1f}%',
            ha='center', va='bottom', color=TEXTO)
for barra, n in zip(barras_amazon, niveles):
    ax.text(barra.get_x() + barra.get_width() / 2, tasa_amazon[n] + 0.4, f'{tasa_amazon[n]:.1f}%',
            ha='center', va='bottom', color=TEXTO)
ax.set_xticks(x, niveles)
ax.set_ylabel('Pedidos cancelados (%)')
ax.set_ylim(0, 22)
ax.set_title('Cancelación por nivel de servicio: total contra dentro de Amazon')
ax.yaxis.grid(True, color=GRID, linewidth=0.8)
ax.set_axisbelow(True)
leyenda = ax.legend(frameon=False, loc='upper left', labelcolor=TEXTO)
guardar(fig, '03_cancelacion_servicio_estratificado.png')

# 4. tamaño del efecto (d de Cohen) de las pruebas t de Welch principales sobre el ticket
def d_cohen(a, b):
    return (a.mean() - b.mean()) / np.sqrt((a.var(ddof=1) + b.var(ddof=1)) / 2)


def ic_d(a, b, d):
    # intervalo de confianza del 95% aproximado para d
    n1, n2 = len(a), len(b)
    ee = np.sqrt((n1 + n2) / (n1 * n2) + d ** 2 / (2 * (n1 + n2)))
    return d - 1.96 * ee, d + 1.96 * ee


amazon_ventas = ventas[ventas['fulfilment'] == 'Amazon']
comparaciones = [
    ('Ticket: Set contra Kurta',
     ventas.loc[ventas['category'] == 'Set', 'amount'], ventas.loc[ventas['category'] == 'Kurta', 'amount']),
    ('Ticket: con promoción contra sin (todas)',
     ventas.loc[ventas['tiene_promocion'], 'amount'], ventas.loc[~ventas['tiene_promocion'], 'amount']),
    ('Ticket: con promoción contra sin (Amazon)',
     amazon_ventas.loc[amazon_ventas['tiene_promocion'], 'amount'],
     amazon_ventas.loc[~amazon_ventas['tiene_promocion'], 'amount']),
    ('Ticket: B2B contra B2C',
     ventas.loc[ventas['b2b'], 'amount'], ventas.loc[~ventas['b2b'], 'amount']),
]

filas = []
for nombre, a, b in comparaciones:
    d = d_cohen(a, b)
    bajo, alto = ic_d(a, b, d)
    p = stats.ttest_ind(a, b, equal_var=False).pvalue
    filas.append((nombre, d, bajo, alto, p))

fig, ax = plt.subplots(figsize=(8, 4))
y = np.arange(len(filas))[::-1]
for yi, (nombre, d, bajo, alto, p) in zip(y, filas):
    ax.plot([bajo, alto], [yi, yi], color=AZUL, linewidth=2)
    ax.plot(d, yi, 'o', color=AZUL, markersize=8, markeredgecolor=SUPERFICIE, markeredgewidth=2)
    ax.text(alto + 0.04, yi, f'{d:.2f}', va='center', color=TEXTO)
for umbral, texto in [(0.2, 'pequeño'), (0.5, 'mediano'), (0.8, 'grande')]:
    ax.axvline(umbral, color=GRID, linewidth=1, linestyle='--', zorder=0)
    ax.text(umbral, len(filas) - 0.35, texto, ha='center', color=TEXTO_SEC, fontsize=9)
ax.set_yticks(y, [f[0] for f in filas])
ax.set_xlim(0, 2.0)
ax.set_ylim(-0.6, len(filas) - 0.1)
ax.set_xlabel('d de Cohen (prueba t de Welch, IC 95%)')
ax.set_title('Tamaño del efecto de las pruebas principales sobre el ticket')
guardar(fig, '04_tamano_efecto_pruebas.png')

# imprimir tablas de apoyo para el README
print(tasa_fulfilment.round(2))
print(ticket_categoria.round(2))
print(tasa_total.round(2))
print(tasa_amazon.round(2))
for f in filas:
    print(f[0], round(f[1], 3), 'p =', f'{f[4]:.2e}')
