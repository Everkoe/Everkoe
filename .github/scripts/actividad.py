"""Genera assets/actividad.svg con las contribuciones del último año.

Lee el calendario de contribuciones por GraphQL con GITHUB_TOKEN y dibuja
barras semanales con el mismo estilo de la cabecera del perfil.
"""
import json
import os
import sys
import urllib.request
from datetime import date

USUARIO = os.environ.get("USUARIO", "Everkoe")
SALIDA = os.environ.get("SALIDA", "assets/actividad.svg")
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]

CONSULTA = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""


def leer_calendario():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit("Falta GITHUB_TOKEN")
    cuerpo = json.dumps({"query": CONSULTA, "variables": {"login": USUARIO}}).encode()
    peticion = urllib.request.Request(
        "https://api.github.com/graphql",
        data=cuerpo,
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(peticion, timeout=30) as respuesta:
        datos = json.load(respuesta)
    if "errors" in datos:
        sys.exit(f"GraphQL: {datos['errors']}")
    return datos["data"]["user"]["contributionsCollection"]["contributionCalendar"]


def rachas(dias):
    mejor = actual = 0
    for d in dias:
        actual = actual + 1 if d["contributionCount"] > 0 else 0
        mejor = max(mejor, actual)
    # La racha actual no se corta si hoy todavía no hay contribuciones.
    vigente = 0
    for i, d in enumerate(reversed(dias)):
        if d["contributionCount"] > 0:
            vigente += 1
        elif i > 0:
            break
    return vigente, mejor


def svg(calendario):
    semanas = calendario["weeks"][-52:]
    totales = [sum(d["contributionCount"] for d in s["contributionDays"]) for s in semanas]
    dias = [d for s in calendario["weeks"] for d in s["contributionDays"]]
    vigente, mejor = rachas(dias)
    maximo = max(totales) or 1

    x0, ancho_util, base, alto_max = 330, 540, 150, 104
    paso = ancho_util / len(semanas)
    barras, etiquetas, mes_previo = [], [], None
    for i, (semana, total) in enumerate(zip(semanas, totales)):
        x = x0 + i * paso
        alto = max(3, round(total / maximo * alto_max)) if total else 3
        opacidad = 0.18 if not total else 0.45 + 0.55 * total / maximo
        barras.append(
            f'<rect x="{x:.1f}" y="{base - alto}" width="{paso - 3:.1f}" height="{alto}" rx="2" '
            f'fill="#4ADE80" fill-opacity="{opacidad:.2f}">'
            f'<animate attributeName="height" from="0" to="{alto}" dur=".8s" begin="{i * 0.015:.2f}s" fill="freeze"/>'
            f'<animate attributeName="y" from="{base}" to="{base - alto}" dur=".8s" begin="{i * 0.015:.2f}s" fill="freeze"/>'
            "</rect>"
        )
        mes = date.fromisoformat(semana["contributionDays"][0]["date"]).month
        if mes != mes_previo and i < len(semanas) - 2:
            etiquetas.append(
                f'<text x="{x:.1f}" y="172" font-size="10" fill="#86EFAC" fill-opacity=".6" class="mono">{MESES[mes - 1]}</text>'
            )
            mes_previo = mes

    total = calendario["totalContributions"]
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="900" height="200" viewBox="0 0 900 200" role="img" aria-label="{total} contribuciones en el último año">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#0B1120"/><stop offset=".45" stop-color="#0F2A20"/><stop offset="1" stop-color="#14532D"/>
    </linearGradient>
  </defs>
  <style>text{{font-family:-apple-system,'Segoe UI',Helvetica,Arial,sans-serif}}.mono{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}}</style>
  <rect width="900" height="200" rx="14" fill="url(#bg)"/>
  <text x="40" y="92" font-size="56" font-weight="700" fill="#F0FDF4">{total}</text>
  <text x="42" y="118" font-size="14" fill="#BBF7D0">contribuciones en el último año</text>
  <text x="42" y="152" font-size="12" fill="#86EFAC" class="mono">racha actual {vigente} d · mejor {mejor} d</text>
  <line x1="310" y1="46" x2="310" y2="160" stroke="#22C55E" stroke-opacity=".25"/>
  {''.join(barras)}
  {''.join(etiquetas)}
</svg>
"""


def main():
    contenido = svg(leer_calendario())
    os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
    with open(SALIDA, "w", encoding="utf-8") as archivo:
        archivo.write(contenido)


if __name__ == "__main__":
    main()
