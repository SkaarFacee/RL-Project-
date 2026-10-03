from guardian_swarm_env import GuardianSwarmEnv


env = GuardianSwarmEnv(
    render_mode="human"
)

observations, infos = env.reset(seed=42)

print("Weather:", infos["attacker_0"]["weather"])
print("POI values:", infos["attacker_0"]["poi_values"])
print("Attacker 0 target:", infos["attacker_0"]["target"])


while env.agents:

    actions = {
        agent: env.action_space(agent).sample()
        for agent in env.agents
    }

    observations, rewards, terminations, truncations, infos = env.step(
        actions
    )


env.close()