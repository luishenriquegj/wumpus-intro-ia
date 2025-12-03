
import streamlit as st
from visualize_game import run_game_streamlit

def main():
    st.title("Wumpus Game Dashboard")
    
    # Sidebar para controle de parâmetros
    st.sidebar.header("Configurações do Jogo")
    game_level = st.sidebar.slider("Dificuldade (Número de buracos)", 1, 40, 1)
    board_scale = st.sidebar.slider("Tamanho do Tabuleiro (4x4, 5x5, 6x6...)", 4, 20, 4)
    max_steps_agent = st.sidebar.slider("Máximo de Passos do Agente", 10, 400, 10)

    simulation_mode = st.sidebar.selectbox("Modo de Simulação", ["Única", "Múltiplas"])
    num_of_simulations = 1
    
    if simulation_mode == "Múltiplas":
        num_of_simulations = st.sidebar.slider("Número de Simulações", 2, 100, 2)

    if "run" not in st.session_state:
        st.session_state.run = False

    if st.sidebar.button("Iniciar Jogo"):
        st.session_state.run = True

    if st.session_state.run:
        run_game_streamlit(size=board_scale, n_pits=game_level, max_steps=max_steps_agent, num_simulations=num_of_simulations)
        st.session_state.run = False

if __name__ == "__main__":
    main()