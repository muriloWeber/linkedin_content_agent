from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os
import sqlite3
import datetime
import smtplib
from email.mime.text import MIMEText
from agno.agent import Agent
from agno.storage.sqlite import SqliteStorage
from agno.models.google import Gemini
from agno.team.team import Team
from agno.tools import tool
from rich.pretty import pprint
from textwrap import dedent
import json
import time

# Carrega as variáveis de ambiente
load_dotenv(dotenv_path="../config/.env")

# Inicializa o FastAPI
app = FastAPI(
    title="Agente de Conteúdo para LinkedIn",
    description="API para gerar posts de LinkedIn sobre Ciência de Dados, CRM e IA, com testes via Swagger UI e aprovação por e-mail.",
    version="0.9.5"
)

# Verifica a chave da API do Google e configurações de SMTP
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = os.getenv("SMTP_PORT")
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

# Valida as variáveis de ambiente
if not GOOGLE_API_KEY:
    raise ValueError("A variável de ambiente GOOGLE_API_KEY não está configurada. Por favor, adicione-a em config/.env")
if not all([SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASSWORD]):
    raise ValueError("Uma ou mais variáveis de ambiente SMTP (SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASSWORD) não estão configuradas. Por favor, adicione-as em config/.env")

# Converte SMTP_PORT para inteiro
try:
    SMTP_PORT = int(SMTP_PORT)
except ValueError:
    raise ValueError("SMTP_PORT deve ser um número inteiro válido. Verifique o arquivo config/.env")

# --- Modelos Pydantic ---
class GeneratePostRequest(BaseModel):
    topic: str = "Um tópico relevante sobre Ciência de Dados, CRM ou IA."
    tone: str = "profissional e direto"
    length: int = 1000  # Caracteres
    call_to_action: str = "O que você acha? Compartilhe sua opinião!"
    session_id: str = "default_session"  # Para persistência de sessões

class PostResponse(BaseModel):
    id: int
    title: str
    content: str
    hashtags: list[str]
    status: str = "pending"
    rejection_reason: str | None = None
    created_at: str

class MetricsResponse(BaseModel):
    posts_per_week: dict
    popular_topics: list
    status: str = "success"

# --- Inicializa o banco de tópicos e posts ---
def init_db(db_file="tmp/linkedin.db"):
    """
    Cria as tabelas de tópicos e posts, populando com 50 tópicos iniciais.
    """
    os.makedirs("tmp", exist_ok=True)
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            usage_count INTEGER DEFAULT 0,
            last_used TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            title TEXT,
            content TEXT,
            hashtags TEXT,
            status TEXT DEFAULT 'pending',
            rejection_reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("SELECT COUNT(*) FROM topics")
    count = cursor.fetchone()[0]
    
    if count < 50:
        topics = get_trending_topics.entrypoint(agent=None, area_of_interest="Ciência de Dados, CRM ou IA")
        topic_list = topics.strip().split('\n') * 10
        topic_list = topic_list[:50]
        for topic in topic_list:
            cursor.execute("INSERT INTO topics (topic, usage_count) VALUES (?, 0)", (topic,))
    
    conn.commit()
    conn.close()

# --- Evento de inicialização do FastAPI ---
@app.on_event("startup")
async def startup_event():
    print("Iniciando banco de dados...")
    init_db()
    print("Banco de dados inicializado.")

# --- Ferramentas para os Agentes ---
@tool
def get_trending_topics(agent: Agent, area_of_interest: str = "Ciência de Dados, CRM ou IA") -> str:
    """
    Gera uma lista de 5 tópicos relevantes e em alta para posts de LinkedIn, evitando repetições com base no session_state.
    """
    used_topics = agent.session_state.get("used_topics", []) if agent else []
    
    prompt = dedent(f"""\
        Você é um gerador de ideias de conteúdo para LinkedIn, focado em {area_of_interest}.
        Gere 5 ideias de tópicos inovadores e práticos para gestores de negócios, evitando os seguintes tópicos já usados: {', '.join(used_topics) if used_topics else 'Nenhum'}.
        Considere tendências de 2025 e temas como: KPIs de CRM, aplicações de IA, automação (ex.: SDR/BDR), personalização, previsão/preditivo, receita, faturamento, engajamento, fidelização, gestão estratégica.
        Priorize palavras-chave: conversão, fidelização, receita, faturamento, engajamento, automação, KPIs, estratégico, gestão, previsão, preditivo.
        Retorne apenas os títulos, uma por linha.
    """)
    
    try:
        response = agent.run(prompt, stream=False)
        return response.content
    except Exception as e:
        print(f"Erro ao gerar tópicos: {e}")
        return "\n".join([
            "Como a IA generativa aumenta a receita no CRM em 2025",
            "Automação de SDRs com IA para maior conversão",
            "KPIs de CRM para gestão estratégica",
            "Modelos preditivos para fidelização de clientes",
            "Engajamento de clientes com personalização via IA"
        ])

@tool(requires_confirmation=True)
def send_post_for_approval(agent: Agent, post: PostResponse, session_id: str) -> str:
    """
    Envia o post gerado por e-mail para aprovação.
    """
    try:
        msg = MIMEText(f"""
        Novo post gerado para o LinkedIn (Sessão: {session_id})

        Título: {post.title}
        Conteúdo: {post.content}
        Hashtags: {' '.join(post.hashtags)}

        Acesse os links abaixo para aprovar ou rejeitar:
        Aprovar: http://localhost:8000/approve_post/{post.id}
        Rejeitar: http://localhost:8000/reject_post/{post.id}?reason=motivo
        (Para rejeitar, substitua 'motivo' no link pelo motivo da rejeição, ex.: 'muito genérico')
        """)
        msg['Subject'] = f"Novo Post LinkedIn - {post.title}"
        msg['From'] = SMTP_USER
        msg['To'] = SMTP_USER

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, SMTP_USER, msg.as_string())
        return "E-mail de aprovação enviado com sucesso!"
    except Exception as e:
        return f"Erro ao enviar e-mail: {e}"

# --- Função de Contexto para Tendências ---
def get_external_trends() -> str:
    return "Tendências de 2025: IA preditiva domina CRM, automação de vendas cresce 20%, foco em KPIs de receita."

# --- Inicializa os Agentes ---
topic_agent = Agent(
    name="TopicAgent",
    model=Gemini(id="gemini-1.5-flash"),
    description="Você é um assistente especializado em gerar tópicos relevantes para posts no LinkedIn sobre Ciência de Dados, CRM e IA.",
    instructions=dedent("""\
        Sua tarefa é gerar tópicos relevantes para posts no LinkedIn, com base em tendências externas e histórico de sessões.
        Use a ferramenta `get_trending_topics` para obter tópicos novos, evitando repetições com base nos tópicos usados: {used_topics}.
        Tendências externas: {external_trends}
        Retorne apenas o tópico selecionado.
    """),
    tools=[get_trending_topics],
    storage=SqliteStorage(table_name="topic_agent_sessions", db_file="tmp/linkedin.db"),
    session_state={"used_topics": [], "external_trends": get_external_trends()},
    add_state_in_messages=True,
    add_history_to_messages=True,
    num_history_runs=3,
    markdown=True,
    show_tool_calls=True,
)

approval_agent = Agent(
    name="ApprovalAgent",
    model=Gemini(id="gemini-1.5-flash"),
    description="Você é um assistente especializado em gerar posts para LinkedIn e gerenciar aprovação.",
    instructions=dedent("""\
        Sua tarefa é gerar um post para LinkedIn com base no tópico fornecido, com tom {tone}, aproximadamente {length} caracteres, e incluir o call-to-action: '{call_to_action}'.
        Adicione 3-5 hashtags relevantes.
        Após gerar o post, use a ferramenta `send_post_for_approval` para enviar para aprovação por e-mail.
        Retorne o post no formato JSON com os campos: id, title, content, hashtags, status.
    """),
    tools=[send_post_for_approval],
    storage=SqliteStorage(table_name="approval_agent_sessions", db_file="tmp/linkedin.db"),
    session_state={"external_trends": get_external_trends()},
    add_state_in_messages=True,
    add_history_to_messages=True,
    num_history_runs=3,
    markdown=True,
    show_tool_calls=True,
    response_model=PostResponse,
)

# --- Inicializa o Team ---
content_team = Team(
    name="LinkedInContentTeam",
    mode="coordinate",
    model=Gemini(id="gemini-1.5-flash"),
    members=[topic_agent, approval_agent],
    instructions=[
        "Collaborar para gerar um post no LinkedIn com base em um tópico relevante.",
        "O TopicAgent deve selecionar um tópico usando `get_trending_topics`.",
        "O ApprovalAgent deve gerar o post com base no tópico e enviá-lo para aprovação.",
        "Retornar apenas a resposta final do ApprovalAgent no formato JSON.",
    ],
    storage=SqliteStorage(table_name="team_sessions", db_file="tmp/linkedin.db"),
    session_state={"used_topics": [], "external_trends": get_external_trends()},
    markdown=True,
    show_members_responses=True,
    enable_agentic_context=True,
    add_datetime_to_instructions=True,
)

# --- Função auxiliar para salvar post no banco ---
def save_post_to_db(topic: str, post_data: dict, session_id: str) -> int:
    conn = sqlite3.connect("tmp/linkedin.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO posts (session_id, title, content, hashtags, status) VALUES (?, ?, ?, ?, ?)",
        (session_id, post_data["title"], post_data["content"], str(post_data["hashtags"]), post_data.get("status", "pending"))
    )
    post_id = cursor.lastrowid
    cursor.execute("UPDATE topics SET usage_count = usage_count + 1, last_used = ? WHERE topic = ?",
                   (datetime.datetime.now(), topic))
    conn.commit()
    conn.close()
    return post_id

# --- Endpoint para gerar post ---
@app.post("/generate_post", response_model=PostResponse)
async def generate_post(request: GeneratePostRequest):
    max_retries = 3
    retry_delay = 2  # segundos
    
    for attempt in range(max_retries):
        try:
            # Usa o Team para coordenar a geração do post
            response = content_team.run(
                dedent(f"""\
                    Gere um post para o LinkedIn sobre {request.topic}.
                    Use tom {request.tone}, aproximadamente {request.length} caracteres, e inclua o call-to_action: '{request.call_to_action}'.
                """),
                session_id=request.session_id
            )
            
            # Verifica se o ApprovalAgent está pausado para confirmação
            if approval_agent.is_paused:
                for tool in approval_agent.run_response.tools_requiring_confirmation:
                    if tool.tool_name == "send_post_for_approval":
                        print(f"Post aguardando aprovação: {tool.tool_args}")
                        tool.confirmed = True  # Simula aprovação automática para testes
                response = content_team.continue_run()
            
            # Extrai o post gerado
            post_data = json.loads(response.content) if response.content else {
                "title": f"Post sobre {request.topic}",
                "content": f"Conteúdo de exemplo sobre {request.topic}. {request.call_to_action}",
                "hashtags": ["#IA", "#CRM", "#CiênciaDeDados"],
                "status": "pending"
            }
            post_id = save_post_to_db(request.topic, post_data, request.session_id)
            post = PostResponse(id=post_id, created_at=datetime.datetime.now().isoformat(), **post_data)
            
            # Atualiza o session_state do team com o tópico usado
            content_team.session_state["used_topics"].append(post_data["title"])
            
            # Exibe métricas do run
            print("--- Métricas do Team ---")
            pprint(response.metrics)
            
            return post
        
        except Exception as e:
            print(f"Tentativa {attempt + 1}/{max_retries} falhou: {str(e)}")
            if "503" in str(e) and attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            # Fallback em caso de falha após todas as tentativas
            print(f"Falha após {max_retries} tentativas. Usando post padrão.")
            conn = sqlite3.connect("tmp/linkedin.db")
            cursor = conn.cursor()
            cursor.execute("SELECT topic FROM topics ORDER BY usage_count ASC LIMIT 1")
            topic = cursor.fetchone()
            conn.close()
            fallback_topic = topic[0] if topic else request.topic
            post_data = {
                "title": f"Post sobre {fallback_topic}",
                "content": f"Conteúdo de exemplo sobre {fallback_topic}. {request.call_to_action}",
                "hashtags": ["#IA", "#CRM", "#CiênciaDeDados"],
                "status": "pending"
            }
            post_id = save_post_to_db(fallback_topic, post_data, request.session_id)
            post = PostResponse(id=post_id, created_at=datetime.datetime.now().isoformat(), **post_data)
            
            # Envia para aprovação (usando entrypoint diretamente)
            approval_result = send_post_for_approval.entrypoint(agent=approval_agent, post=post, session_id=request.session_id)
            print(f"Resultado da aprovação: {approval_result}")
            
            return post

# --- Endpoint para consultar um post ---
@app.get("/get_post/{post_id}", response_model=PostResponse)
async def get_post(post_id: int):
    conn = sqlite3.connect("tmp/linkedin.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, session_id, title, content, hashtags, status, rejection_reason, created_at FROM posts WHERE id = ?",
        (post_id,)
    )
    post = cursor.fetchone()
    conn.close()
    
    if not post:
        raise HTTPException(status_code=404, detail=f"Post com id {post_id} não encontrado.")
    
    return PostResponse(
        id=post[0],
        title=post[2],
        content=post[3],
        hashtags=eval(post[4]),
        status=post[5],
        rejection_reason=post[6],
        created_at=post[7]
    )

# --- Endpoint para aprovar post ---
@app.get("/approve_post/{post_id}")
async def approve_post(post_id: int):
    conn = sqlite3.connect("tmp/linkedin.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE posts SET status = 'approved' WHERE id = ?", (post_id,))
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Post com id {post_id} não encontrado.")
    conn.commit()
    conn.close()
    return {"message": f"Post {post_id} aprovado com sucesso!"}

# --- Endpoint para rejeitar post ---
@app.get("/reject_post/{post_id}")
async def reject_post(post_id: int, reason: str = "Nenhum motivo fornecido"):
    conn = sqlite3.connect("tmp/linkedin.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE posts SET status = 'rejected', rejection_reason = ? WHERE id = ?", (reason, post_id))
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Post com id {post_id} não encontrado.")
    conn.commit()
    conn.close()
    return {"message": f"Post {post_id} rejeitado. Motivo: {reason}"}

# --- Endpoint para métricas ---
@app.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    conn = sqlite3.connect("tmp/linkedin.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT strftime('%W', created_at) as week, COUNT(*) 
        FROM posts 
        GROUP BY strftime('%W', created_at)
    """)
    posts_per_week = {row[0]: row[1] for row in cursor.fetchall()}
    
    cursor.execute("SELECT topic, usage_count FROM topics ORDER BY usage_count DESC LIMIT 5")
    popular_topics = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    return MetricsResponse(posts_per_week=posts_per_week, popular_topics=popular_topics)