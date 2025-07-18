# 🤖 Agente de IA para Geração de Conteúdo no LinkedIn

![LinkedIn Content Agent Banner](images/tres-agentes-de-ia-525.webp)

[![Status do Projeto](https://img.shields.io/badge/Status-Em%20Desenvolvimento-yellow.svg)](https://github.com/muriloWeber/linkedin_content_agent/blob/main/README.md)

Este projeto demonstra a automação inteligente da criação e postagem de conteúdo profissional no LinkedIn, focando em temas como **Ciência de Dados, CRM e Inteligência Artificial**.

---

## 💡 Visão Geral do Projeto

O objetivo principal é criar um agente autônomo que possa:
1.  **Gerar ideias de posts** relevantes e engajadores sobre as áreas de minha expertise (Ciência de Dados, CRM, IA).
2.  **Desenvolver o conteúdo completo** dos posts, incluindo título, corpo do texto e hashtags, com um tom profissional e direto.
3.  **Publicar automaticamente** esses posts no perfil do LinkedIn, garantindo consistência e visibilidade.

Este projeto não só otimiza o branding pessoal, como também serve como uma poderosa demonstração das capacidades de automação com IA para fins práticos.

---

## ⚙️ Arquitetura e Tecnologias Utilizadas

A solução é construída com uma arquitetura modular, utilizando as seguintes tecnologias:

* **Python:** Linguagem de programação principal.
* **FastAPI:** Framework web para construir a API que hospeda a lógica do agente, oferecendo endpoints para geração e gerenciamento de posts.
* **LangChain:** Framework para orquestração de LLMs, facilitando a criação e o encadeamento de passos lógicos para o agente de IA.
* **Google Gemini Pro:** Modelo de Linguagem Grande (LLM) principal, utilizado para a geração criativa de ideias e conteúdo dos posts.
* **Make.com (Antigo Integromat):** Plataforma de automação e orquestração no-code/low-code, responsável por agendar a execução do agente e realizar a publicação final no LinkedIn.
* **Hospedagem Gratuita:** Utilização de plataformas como Render ou Google Cloud Run para o deploy da API, garantindo custo zero para o projeto de portfólio.
* **Conceitos Aplicados:**
    * **Engenharia de Prompt:** Criação de prompts otimizados para guiar o Gemini na geração de conteúdo relevante e com o tom desejado.
    * **Tools/Function Calling (Simulação de MCP):** O agente utiliza "ferramentas" internas (simuladas inicialmente) para obter ideias e inspirar a criação de posts.

---

## 🚀 Como Rodar Localmente (Desenvolvimento)

Siga os passos abaixo para configurar e rodar o projeto em sua máquina:

1.  **Clone o Repositório:**
    ```bash
    git clone [https://github.com/muriloWeber/linkedin_content_agent.git](https://github.com/muriloWeber/linkedin_content_agent.git)
    cd linkedin_content_agent
    ```
2.  **Crie e Ative o Ambiente Virtual:**
    ```bash
    python3 -m venv venv
    # No Linux/macOS
    source venv/bin/activate
    # No Windows (PowerShell)
    # .\venv\Scripts\Activate.ps1
    ```
3.  **Instale as Dependências:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configure suas Variáveis de Ambiente:**
    * Crie um arquivo `.env` dentro da pasta `config/`.
    * Adicione sua chave da API do Google Gemini:
        ```dotenv
        GOOGLE_API_KEY="SUA_CHAVE_API_DO_GEMINI_AQUI"
        ```
    * **ATENÇÃO:** Nunca publique seu arquivo `.env` no GitHub! Ele já está incluído no `.gitignore`.
5.  **Inicie a API FastAPI:**
    ```bash
    uvicorn src.main:app --reload
    ```
    A API estará acessível em `http://127.0.0.1:8000`.
6.  **Teste a API:**
    * Abra `http://127.0.0.1:8000/docs` no seu navegador para acessar a documentação interativa (Swagger UI) e testar o endpoint `/generate_linkedin_post`.

---

## 🚧 Desafios de Configuração e Soluções (LangChain Agent)

Durante o desenvolvimento e configuração deste agente, foram encontrados alguns desafios específicos relacionados à integração do LangChain com o `MessagesPlaceholder` e o tratamento do `agent_scratchpad`. As seguintes soluções foram aplicadas para garantir o funcionamento correto:

### 1. Erro `ValueError: Prompt missing required variables: {'tool_names'}`

* **Problema:** O `create_react_agent` exigia que a variável `tool_names` estivesse explicitamente presente no `ChatPromptTemplate` para que o LLM soubesse os nomes das ferramentas disponíveis.
* **Solução:** Adicionada a linha `{tool_names}` ao prompt do sistema no `src/main.py`.

    ```python
    # Exemplo do prompt ajustado:
    # "Use as ferramentas a seguir apenas se elas forem úteis para responder à pergunta. Os nomes das ferramentas que você pode usar são: {tool_names}."
    ```

### 2. Erro `variable agent_scratchpad should be a list of base messages, got of type <class 'str'>`

* **Problema:** O `MessagesPlaceholder` no prompt do agente esperava uma lista de objetos de mensagem (`BaseMessage`), mas o `agent_scratchpad` estava sendo interpretado como uma string em certas interações, causando um erro de tipagem.
* **Solução:** Configurado o `AgentExecutor` para usar `format_log_to_messages` no parâmetro `agent_scratchpad_tool_executor`. Esta função garante que o histórico de pensamentos do agente seja formatado corretamente como uma lista de mensagens.

    ```python
    # Importação necessária:
    # from langchain.agents.format_scratchpad import format_log_to_messages

    # Configuração do AgentExecutor:
    # agent_executor = AgentExecutor(
    #     agent=agent,
    #     tools=tools,
    #     verbose=True,
    #     handle_parsing_errors=True,
    #     agent_scratchpad_tool_executor=format_log_to_messages
    # )
    ```
    *Nota:* Tentativas anteriores de usar `render_text_to_messages` ou passar `agent_scratchpad: []` diretamente no `ainvoke` não foram eficazes ou causaram outros erros de importação/tipagem, sendo a configuração do `agent_scratchpad_tool_executor` a abordagem mais robusta para este cenário.

### Versões das Dependências (Recomendadas/Testadas)

Para garantir a compatibilidade, as seguintes versões das bibliotecas foram testadas ou são recomendadas:

* **Python:** 3.13.x (embora 3.10 ou 3.11 possam ter maior compatibilidade histórica com LangChain)
* **langchain:** (Adicione aqui a versão exata que você tem, ex: `0.1.17`)
* **langchain-google-genai:** (Adicione aqui a versão exata que você tem, ex: `0.0.10`)
* **pydantic:** (Adicione aqui a versão exata que você tem, ex: `2.7.1`)
* **fastapi:** (Adicione aqui a versão exata que você tem, ex: `0.110.0`)
* **uvicorn:** (Adicione aqui a versão exata que você tem, ex: `0.29.0`)

Você pode obter as versões exatas executando `pip show <nome_da_biblioteca>` no seu ambiente virtual.

---

## 🗺️ Próximos Passos (Roadmap)

* Refinar a lógica de geração de ideias de posts (integrar com feeds RSS ou APIs de notícias).
* Melhorar a engenharia de prompt para um tom e estilo de escrita mais personalizados.
* Desenvolver a persistência para gerenciar tópicos já abordados ou ideias futuras.
* Configurar a automação completa no Make.com para a publicação agendada no LinkedIn.

---

## 🤝 Contribuições

Sinta-se à vontade para abrir issues ou pull requests se tiver sugestões ou encontrar problemas.

---

## 📄 Licença

Este projeto está licenciado sob a Licença MIT.

---