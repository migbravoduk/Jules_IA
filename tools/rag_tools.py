import os
import chromadb
from pathlib import Path
from config import BASE_DIRS
from tools.api_ai_tools import ask_gemini_api
from tools.word_tools import extraer_texto_word

def init_chroma():
    """Inicializa la colección de ChromaDB de forma persistente."""
    # Guardar en temp/chroma_db
    db_path = BASE_DIRS["temp"] / "chroma_db"
    db_path.mkdir(parents=True, exist_ok=True)
    
    # chromadb client
    client = chromadb.PersistentClient(path=str(db_path))
    collection = client.get_or_create_collection(
        name="jules_rag",
        metadata={"hnsw:space": "cosine"}
    )
    return collection

def extraer_texto_pdf(filepath: str) -> str:
    """Extrae texto de un PDF."""
    try:
        import pdfplumber
        texto = []
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    texto.append(t)
        return "\n".join(texto)
    except ImportError:
        return "Error: pdfplumber no instalado"
    except Exception as e:
        return f"Error leyendo PDF: {e}"

def indexar_documentos():
    """Lee todos los archivos de inputs/ y los indexa en ChromaDB."""
    collection = init_chroma()
    
    # Limpiar previos para no duplicar en demostración
    try:
        docs = collection.get()
        if docs and docs["ids"]:
            collection.delete(ids=docs["ids"])
    except:
        pass

    inputs_dir = BASE_DIRS["inputs"]
    archivos = list(inputs_dir.glob("*.*"))
    
    documentos = []
    metadatos = []
    ids = []
    
    for i, file_path in enumerate(archivos):
        ext = file_path.suffix.lower()
        texto = ""
        
        if ext == ".txt":
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    texto = f.read()
            except Exception as e:
                print(f"Error leyendo txt: {e}")
                
        elif ext == ".docx":
            texto = extraer_texto_word(str(file_path))
            if texto.startswith("Error"): texto = ""
            
        elif ext == ".pdf":
            texto = extraer_texto_pdf(str(file_path))
            if texto.startswith("Error"): texto = ""
            
        if texto.strip():
            # Dividir en chunks rudimentarios (por parrafos simples)
            chunks = [t for t in texto.split("\n\n") if len(t.strip()) > 50]
            for j, chunk in enumerate(chunks):
                documentos.append(chunk)
                metadatos.append({"origen": file_path.name, "chunk": j})
                ids.append(f"{file_path.name}_chunk_{j}")
                
    if documentos:
        collection.add(
            documents=documentos,
            metadatas=metadatos,
            ids=ids
        )
        return f"✅ Indexados {len(documentos)} fragmentos de {len(archivos)} archivos locales."
    else:
        return "⚠️ No se encontraron documentos con texto extraíble en inputs/."

def consultar_rag(pregunta: str) -> str:
    """Busca en ChromaDB y pregunta a Gemini usando ese contexto."""
    print("🔍 [RAG] Indexando documentos locales...")
    indexar_documentos()
    
    collection = init_chroma()
    
    print("🔍 [RAG] Buscando fragmentos relevantes...")
    resultados = collection.query(
        query_texts=[pregunta],
        n_results=5
    )
    
    if not resultados["documents"] or not resultados["documents"][0]:
        return "No encontré información relevante en tus documentos locales para responder esto."
        
    contextos = []
    for doc, meta in zip(resultados["documents"][0], resultados["metadatas"][0]):
        contextos.append(f"--- Documento: {meta['origen']} ---\n{doc}")
        
    contexto_str = "\n\n".join(contextos)
    
    prompt = (
        f"Eres un asistente experto. Responde a la pregunta basándote ÚNICAMENTE en el siguiente contexto.\n"
        f"Si la respuesta no está en el contexto, di que no tienes la información.\n"
        f"Menciona de qué documento (origen) sacaste la información usando los metadatos proporcionados.\n\n"
        f"CONTEXTO:\n{contexto_str}\n\n"
        f"PREGUNTA: {pregunta}"
    )
    
    print("🧠 [RAG] Generando respuesta con IA...")
    # Llamar directamente a la API de Gemini (requiere GEMINI_API_KEY)
    respuesta = ask_gemini_api(prompt)
    if respuesta.startswith("❌"):
        return "Error de API al consultar RAG: " + respuesta
        
    return respuesta
