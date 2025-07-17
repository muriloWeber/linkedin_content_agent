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
    git clone [https://github.com/seu-usuario/linkedin_content_agent.git](https://github.com/muriloWeber/linkedin_content_agent.git)
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