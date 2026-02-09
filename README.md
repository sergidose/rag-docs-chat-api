# 🤖 rag-docs-chat-api

API de preguntas y respuestas sobre documentación utilizando un enfoque **RAG extractivo sin LLM**, basada en FastAPI y recuperación de información con TF-IDF.

El sistema permite indexar documentos en texto plano o Markdown y responder preguntas devolviendo fragmentos relevantes como respuesta.

---

## 🚀 Características

- API REST desarrollada con **FastAPI**
- Recuperación de información mediante **TF-IDF**
- Soporte para documentos `.md` y `.txt`
- Endpoint para ingesta dinámica de documentos
- Respuestas extractivas (sin modelos generativos)
- Dockerizado y listo para despliegue
- Tests automatizados con **pytest**
- Calidad de código con **ruff** y **pre-commit**

---

## 🧩 Arquitectura

Flujo general de la aplicación:

1. Se cargan documentos desde `data/raw`
2. Se dividen en fragmentos (chunks)
3. Se construye un índice TF-IDF
4. Las consultas se comparan contra ese índice
5. Se devuelve el fragmento más relevante como respuesta

Este proyecto implementa un RAG **ligero y determinista**, ideal para:

- FAQs
- Documentación interna
- Sistemas de ayuda
- Bases de conocimiento pequeñas o medianas

---

## 📁 Estructura del proyecto

rag-docs-chat-api/
├── app/
│ └── main.py # Punto de entrada de FastAPI
├── src/
│ ├── init.py
│ ├── chunking.py # División de textos en fragmentos
│ ├── config.py # Configuración general
│ ├── docs.py # Carga de documentos
│ ├── index.py # Construcción y guardado del índice
│ ├── markdown.py # Utilidades para procesar Markdown
│ ├── rag.py # Lógica principal de preguntas
│ └── retriever.py # Implementación TF-IDF
├── data/
│ └── raw/ # Documentos a indexar
├── models/
│ └── rag_index.joblib # Índice generado (tras ingest)
├── scripts/
│ └── start_api.py # Script de arranque
├── tests/ # Tests automatizados
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
└── README.md

---

## 🔧 Instalación y ejecución

### Requisitos

- Python 3.10 o superior
- Docker (opcional)

---

### ▶ Ejecución local

Clonar el proyecto y crear entorno:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

---

### Instalar el proyecto en modo editable (recomendado):

```powershell
pip install -e .
```

---

### Iniciar la API

```powershell
uvicorn app.main:app --reload
```

La documentación Swagger estará disponible en:

👉 http://localhost:8000/docs


---

## 🐳 Ejecución con Docker

```bash
docker compose up --build
```

La API quedará accesible en:

👉 http://localhost:8000/docs

---

## 📥 Ingestar documentos

Antes de poder hacer preguntas es necesario indexar los documentos.

Endpoint
POST /ingest

Ejemplo con curl:

``` bash
curl -X POST http://localhost:8000/ingest
```

Esto realiza:

- Lectura de los archivos en data/raw

- Creación del índice TF-IDF

- Guardado del índice en models/

---

## ❓ Realizar preguntas

Endpoint
POST /chat

Ejemplo de petición:

```json
{
  "question": "¿Qué planes tenéis?"
}
```

Ejemplo de respuesta:

```json
{
  "answer": "Plan Basic, Pro y Enterprise.",
  "sources": [
    {
      "source": "faq.md",
      "chunk_id": 1,
      "score": 0.33,
      "snippet": "Planes Plan Basic, Pro y Enterprise."
    }
  ]
}
```

## 🧪 Ejecución de tests

Para ejecutar los tests:

```powershell
pytest -q
```

Con cobretura:

```powershell
pytest --cov=src
```

---

## 🛠 Calidad de código

Este proyecto utiliza:

- ruff para linting y formateo

- pre-commit para validaciones automáticas

Instalar hooks:

```bash
pre-commit install
```

Verificar calidad manualmente:

```bash
ruff check .
```

---

## 📌 Limitaciones actuales

- No utiliza modelos de lenguaje (LLM)

- Respuestas estrictamente extractivas

- No hay embeddings semánticos

- El contexto se limita a los textos indexados

---

## 🚧 Posibles mejoras futuras

- Incorporar búsqueda con embeddings

- Re-ranking de resultados

- Soporte para PDFs

- Respuestas generativas con un LLM

- Interfaz web sencilla
