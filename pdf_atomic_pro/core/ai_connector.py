import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

class MetadataEngine:
    """
    Clase para interactuar con la API de Google Gemini y generar metadatos.
    Carga dinámicamente las reglas de taxonomía desde un archivo externo.
    """
    def __init__(self, rules_path="config/taxonomy_rules.txt"):
        """
        Inicializa el motor de metadatos, cargando la API Key,
        configurando el modelo y cargando las reglas de taxonomía.
        """
        load_dotenv()
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY no encontrada en el archivo .env")

        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-pro')

        self.system_prompt_base = "Eres un bibliotecario experto encargado de catalogar conocimiento en un Obsidian Vault. Tu tarea es analizar el texto y asignar etiquetas (tags) y un resumen."
        self.output_format_instruction = "OUTPUT FORMAT: Debes responder SOLAMENTE con un objeto JSON válido con las claves 'summary' y 'tags'. Sin markdown ni texto adicional."

        self._load_taxonomy_rules(rules_path)

    def _load_taxonomy_rules(self, rules_path):
        """Carga las reglas de taxonomía desde el archivo de configuración."""
        try:
            with open(rules_path, 'r', encoding='utf-8') as f:
                self.taxonomy_rules = f.read()
        except FileNotFoundError:
            print(f"[ERROR] No se encontró el archivo de reglas de taxonomía en: {rules_path}")
            self.taxonomy_rules = "No se pudieron cargar las reglas de taxonomía."
        except Exception as e:
            print(f"[ERROR] Falló al leer el archivo de reglas: {e}")
            self.taxonomy_rules = "Error al cargar reglas."

    def get_metadata(self, text: str) -> dict:
        """
        Genera metadatos (resumen y tags) para un texto dado usando la IA.

        Args:
            text: El contenido de la nota atómica.

        Returns:
            Un diccionario con 'summary' y 'tags'. En caso de error, devuelve valores vacíos.
        """
        default_response = {'summary': '', 'tags': []}

        # Construcción del prompt dinámico
        full_prompt = (
            f"{self.system_prompt_base}\n\n"
            f"CONTEXTO Y REGLAS:\n{self.taxonomy_rules}\n\n"
            f"Texto a analizar:\n{text}\n\n"
            f"{self.output_format_instruction}"
        )

        try:
            response = self.model.generate_content(full_prompt)

            cleaned_response = response.text.strip().replace("```json", "").replace("```", "").strip()

            metadata = json.loads(cleaned_response)

            if 'summary' not in metadata or 'tags' not in metadata:
                print(f"Warning: AI response is missing required keys. Response: {metadata}")
                return default_response

            return metadata

        except Exception as e:
            print(f"Warning: Fallo al generar metadatos con la IA. Error: {e}")
            return default_response

if __name__ == '__main__':
    engine = MetadataEngine()
    print("--- Reglas de Taxonomía Cargadas ---")
    print(engine.taxonomy_rules)
    print("------------------------------------")

    sample_text = "El libro explora las técnicas fundamentales de la cocina francesa, centrándose en la preparación de salsas madre como la bechamel y la velouté. Se detallan los ingredientes y los pasos precisos para lograr la consistencia ideal."

    metadata = engine.get_metadata(sample_text)
    print(f"\nMetadatos generados para libro de cocina: {metadata}")
