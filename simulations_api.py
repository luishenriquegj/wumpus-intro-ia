from fastapi import FastAPI
from fastapi.concurrency import run_in_threadpool
from besyan_agent import BayesianAgent
from pydantic import BaseModel

from wumpus_environment import WumpusEnvironment

app = FastAPI()

class SimulationRequest(BaseModel):
    size: int
    n_pits: int
    max_steps: int
    num_simulations: int



def run_multiple_simulations_api(size, n_pits, max_steps, num_simulations):
    # Dicionário que acumula as métricas de TODAS as simulações
    results = {
        "victories": 0,             # quantas vezes o agente pegou o ouro
        "defeats_wumpus": 0,        # quantas vezes morreu pelo wumpus
        "defeats_pit": 0,           # quantas vezes caiu em um buraco
        "total_steps": 0,           # total de passos somados em todas as simulações
        "games_played": num_simulations,  # quantidade de jogos simulados
        "stuck": 0,                 # vezes em que o agente travou e não tinha ação
        "total_nodes_expanded": 0,  # total de nós expandidos pelo agente
        "total_score": 0,           # pontuação total bruta
        "average_score": 0
    }
    
    # Executa N simulações consecutivas
    for sim in range(num_simulations):

        # Cria um novo agente e um novo ambiente para cada simulação
        agent = BayesianAgent(size=size)
        env = WumpusEnvironment(size=size, n_pits=n_pits)

        # Obter a primeira observação e atualizar o agente
        obs = env.get_observation()
        agent.update(obs, env.agent_pos)
        step = 0  # conta quantos passos foram dados neste jogo

        # Loop principal do jogo
        while step <= max_steps:

            # Agente decide uma ação baseada no estado atual
            action = agent.choose_action(env.agent_pos, env.gold_pos)
        
            # Quando o agente fica sem plano (nenhum opção válida), ele trava
            if action is None:
                results["stuck"] += 1
                break

            # Ambiente executa a ação: anda, atualiza posição e retorna a nova percepção
            obs, done, score = env.step(action)
            step += 1  # incrementa a quantidade de passos

            # Atualiza as probabilidades e histórico do agente
            agent.update(obs, env.agent_pos)

            # Se o jogo terminou, checamos o motivo
            if done:
                if env.agent_pos == env.gold_pos:
                    # Vitória → ouro encontrado
                    results["victories"] += 1
                    break
                elif env.agent_pos == env.wumpus_pos:
                    # Derrota → wumpus comeu
                    results["defeats_wumpus"] += 1
                    break
                elif env.agent_pos in env.pits_pos:
                    # Derrota → caiu em um buraco
                    results["defeats_pit"] += 1
                    break

        # Soma os passos deste jogo ao total geral
        results["total_steps"] += step
        results["total_nodes_expanded"] += agent.nodes_expanded # Soma os nós expandidos pelo agente nesta simulação
        results["total_score"] += env.score

        # Se o agente não terminou e não ficou sem ação → provavelmente ficou preso
        if not done and action is not None:
            results["stuck"] += 1

    results["average_score"] = results["total_score"] / num_simulations
    # Retorna todas as métricas consolidadas
    return results

@app.post("/simulate")
async def simulate(req: SimulationRequest):
    # Roda a função de simulação pesada em outra thread
    # Isso evita travar o servidor FastAPI
    results = await run_in_threadpool(
        run_multiple_simulations_api,
        req.size,        # tamanho do tabuleiro
        req.n_pits,      # quantidade de buracos
        req.max_steps,   # máximo de passos por simulação
        req.num_simulations  # número total de simulações
    )

    # Retorna o dicionário com todas as métricas agregadas
    return results