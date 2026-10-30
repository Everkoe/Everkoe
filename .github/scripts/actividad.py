"""Genera assets/actividad.svg con las contribuciones del último año.

Lee el calendario de contribuciones por GraphQL con GITHUB_TOKEN y dibuja
barras semanales con el mismo estilo de las tarjetas de proyectos.
"""
import json
import os
import sys
import urllib.request
from datetime import date

USUARIO = os.environ.get("USUARIO", "Everkoe")
SALIDA = os.environ.get("SALIDA", "assets/actividad-semanas.svg")
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

    x0, ancho_util, base, alto_max = 316, 548, 128, 88
    paso = ancho_util / len(semanas)
    barras, etiquetas, mes_previo = [], [], None
    for i, (semana, total) in enumerate(zip(semanas, totales)):
        x = x0 + i * paso
        alto = max(4, round(total / maximo * alto_max)) if total else 4
        clase = "b" if total else "v"
        opacidad = 1 if not total else 0.35 + 0.65 * total / maximo
        barras.append(
            f'<rect class="{clase}" x="{x:.1f}" y="{base - alto}" width="{paso - 3.5:.1f}" height="{alto}" rx="3" '
            f'fill-opacity="{opacidad:.2f}">'
            f'<animate attributeName="height" from="0" to="{alto}" dur=".7s" begin="{i * 0.012:.2f}s" fill="freeze"/>'
            f'<animate attributeName="y" from="{base}" to="{base - alto}" dur=".7s" begin="{i * 0.012:.2f}s" fill="freeze"/>'
            "</rect>"
        )
        mes = date.fromisoformat(semana["contributionDays"][0]["date"]).month
        if mes != mes_previo and i < len(semanas) - 2:
            etiquetas.append(f'<text class="d" x="{x:.1f}" y="150" font-size="11">{MESES[mes - 1]}</text>')
            mes_previo = mes

    total = calendario["totalContributions"]
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="900" height="172" viewBox="0 0 900 172" role="img" aria-label="{total} contribuciones en el último año">
  <style>
    text{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif}}
    .bg{{fill:#ECFDF3}}.n{{fill:#14532D}}.d{{fill:#59636E}}.st{{fill:#166534}}.p{{fill:#DCFCE7}}.b{{fill:#16A34A}}.v{{fill:#16A34A;fill-opacity:.12}}.l{{stroke:#16A34A;stroke-opacity:.18}}
    @media (prefers-color-scheme:dark){{.bg{{fill:#0F2A1C}}.n{{fill:#F0FDF4}}.d{{fill:#9198A1}}.st{{fill:#BBF7D0}}.p{{fill:#14532D}}.b{{fill:#4ADE80}}.v{{fill:#4ADE80;fill-opacity:.12}}.l{{stroke:#4ADE80;stroke-opacity:.2}}}}
  </style>
  <rect class="bg" width="900" height="172" rx="18"/>
  <text class="n" x="36" y="82" font-size="52" font-weight="600" letter-spacing="-1">{total}</text>
  <text class="d" x="38" y="108" font-size="14">contribuciones en el último año</text>
  <rect class="p" x="36" y="122" width="112" height="26" rx="13"/>
  <text class="st" x="92" y="139.5" font-size="12.5" font-weight="500" text-anchor="middle">racha {vigente} días</text>
  <rect class="p" x="156" y="122" width="112" height="26" rx="13"/>
  <text class="st" x="212" y="139.5" font-size="12.5" font-weight="500" text-anchor="middle">mejor {mejor} días</text>
  <line class="l" x1="{x0}" y1="{base + 0.5}" x2="{x0 + ancho_util - 3.5}" y2="{base + 0.5}"/>
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
