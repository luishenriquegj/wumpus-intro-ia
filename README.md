# 🧠 Projeto Wumpus World — Agente Bayesiano com Visualização Interativa
    Este repositório implementa um Agente Bayesiano Inteligente para o clássico problema do Wumpus World, com:

    🌐 API FastAPI para simulações múltiplas
    📊 Dashboard Streamlit com visualizações interativas
    🤖 Agente probabilístico com modelo Bayesiano completo
    🔥 Ambiente com física realista: Wumpus móvel, brilho, brisa e fedor
    📈 Métricas PEAS (score, passos, nós expandidos, vitórias, derrotas...)
    🎨 Visualização em tempo real com sprites personalizados


# 🚀 Como Rodar o Projeto

    1) Instalar dependências
    python -m pip install fastapi uvicorn streamlit numpy matplotlib requests pydantic ipython

    2) Rodar a API FastAPI (Simulações Múltiplas)
    uvicorn simulations_api:app --reload
    Ela sobe em:

    http://localhost:8000
    Endpoints principais:
    Método	Rota	Descrição
    POST	/simulate	Executa N simulações e retorna métricas
    3) Rodar o Dashboard Streamlit
    streamlit run app.py
    Abre automaticamente em:

    http://localhost:8501
    4) Rodar os dois juntos (modo simplificado)
    python run_all.py

# 🧩 Arquivos Principais

### 🧠 besyan_agent.py — Agente Bayesiano Inteligente
Implementa:

- Modelo Bayesiano para:
    - probabilidade de Wumpus móvel
    - probabilidade de poços
    - probabilidade do ouro
    - Inferência tipo Minesweeper
    - Fronteira de exploração segura
    - Plano de emergência para ambientes incertos
- A* modificado com custo baseado em risco
- Histórico completo do agente
- Contador de nós expandidos
- Integração com score do ambiente

O método central é:

``` 
    choose_action(self, agent_pos, gold_pos)
```

 ###   🌍 wumpus_environment.py — Física do Mundo Wumpus
    Contém toda a simulação do ambiente:

- Wumpus com movimento aleatório
- Poços distribuídos no mapa
- Ouro em posição oculta
- Perceptos:
    - Brisa (buracos)
    - Fedor (Wumpus)
    - Brilho (ouro adjacente)
- Morte por poço ou Wumpus
- Vitória ao pegar o ouro
- Score conforme o modelo PEAS
- Retorna perceptos via:
    - Processa movimento via:
        ```` 
            obs = env.get_observation()
            obs, done, score = env.step(action)
        ````
### 🎨 visualize_game.py — Visualização e Dashboard
É o módulo que conecta:

- Agente
- Ambiente
- Gráficos Matplotlib
- Dashboard Streamlit
- Chamadas à API
- Inclui:

    ####    🟢 Simulação Única
        Com animação frame a frame no Streamlit.

    ####    🔵 Simulações Múltiplas
        Chama FastAPI → plota métricas como:

- vitórias, mortes, travamentos
- score total e score médio
- passos totais e médios
- nós expandidos
    ### 🔶 Heatmap de Perigo
        Mostra:

        - risco estimado do Wumpus
        - risco estimado dos poços
        - posição provável do ouro
        - histórico de movimento
        - plano atual

### 🌐 app.py — Painel Streamlit
    Fornece interface interativa:

- escolher tamanho do tabuleiro
- número de buracos
- passos máximos
- modo “Única” ou “Múltiplas”
- número de simulações (via API)
- Chamando:

    ```
        run_game_streamlit(...)
    ```
### 🔧 run_all.py — Executor combinado
    Script auxiliar que inicia:

- FastAPI
- Streamlit
- em paralelo (embora sem hot reload).

# 📊 Métricas (PEAS)

    O sistema calcula automaticamente:

   - Score total
   - Score médio
   - Vitórias
   - Mortes pelo Wumpus
   - Quedas em poços 
   - Travamentos
   - Passos totais e médios
   - Nós expandidos pelo A*
   - Essas métricas são retornadas pela API e renderizadas no Streamlit.

# 🖥️ Exemplo de Uso
- Simulação única:
    - Ajuste os valores na barra lateral
    - Clique "Iniciar Jogo"
    - Observe o agente explorar o mundo ao vivo
- Simulações múltiplas (API):
    - Mude para modo "Múltiplas"
    - Escolha o número de simulações
    - Veja os gráficos agregados e cálculos de média