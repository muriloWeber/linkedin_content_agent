# src/main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import os

# Importar o LangChain e Gemini
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema.output_parser import StrOutputParser
from langchain.agents import AgentExecutor, create_react_agent, tool
from langchain.agents.format_scratchpad import format_log_to_messages

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv(dotenv_path='config/.env')

# Inicializa o FastAPI
app = FastAPI(
    title="Agente de Conteúdo para LinkedIn",
    description="API para gerar posts de LinkedIn sobre Ciência de Dados, CRM e IA.",
    version="0.1.0"
)

# Verifica se a chave da API do Google está configurada
if not os.getenv("GOOGLE_API_KEY"):
    raise ValueError("A variável de ambiente GOOGLE_API_KEY não está configurada. Por favor, adicione-a em config/.env")

# Inicializa o modelo Gemini
llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.5)

# --- Modelos Pydantic para as requisições da API ---
class GeneratePostRequest(BaseModel):
    topic: str = "Um tópico relevante sobre Ciência de Dados, CRM ou IA."
    tone: str = "profissional e direto"
    length: int = 1000 # Caracteres
    call_to_action: str = "O que você achou? Compartilhe sua opinião!"

class PostResponse(BaseModel):
    title: str
    content: str
    hashtags: list[str]
    status: str = "success"

# --- Ferramentas (Tools) para o Agente ---
@tool
def get_trending_topics(area_of_interest: str = "Ciência de Dados, CRM ou IA") -> str:
    """
    Gera uma lista de tópicos relevantes e em alta para posts de LinkedIn sobre
    a área(s) de interesse especificada(s), com um tom de consultoria.
    A entrada deve ser a área geral de interesse (e.g., 'Ciência de Dados', 'CRM', 'IA', 'Automação').
    """
    idea_generation_prompt = ChatPromptTemplate.from_messages([
        ("system", f"""Você é um gerador de ideias de conteúdo para LinkedIn, focado em {area_of_interest}, com um forte tom de consultoria.
        Gere 5 ideias de tópicos de posts que sejam inovadores, práticos e engajadores.
        Considere temas como: dicas de KPIs de CRM, novas tendências de IA, aplicações de IA em CRM, aplicações de Ciência de Dados em CRM, relevância da Ciência de Dados para aumentar receita/lucro, automação de processos, personalização de clientes, ética em IA, MLOps, Data Storytelling.
        As ideias devem ser apenas os títulos dos tópicos, uma por linha, sem numeração ou marcadores."""),
        ("human", f"""Por favor, gere as ideias de tópicos agora.""")
    ])

    try:
        idea_chain = idea_generation_prompt | llm | StrOutputParser()
        ideas_raw = idea_chain.invoke({"area_of_interest": area_of_interest})
        return ideas_raw
    except Exception as e:
        print(f"Erro ao gerar tópicos com LLM: {e}")
        return "Automação de leads com IA, Otimização de CRM com Data Science, Tendências de IA para 2025, Experiência do Cliente com IA."

# --- Lógica do Agente LangChain ---
# Definindo o prompt ReAct diretamente no código.
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", """Você é um assistente de IA útil e um especialista em Ciência de Dados, CRM e Inteligência Artificial.
        Você tem acesso às seguintes ferramentas:

        {tools}

        Use as ferramentas a seguir apenas se elas forem úteis para responder à pergunta. Os nomes das ferramentas que você pode usar são: {tool_names}.

        Para usar uma ferramenta, use o formato:
        ```json
        {{
            "action": "nome_da_ferramenta",
            "action_input": "entrada_para_a_ferramenta"
        }}
        ```
        Para responder ao usuário, use o formato:
        ```json
        {{
            "action": "Final Answer",
            "action_input": "Sua resposta final aqui"
        }}
        ```

        Sua tarefa é ajudar a gerar ideias e conteúdo para posts de LinkedIn.
        """),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)


# Ferramentas que o agente pode usar
tools = [get_trending_topics]

# Cria o agente ReAct
agent = create_react_agent(llm, tools, prompt)

# Cria o executor do agente
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True,
    agent_scratchpad_tool_executor=format_log_to_messages
)


# --- Endpoint da API ---
@app.post("/generate_linkedin_post", response_model=PostResponse)
async def generate_linkedin_post(request: GeneratePostRequest):
    """
    Gera um post completo para o LinkedIn com base no tópico, tom e comprimento desejados.
    Se o tópico for genérico, o agente tentará gerar uma ideia.
    """
    try:
        chosen_topic = request.topic

        if "tópico relevante" in request.topic.lower() or not request.topic.strip():
            print("Solicitando ao agente para sugerir um tópico...")
            # Removida a passagem explícita de agent_scratchpad para ainvoke
            agent_response = await agent_executor.ainvoke({
                "input": "Preciso de um tópico interessante para um post de LinkedIn sobre Ciência de Dados, CRM ou IA. Sugira algo relevante e com tom de consultoria."
            })

            if "Final Answer:" in agent_response["output"]:
                chosen_topic = agent_response["output"].split("Final Answer:")[-1].strip()
            else:
                chosen_topic = agent_response["output"].strip()

            if not chosen_topic or "tópico relevante" in chosen_topic.lower() or "não consigo" in chosen_topic.lower():
                chosen_topic = "Aplicações práticas de IA em CRM para pequenas e médias empresas."

            print(f"Agente sugeriu o tópico: '{chosen_topic}'")


        post_generation_prompt = ChatPromptTemplate.from_messages([
            ("system", f"""Você é um especialista em Ciência de Dados, CRM e Inteligência Artificial, atuando como Analista de Implantação Sênior. Seu nome é Murilo Weber.
            Seu estilo de comunicação é profissional, direto, concreto e sem rodeios, como um consultor experiente.
            Seu objetivo é gerar posts engajadores e informativos para o LinkedIn, focando em insights acionáveis e tendências nas suas áreas de expertise.
            Os posts devem ter um tom de consultoria, oferecendo dicas, análises e aplicações práticas que agreguem valor para profissionais de negócios, especialmente em como Ciência de Dados e IA podem otimizar o CRM e impactar positivamente receita e lucro.
            Inclua emojis relevantes para o contexto e hashtags populares (5 a 7) ao final, relacionadas ao conteúdo e às suas áreas.
            O post deve ter aproximadamente {request.length} caracteres.
            Formate a saída com "Título: [Seu Título Aqui]", seguido do conteúdo do post, e depois as hashtags."""),
            ("human", f"""Gere um post para o LinkedIn sobre o tópico: "{chosen_topic}".
            Inclua um título chamativo.
            O post deve terminar com uma chamada para ação: "{request.call_to_action}".""")
        ])

        chain = post_generation_prompt | llm | StrOutputParser()

        raw_post_content = await chain.ainvoke({"topic": chosen_topic, "tone": request.tone, "length": request.length, "call_to_action": request.call_to_action})

        title = "Título Não Encontrado"
        content_lines = []
        hashtags = []

        found_title = False
        found_hashtags = False

        for line in raw_post_content.split('\n'):
            stripped_line = line.strip()
            if stripped_line.lower().startswith("título:"):
                title = stripped_line[len("título:"):].strip()
                found_title = True
            elif stripped_line.startswith("#"):
                hashtags.extend([tag.strip() for tag in stripped_line.split() if tag.startswith("#")])
                found_hashtags = True
            elif found_title and not found_hashtags:
                if stripped_line:
                    content_lines.append(stripped_line)
            elif found_hashtags:
                pass

        content = "\n".join(content_lines).strip()

        if not hashtags:
            hashtags = ["#CienciaDeDados", "#IA", "#CRM", "#Automação", "#Consultoria", "#Tech"]

        if content.startswith(title) and len(title) > 5:
            content = content[len(title):].strip()
            if content.startswith("\n"):
                content = content[1:].strip()

        return PostResponse(title=title, content=content, hashtags=hashtags)

    except Exception as e:
        print(f"Erro na API: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno ao gerar o post: {str(e)}")

# --- Endpoint de Teste ---
@app.get("/")
async def read_root():
    return {"message": "Bem-vindo à API do Agente de Conteúdo para LinkedIn!"}