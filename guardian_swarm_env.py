from __future__ import annotations

import math
from typing import Dict

import numpy as np
import pybullet as p

from gymnasium.spaces import Box
from pettingzoo import ParallelEnv
from PyFlyt.core import Aviary

from constants import (
    ATTACKER_SPAWNS,
    BASE_DETECTION_RANGE,
    CONTROL_REPEAT,
    DEFENDER_SPAWNS,
    ENV_METADATA,
    INTERCEPT_RADIUS,
    MAX_ALTITUDE,
    MAX_HORIZONTAL_SPEED,
    MAX_STEPS,
    MAX_VERTICAL_SPEED,
    MAX_YAW_RATE,
    MAP_HALF_SIZE,
    NUM_AGENTS,
    NUM_ATTACKERS,
    NUM_DEFENDERS,
    OBS_DIM,
    POI_NAMES,
    TARGET_RADIUS,
    WEATHER_CONFIG,
    WEATHER_NAMES,
)

from map_config import (building_specification,poi_specification,road_specification,)


class GuardianSwarmEnv(ParallelEnv):
    """
    GuardianSwarm V1.1

    Updates:
    - Bigger map
    - Wider roads / clearer city structure
    - More open space for flight
    - Explicit road visuals
    - Mixed open + narrow urban routes

    Multi-agent setup:
    - 3 attackers
    - 3 defenders

    POIs:
    - hospital
    - defence base
    - power plant
    - communication centre
    - tourist site

    Episode randomization:
    - POI values are randomized each reset
    - weather is randomized each reset

    Action (normalized):
        [vx, vy, yaw_rate, vz] in [-1, 1]

    Internally mapped to PyFlyt QuadX mode 6:
        [vx, vy, yaw_rate, vz]
    """

    metadata = ENV_METADATA

    # ==============================================================
    # INIT
    # ==============================================================

    def __init__(self, render_mode=None):
        super().__init__()

        self.render_mode = render_mode

        self.possible_agents = (
            [f"attacker_{i}" for i in range(NUM_ATTACKERS)] +
            [f"defender_{i}" for i in range(NUM_DEFENDERS)]
        )
        self.agents = self.possible_agents.copy()

        self.attacker_agents = [f"attacker_{i}" for i in range(NUM_ATTACKERS)]
        self.defender_agents = [f"defender_{i}" for i in range(NUM_DEFENDERS)]

        self.agent_to_drone = {
            agent: i for i, agent in enumerate(self.possible_agents)
        }

        self.start_pos = np.vstack([ATTACKER_SPAWNS, DEFENDER_SPAWNS])
        self.start_orn = np.zeros_like(self.start_pos)

        self._action_space = Box(
            low=-1.0,
            high=1.0,
            shape=(4,),
            dtype=np.float32,
        )

        self.obs_dim = OBS_DIM
        self._observation_space = Box(
            low=-1e4,
            high=1e4,
            shape=(self.obs_dim,),
            dtype=np.float32,
        )

        self.aviary = None
        self.step_count = 0
        self.intercepted_attackers = set()
        self.np_random = np.random.default_rng()

    # ==============================================================
    # PETTINGZOO API
    # ==============================================================

    def action_space(self, agent):
        return self._action_space

    def observation_space(self, agent):
        return self._observation_space

    # ==============================================================
    # BULLET HELPERS
    # ==============================================================

    def _create_box_body(self, xy, size, colour, collidable=True):
        width, depth, height = size
        half_extents = [width / 2, depth / 2, height / 2]

        collision_id = -1
        if collidable:
            collision_id = self.aviary.createCollisionShape(
                shapeType=p.GEOM_BOX,
                halfExtents=half_extents,
            )

        visual_id = self.aviary.createVisualShape(
            shapeType=p.GEOM_BOX,
            halfExtents=half_extents,
            rgbaColor=colour,
        )

        body_id = self.aviary.createMultiBody(
            baseMass=0.0,
            baseCollisionShapeIndex=collision_id,
            baseVisualShapeIndex=visual_id,
            basePosition=[xy[0], xy[1], height / 2],
        )

        return body_id

    def _create_building(self, spec):
        body_id = self._create_box_body(
            xy=spec["xy"],
            size=spec["size"],
            colour=spec["colour"],
            collidable=True,
        )

        if self.render_mode == "human":
            height = spec["size"][2]
            self.aviary.addUserDebugText(
                text=spec["name"].replace("_", " ").upper(),
                textPosition=[spec["xy"][0], spec["xy"][1], height + 1.5],
                textColorRGB=[1, 1, 1],
                textSize=1.0,
            )

        return body_id

    def _create_road(self, spec):
        width, depth, _ = spec["size"]

        visual_id = self.aviary.createVisualShape(
            shapeType=p.GEOM_BOX,
            halfExtents=[width / 2, depth / 2, 0.025],
            rgbaColor=spec["colour"],
        )

        road_id = self.aviary.createMultiBody(
            baseMass=0.0,
            baseCollisionShapeIndex=-1,
            baseVisualShapeIndex=visual_id,
            basePosition=[spec["xy"][0], spec["xy"][1], 0.025],
        )

        return road_id

    def _create_target_marker(self, position, colour):
        visual = self.aviary.createVisualShape(
            shapeType=p.GEOM_SPHERE,
            radius=TARGET_RADIUS,
            rgbaColor=[colour[0], colour[1], colour[2], 0.30],
        )

        return self.aviary.createMultiBody(
            baseMass=0,
            baseCollisionShapeIndex=-1,
            baseVisualShapeIndex=visual,
            basePosition=position,
        )

    def _build_map(self):
        self.building_ids = []
        self.road_ids = []
        self.poi_body_ids = {}
        self.poi_positions = {}

        for road in road_specification():
            road_id = self._create_road(road)
            self.road_ids.append(road_id)

        for spec in poi_specification():
            body_id = self._create_building(spec)
            self.building_ids.append(body_id)

            _, _, height = spec["size"]
            target_position = np.array(
                [spec["xy"][0], spec["xy"][1], height + 4.0],
                dtype=np.float32,
            )

            self.poi_body_ids[spec["name"]] = body_id
            self.poi_positions[spec["name"]] = target_position

            self._create_target_marker(target_position, spec["colour"])

        for spec in building_specification():
            body_id = self._create_building(spec)
            self.building_ids.append(body_id)

        self.aviary.register_all_new_bodies()

        if self.render_mode == "human":
            self.aviary.resetDebugVisualizerCamera(
                cameraDistance=145,
                cameraYaw=45,
                cameraPitch=-58,
                cameraTargetPosition=[0, 0, 6],
            )

    # ==============================================================
    # WEATHER
    # ==============================================================

    def _randomize_weather(self):
        self.weather = self.np_random.choice(WEATHER_NAMES)
        cfg = WEATHER_CONFIG[self.weather]

        self.sensor_multiplier = cfg["sensor_multiplier"]

        angle = self.np_random.uniform(0, 2 * math.pi)
        self.wind_direction = np.array(
            [math.cos(angle), math.sin(angle), 0.0],
            dtype=np.float32,
        )

        self.wind_base = cfg["base_wind"]
        self.wind_gust = cfg["gust"]
        self.wind_phase = self.np_random.uniform(0, 2 * math.pi)

        def wind_field(time, positions):
            positions = np.asarray(positions)

            speed = self.wind_base + self.wind_gust * math.sin(0.7 * time + self.wind_phase)
            vector = self.wind_direction * speed

            return np.broadcast_to(vector, positions.shape).copy()

        self.wind_field = wind_field
        self.aviary.register_wind_field_function(self.wind_field)

    def _current_wind(self):
        pos = np.zeros((1, 3))
        return self.wind_field(self.aviary.elapsed_time, pos)[0]

    # ==============================================================
    # POI VALUES / TARGETS
    # ==============================================================

    def _randomize_poi_values(self):
        values = self.np_random.integers(low=1, high=6, size=len(POI_NAMES))
        self.poi_values = {
            poi: float(value)
            for poi, value in zip(POI_NAMES, values)
        }

    def _assign_targets(self):
        self.attacker_targets = {}
        for attacker in self.attacker_agents:
            target_index = int(self.np_random.integers(0, len(POI_NAMES)))
            self.attacker_targets[attacker] = target_index

    # ==============================================================
    # RESET
    # ==============================================================

    def reset(self, seed=None, options=None):
        if seed is not None:
            self.np_random = np.random.default_rng(seed)

        self.agents = self.possible_agents.copy()
        self.step_count = 0
        self.intercepted_attackers = set()

        if self.aviary is None:
            drone_options = [
                {
                    "control_hz": 120,
                    "use_camera": False,
                }
                for _ in self.possible_agents
            ]

            self.aviary = Aviary(
                start_pos=self.start_pos,
                start_orn=self.start_orn,
                drone_type=["quadx"] * NUM_AGENTS,
                drone_options=drone_options,
                render=(self.render_mode == "human"),
                physics_hz=240,
            )
        else:
            self.aviary.reset()

        self.aviary.set_mode(6)

        self._build_map()
        self._randomize_poi_values()
        self._randomize_weather()
        self._assign_targets()

        observations = {
            agent: self._get_observation(agent)
            for agent in self.agents
        }

        infos = {
            agent: self._get_info(agent)
            for agent in self.agents
        }

        return observations, infos

    # ==============================================================
    # DRONE STATE
    # ==============================================================

    def _world_state(self, agent):
        drone_idx = self.agent_to_drone[agent]
        body_id = self.aviary.drones[drone_idx].Id

        position, _ = self.aviary.getBasePositionAndOrientation(body_id)
        linear_velocity, _ = self.aviary.getBaseVelocity(body_id)

        return (
            np.asarray(position, dtype=np.float32),
            np.asarray(linear_velocity, dtype=np.float32),
        )

    # ==============================================================
    # OBSERVATION
    # ==============================================================

    def _get_observation(self, agent):
        own_pos, own_vel = self._world_state(agent)
        obs = []

        obs.extend(own_pos)
        obs.extend(own_vel)

        detection_range = BASE_DETECTION_RANGE * self.sensor_multiplier

        for other_agent in self.possible_agents:
            if other_agent == agent:
                continue

            other_pos, other_vel = self._world_state(other_agent)
            relative_pos = other_pos - own_pos
            relative_vel = other_vel - own_vel

            distance = np.linalg.norm(relative_pos)
            visible = float(distance <= detection_range)

            if visible:
                obs.extend(relative_pos)
                obs.extend(relative_vel)
            else:
                obs.extend([0.0, 0.0, 0.0])
                obs.extend([0.0, 0.0, 0.0])

            obs.append(visible)

        for poi in POI_NAMES:
            relative_poi = self.poi_positions[poi] - own_pos
            obs.extend(relative_poi)
            obs.append(self.poi_values[poi] / 5.0)

        target_one_hot = np.zeros(len(POI_NAMES), dtype=np.float32)
        if agent.startswith("attacker"):
            target_index = self.attacker_targets[agent]
            target_one_hot[target_index] = 1.0
        obs.extend(target_one_hot)

        weather_one_hot = np.zeros(len(WEATHER_NAMES), dtype=np.float32)
        weather_index = WEATHER_NAMES.index(self.weather)
        weather_one_hot[weather_index] = 1.0
        obs.extend(weather_one_hot)

        obs.extend(self._current_wind())

        observation = np.asarray(obs, dtype=np.float32)
        assert observation.shape == (self.obs_dim,), observation.shape
        return observation

    # ==============================================================
    # STEP
    # ==============================================================

    def step(self, actions: Dict[str, np.ndarray]):
        active_agents = self.agents.copy()

        setpoints = np.zeros((NUM_AGENTS, 4), dtype=np.float32)

        for agent in active_agents:
            idx = self.agent_to_drone[agent]

            if agent in self.intercepted_attackers:
                continue

            action = np.clip(actions[agent], -1.0, 1.0)

            vx = action[0] * MAX_HORIZONTAL_SPEED
            vy = action[1] * MAX_HORIZONTAL_SPEED
            yaw_rate = action[2] * MAX_YAW_RATE
            vz = action[3] * MAX_VERTICAL_SPEED

            setpoints[idx] = [vx, vy, yaw_rate, vz]

        self.aviary.set_all_setpoints(setpoints)

        for _ in range(CONTROL_REPEAT):
            self.aviary.step()

        self.step_count += 1

        rewards = {agent: -0.001 for agent in active_agents}
        episode_finished = False

        for attacker in self.attacker_agents:
            if attacker in self.intercepted_attackers:
                continue

            attacker_pos, _ = self._world_state(attacker)

            for defender in self.defender_agents:
                defender_pos, _ = self._world_state(defender)

                distance = np.linalg.norm(attacker_pos - defender_pos)
                if distance < INTERCEPT_RADIUS:
                    self.intercepted_attackers.add(attacker)

                    target_idx = self.attacker_targets[attacker]
                    target_name = POI_NAMES[target_idx]
                    value = self.poi_values[target_name]

                    for defender_agent in self.defender_agents:
                        rewards[defender_agent] += value

                    rewards[attacker] -= value
                    break

        for attacker in self.attacker_agents:
            if attacker in self.intercepted_attackers:
                continue

            attacker_pos, _ = self._world_state(attacker)
            target_idx = self.attacker_targets[attacker]
            target_name = POI_NAMES[target_idx]
            target_pos = self.poi_positions[target_name]

            distance = np.linalg.norm(attacker_pos - target_pos)
            if distance <= TARGET_RADIUS:
                value = self.poi_values[target_name]

                for attacker_agent in self.attacker_agents:
                    rewards[attacker_agent] += value

                for defender_agent in self.defender_agents:
                    rewards[defender_agent] -= value

                episode_finished = True
                break

        if len(self.intercepted_attackers) == NUM_ATTACKERS:
            episode_finished = True

        for agent in active_agents:
            pos, _ = self._world_state(agent)

            outside_map = (
                abs(pos[0]) > MAP_HALF_SIZE or
                abs(pos[1]) > MAP_HALF_SIZE or
                pos[2] < 0.5 or
                pos[2] > MAX_ALTITUDE
            )

            if outside_map:
                rewards[agent] -= 2.0

        timeout = self.step_count >= MAX_STEPS

        terminations = {
            agent: episode_finished for agent in active_agents
        }
        truncations = {
            agent: timeout for agent in active_agents
        }

        observations = {
            agent: self._get_observation(agent)
            for agent in active_agents
        }
        infos = {
            agent: self._get_info(agent)
            for agent in active_agents
        }

        if episode_finished or timeout:
            self.agents = []

        return observations, rewards, terminations, truncations, infos

    # ==============================================================
    # INFO
    # ==============================================================

    def _get_info(self, agent):
        info = {
            "weather": self.weather,
            "poi_values": self.poi_values.copy(),
            "intercepted_attackers": len(self.intercepted_attackers),
        }

        if agent.startswith("attacker"):
            target_idx = self.attacker_targets[agent]
            info["target"] = POI_NAMES[target_idx]

        return info

    # ==============================================================
    # RENDER / CLOSE
    # ==============================================================

    def render(self):
        pass

    def close(self):
        if self.aviary is not None:
            self.aviary.close()
            self.aviary = None