import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

class MetadataEngine:
    """
    Clase para interactuar con la API de Google Gemini y generar metadatos.
    """
    def __init__(self):
        """
        Inicializa el motor de metadatos, cargando la API Key y configurando el modelo.
        """
        load_dotenv()
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY no encontrada en el archivo .env")

        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        self.system_prompt = "Eres un bibliotecario experto. Analiza el texto proporcionado. Devuelve SOLAMENTE un objeto JSON con dos claves: 'summary' (un resumen de una sola oración potente en español) y 'tags' (una lista de 3 a 5 etiquetas temáticas/taxonómicas en kebab-case, no palabras genéricas)."

    def get_metadata(self, text: str) -> dict:
        """
        Genera metadatos (resumen y tags) para un texto dado usando la IA.

        Args:
            text: El contenido de la nota atómica.

        Returns:
            Un diccionario con 'summary' y 'tags'. En caso de error, devuelve valores vacíos.
        """
        default_response = {'summary': '', 'tags': []}

        try:
            full_prompt = f"{self.system_prompt}\n\nTexto a analizar:\n{text}"
            response = self.model.generate_content(full_prompt)

            # Limpiar la respuesta para extraer solo el JSON
            cleaned_response = response.text.strip().replace("```json", "").replace("```", "").strip()

            metadata = json.loads(cleaned_response)

            # Validar que las claves esperadas están presentes
            if 'summary' not in metadata or 'tags' not in metadata:
                print(f"Warning: AI response is missing required keys. Response: {metadata}")
                return default_response

            return metadata

        except Exception as e:
            print(f"Warning: Fallo al generar metadatos con la IA. Error: {e}")
            return default_response

if __name__ == '__main__':
    # Ejemplo de uso (para pruebas)
    engine = MetadataEngine()
    sample_text = "El principio de responsabilidad única (SRP) establece que una clase debe tener una, y solo una, razón para cambiar. Esto significa que una clase solo debe tener un trabajo o responsabilidad. Cuando una clase tiene más de una responsabilidad, estas responsabilidades se acoplan. Los cambios en una responsabilidad pueden llevar a cambios en la otra."

    metadata = engine.get_metadata(sample_text)
    print(f"Metadatos generados: {metadata}")

    # Prueba de fallo
    invalid_text = ""
    metadata_fail = engine.get_metadata(invalid_text)
    print(f"Prueba de fallo: {metadata_fail}")
