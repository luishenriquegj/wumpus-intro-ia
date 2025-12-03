import requests
from besyan_agent import BayesianAgent
from wumpus_environment import WumpusEnvironment, get_sprite
import matplotlib.pyplot as plt
import streamlit as st
import numpy as np

SPRITE_LIB = {
    'hero': get_sprite('hero'),
    'wumpus': get_sprite('wumpus'),
    'gold': get_sprite('gold'),
    'pit': get_sprite('pit')
}




def run_game_streamlit(size, n_pits, max_steps, num_simulations):
    if num_simulations == 1:
        # Executa uma única simulação
        st.write("Executando uma única simulação...")
        run_single_simulation(size, n_pits, max_steps)
    else:
        # Executa múltiplas simulações
        st.write(f"Executando {num_simulations} simulações...")
        run_multiple_simulations(size, n_pits, max_steps, num_simulations)
        


def run_single_simulation(size, n_pits, max_steps):
    # Cria um novo ambiente com o tamanho e número de poços definidos
    env = WumpusEnvironment(size=size, n_pits=n_pits)

    # Cria o agente Bayesiano
    agent = BayesianAgent(size=size)

    # Ambiente gera a primeira percepção (brisa, fedor, brilho etc.)
    obs = env.get_observation()

    # Agente atualiza suas probabilidades internas com essa percepção inicial
    agent.update(obs, env.agent_pos)

    step = 0      # contador de passos
    done = False  # indica se o jogo terminou

    # Espaço reservado no Streamlit para atualizar os gráficos a cada step
    plot_placeholder = st.empty()

    # Loop principal da simulação → roda até atingir o limite de passos
    while step < max_steps:

        # O agente escolhe uma ação baseado no estado atual do ambiente
        action = agent.choose_action(env.agent_pos, env.gold_pos)

        # Se o agente retornar None → ele está sem plano e ficou travado
        if action is None:
            st.write(f"Agente travou no passo {step}!")

            # Exibe o mundo e o estado do agente na tela
            with plot_placeholder.container():
                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7))
                visualize_game(env, agent, step, ax1, ax2)
                st.pyplot(fig)
                plt.close(fig)

            break  # encerra o jogo

        # Ambiente processa a ação: move o agente e retorna a nova percepção
        obs, done, score = env.step(action)
        step += 1  # incrementa o passo

        # Agente atualiza suas crenças com base na nova percepção e posição atual
        agent.update(obs, env.agent_pos)

        # Atualiza visualização gráfica no Streamlit
        with plot_placeholder.container():
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7))
            visualize_game(env, agent, step, ax1, ax2)
            st.pyplot(fig)
            plt.close(fig)

        # Se o jogo terminou (ouro, wumpus, poço)
        if done:
            display_game_outcome(done, env, step) 
            break

    # Se o loop terminou sem "done = True", o agente não chegou ao objetivo
    if not done:
         display_game_outcome(done, env, step)

    
    display_results_single(step, agent.nodes_expanded,score)
    

def call_api(size, n_pits, max_steps, num_simulations):
    payload = {
        "size": size,
        "n_pits": n_pits,
        "max_steps": max_steps,
        "num_simulations": num_simulations,
        
    }

    response = requests.post("http://localhost:8000/simulate", json=payload,timeout=300)
    st.write(response)
    return response.json()

def run_multiple_simulations(size, n_pits, max_steps, num_simulations):

    with st.spinner("Executando simulações..."):
        results = call_api(size, n_pits, max_steps, num_simulations)

    st.success("Simulações concluídas!")
    display_results(results)
    return results

def display_results(results):
    st.write("## 📊 Resultados das Simulações")

    # --- LINHA SUPERIOR: cards principais ---
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div style="
            background-color:#e8f5e9;
            padding:20px;
            border-radius:10px;
            text-align:center;
            border:1px solid #c8e6c9;">
            <h4 style="margin:0; color:#2e7d32;">Vitórias</h4>
            <h2 style="margin:0; color:#1b5e20;">{}</h2>
        </div>
        """.format(results["victories"]), unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="
            background-color:#ffebee;
            padding:20px;
            border-radius:10px;
            text-align:center;
            border:1px solid #ffcdd2;">
            <h4 style="margin:0; color:#c62828;">Mortes pelo Wumpus</h4>
            <h2 style="margin:0; color:#b71c1c;">{}</h2>
        </div>
        """.format(results["defeats_wumpus"]), unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div style="
            background-color:#fffde7;
            padding:20px;
            border-radius:10px;
            text-align:center;
            border:1px solid #fff9c4;">
            <h4 style="margin:0; color:#f57f17;">Quedas em Buracos</h4>
            <h2 style="margin:0; color:#f9a825;">{}</h2>
        </div>
        """.format(results["defeats_pit"]), unsafe_allow_html=True)

    st.write("---")

    # --- LINHA MÉTRICAS NUMÉRICAS ---
    col4, col5, col6 = st.columns(3)

    with col4:
        st.metric("Jogos Executados", results["games_played"])

    with col5:
        win_rate = (results["victories"] / results["games_played"]) * 100
        st.metric("Taxa de Vitória (%)", f"{win_rate:.2f}%")

    with col6:
        st.metric("Não Concluídos", results['stuck'])
    
    st.write("### 📈 Estatísticas de Score")

    colA, colB = st.columns(2)

    total_score = results["total_score"]
    avg_score  = results["average_score"]

    with colA:
        st.metric("Score Total", total_score)

    with colB:
        st.metric("Score Médio", f"{avg_score:.2f}")

    st.write("---")

    # --- MÉTRICAS DE PASSOS ---
    st.write("### 🧭 Métricas de Movimentação")

    col7, col8 = st.columns(2)

    with col7:
        st.metric("Total de Passos", results["total_steps"])

    with col8:
        avg_steps = results["total_steps"] / results["games_played"]
        st.markdown(f"""
        <div style="
            background-color:#e8f5e9;
            padding:20px;
            border-radius:10px;
            text-align:center;
            border:1px solid #c8e6c9;
            margin-top:10px;">
            <h4 style="margin:0; color:#2e7d32;">Média de Passos</h4>
            <h2 style="margin:0; color:#1b5e20;">{avg_steps:.2f}</h2>
        </div>
        """, unsafe_allow_html=True)

    # --- MÉTRICA DE NÓS EXPANDIDOS ---
    st.write("### 🤖 Métricas do Agente")

    total_expanded = results.get("total_nodes_expanded", None)

    if total_expanded is not None:
        avg_expanded = total_expanded / results["games_played"]

        st.markdown("""
        <div style="
            background-color:#e3f2fd;
            padding:20px;
            border-radius:10px;
            text-align:center;
            border:1px solid #bbdefb;
            margin-top:10px;">
            <h4 style="margin:0; color:#0d47a1;">Nós Expandidos (Total)</h4>
            <h2 style="margin:0; color:#0d47a1;">{}</h2>
            <p style="margin:5px 0 0 0 ;  color:#0d47a1; font-size:14px;">Média por jogo: {:.2f}</p>
        </div>
        """.format(total_expanded, avg_expanded), unsafe_allow_html=True)

    st.write("---")
    st.success("✔ Análise concluída!")

def display_results_single(step_count, nodes_expanded, score):
    st.write("## 📊 Resultado da Simulação Única")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Passos", step_count)

    with col2:
        st.metric("Nós Expandidos", nodes_expanded)

    with col3:
        st.metric("Score", score)

    st.success("✔ Simulação concluída!")

def display_game_outcome(done, env, step):
    if done:
        # --- VITÓRIA ---
        if env.agent_pos == env.gold_pos:
            st.markdown(f"""
            <div style="
                background-color:#e8f5e9;
                border-left:8px solid #2e7d32;
                padding:18px;
                border-radius:10px;
                margin-top:15px;">
                <h3 style="color:#1b5e20; margin:0;">🏆 Vitória!</h3>
                <p style="color:#1b5e20; margin:0;">O agente encontrou o ouro no passo <b>{step}</b>.</p>
            </div>
            """, unsafe_allow_html=True)

        # --- DERROTA: WUMPUS ---
        elif env.agent_pos == env.wumpus_pos:
            st.markdown(f"""
            <div style="
                background-color:#ffebee;
                border-left:8px solid #c62828;
                padding:18px;
                border-radius:10px;
                margin-top:15px;">
                <h3 style="color:#b71c1c; margin:0;">💀 Derrota!</h3>
                <p style="color:#b71c1c; margin:0;">O agente foi devorado pelo Wumpus no passo <b>{step}</b>.</p>
            </div>
            """, unsafe_allow_html=True)

        # --- DERROTA: POÇO ---
        elif env.agent_pos in env.pits_pos:
            st.markdown(f"""
            <div style="
                background-color:#fffde7;
                border-left:8px solid #f57f17;
                padding:18px;
                border-radius:10px;
                margin-top:15px;">
                <h3 style="color:#f57f17; margin:0;">🕳️ Derrota!</h3>
                <p style="color:#8d6e63; margin:0;">O agente caiu em um poço no passo <b>{step}</b>.</p>
            </div>
            """, unsafe_allow_html=True)

    else:
        # --- TRAVADO OU TEMPO ESGOTADO ---
        st.markdown(f"""
        <div style="
            background-color:#e3f2fd;
            border-left:8px solid #1565c0;
            padding:18px;
            border-radius:10px;
            margin-top:15px;">
            <h3 style="color:#0d47a1; margin:0;">⚠️ Jogo não concluído</h3>
            <p style="color:#0d47a1; margin:0;">O agente não completou a missão dentro do limite de passos.</p>
        </div>
        """, unsafe_allow_html=True)

def visualize_game(env, agent, step_num, ax1, ax2):
    # --- PLOT 1: TABULEIRO COM SPRITES ---

    #TAMANHO DAS SPRITES
    P_SIZE = 8
    board_img = np.zeros((env.size * P_SIZE, env.size * P_SIZE, 3), dtype=int)

    for i in range(env.size):
        for j in range(env.size):
            tile = env.floor_map[i][j]
            board_img[i*P_SIZE:(i+1)*P_SIZE, j*P_SIZE:(j+1)*P_SIZE] = tile

            sprite = None
            if (i, j) == env.agent_pos:
                sprite = SPRITE_LIB['hero']
            elif (i, j) == env.wumpus_pos:
                sprite = SPRITE_LIB['wumpus']
            elif (i, j) == env.gold_pos:
                sprite = SPRITE_LIB['gold']
            elif (i, j) in env.pits_pos:
                is_pit = False
                for p in env.pits_pos:
                    if p == (i,j): is_pit = True
                if is_pit: sprite = SPRITE_LIB['pit']

            if sprite is not None:
                for r in range(P_SIZE):
                    for c in range(P_SIZE):
                        alpha = sprite[r,c,3]
                        if alpha > 0:
                            rgb = sprite[r,c,:3] * 255
                            board_img[i*P_SIZE+r, j*P_SIZE+c] = rgb

    ax1.imshow(board_img)
    ax1.axis('off')
    ax1.set_title(f"Mundo Real - Passo {step_num}\n{env.message}", fontsize=12, fontweight='bold')

    # --- PLOT 1: HEATMAP COM PERECEPÇÃO DE PERIGO/RECOMPENSA/HISTORICO DO AGENTE ---
    # INICIALIZAÇÃO DO HEATMAP DE PERIGO
    combined_danger = np.maximum(agent.P_wumpus, agent.P_pit)
    heatmap = ax2.imshow(combined_danger, cmap='Reds', interpolation='nearest', vmin=0, vmax=1)

    gold_map = agent.P_gold

    # PROCURA A POSIÇÃO PROVÁVEL DO OURO COM BASE NAS PERCEPÇÕES DO AGENTE
    gold_y, gold_x = np.unravel_index(np.argmax(gold_map), gold_map.shape)

    # PLOTA O O OURO PROVÁVEL POR CIMA DO HEATMAP DE PERIGO
    ax2.plot(
        gold_x, gold_y,
        marker='*', markersize=20, color='yellow',
        markeredgecolor='black', markeredgewidth=1.5,
        label="Ouro provável"
    )

    # DESENHA NO HEATMAP O HISTÓRICO DE PASSOS DO AGENTE
    if len(agent.history) > 1:
        for i in range(len(agent.history) - 1):
            start = agent.history[i]
            end = agent.history[i+1]
            x_start, y_start = start[1], start[0]
            x_end, y_end = end[1], end[0]
            dx, dy = x_end - x_start, y_end - y_start
            ax2.arrow(x_start, y_start, dx*0.8, dy*0.8, head_width=0.3, color='blue', alpha=0.5)

    ax2.plot(env.agent_pos[1], env.agent_pos[0], 'bo', markersize=10, label="Agente")

    if agent.current_path:
        path_y = [p[0] for p in agent.current_path]
        path_x = [p[1] for p in agent.current_path]
        path_y.insert(0, env.agent_pos[0])
        path_x.insert(0, env.agent_pos[1])
        ax2.plot(path_x, path_y, 'g-', linewidth=2, label="Plano")

    ax2.grid(color='gray', linewidth=0.5)
    ax2.set_title("Visão do Agente", fontsize=12)

    plt.tight_layout()