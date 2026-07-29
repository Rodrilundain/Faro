"""Configuracion compartida de pytest: agrega la raiz del repo a sys.path
para poder importar los modulos del pipeline (calculo_riesgo, sanitacion,
procesamiento_emocional) desde tests/, sin instalar el proyecto como paquete.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
      sys.path.insert(0, str(ROOT_DIR))
  
