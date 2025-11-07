"""High-performance swarm integration backends."""
from __future__ import annotations

import math
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Sequence, Tuple

from .config import Config

Vector3 = Tuple[float, float, float]

if TYPE_CHECKING:
    from .lik import Lik


class BaseSwarmIntegrator(ABC):
    """Common interface for swarm integration backends."""

    def __init__(self, config: Config) -> None:
        self.config = config

    @abstractmethod
    def update(self, frame: int, liks: Sequence["Lik"], global_drift: Vector3) -> None:
        """Advance all liks in-place by one simulation step."""


class CpuSwarmIntegrator(BaseSwarmIntegrator):
    """Optimised CPU backend using pairwise force symmetrisation."""

    def update(self, frame: int, liks: Sequence["Lik"], global_drift: Vector3) -> None:  # noqa: D401
        swarm = self.config.swarm
        interaction = self.config.interaction
        fg = self.config.field_geometry

        count = len(liks)
        if count == 0:
            return

        gx, gy, gz = global_drift
        random_value = random.random
        migration = swarm.base_migration_speed

        forces_x = [gx + (random_value() - 0.5) * migration for _ in range(count)]
        forces_y = [gy + (random_value() - 0.5) * migration for _ in range(count)]
        forces_z = [gz + (random_value() - 0.5) * migration for _ in range(count)]

        positions_x = [lik.x for lik in liks]
        positions_y = [lik.y for lik in liks]
        positions_z = [lik.z for lik in liks]
        hues = [lik.hue for lik in liks]

        ps_radius = swarm.personal_space_radius
        ps_radius_sq = ps_radius * ps_radius
        ps_repulsion = swarm.personal_space_repulsion
        attraction_strength = swarm.attraction_strength
        repulsion_strength = swarm.repulsion_strength
        similarity_threshold = swarm.attraction_similarity_threshold

        for i in range(count - 1):
            xi = positions_x[i]
            yi = positions_y[i]
            zi = positions_z[i]
            hi = hues[i]
            fx_i = forces_x[i]
            fy_i = forces_y[i]
            fz_i = forces_z[i]
            for j in range(i + 1, count):
                dx = positions_x[j] - xi
                dy = positions_y[j] - yi
                dz = positions_z[j] - zi
                fx_j = forces_x[j]
                fy_j = forces_y[j]
                fz_j = forces_z[j]

                dist_sq = dx * dx + dy * dy + dz * dz
                if dist_sq < 1e-9:
                    continue

                inv_dist_sq = 1.0 / dist_sq

                if dist_sq < ps_radius_sq:
                    inv_dist = math.sqrt(inv_dist_sq)
                    dist = dist_sq * inv_dist
                    repulsion = ps_repulsion * (ps_radius - dist) * inv_dist
                    fx = dx * repulsion
                    fy = dy * repulsion
                    fz = dz * repulsion
                    fx_i -= fx
                    fy_i -= fy
                    fz_i -= fz
                    fx_j += fx
                    fy_j += fy
                    fz_j += fz
                diff = abs(hi - hues[j])
                if diff > 180.0:
                    diff = 360.0 - diff
                similarity = 1.0 - (diff / 180.0)
                if similarity > similarity_threshold:
                    strength = attraction_strength * similarity * inv_dist_sq
                    fx = dx * strength
                    fy = dy * strength
                    fz = dz * strength
                    fx_i += fx
                    fy_i += fy
                    fz_i += fz
                    fx_j -= fx
                    fy_j -= fy
                    fz_j -= fz
                else:
                    strength = repulsion_strength * (1.0 - similarity) * inv_dist_sq
                    fx = dx * strength
                    fy = dy * strength
                    fz = dz * strength
                    fx_i -= fx
                    fy_i -= fy
                    fz_i -= fz
                    fx_j += fx
                    fy_j += fy
                    fz_j += fz

                forces_x[j] = fx_j
                forces_y[j] = fy_j
                forces_z[j] = fz_j

            forces_x[i] = fx_i
            forces_y[i] = fy_i
            forces_z[i] = fz_i

        damping = interaction.global_drift_momentum
        radius = fg.universe_radius
        radius_sq = radius * radius

        for idx, lik in enumerate(liks):
            vx = (lik.vx + forces_x[idx]) * damping
            vy = (lik.vy + forces_y[idx]) * damping
            vz = (lik.vz + forces_z[idx]) * damping

            x = positions_x[idx] + vx
            y = positions_y[idx] + vy
            z = positions_z[idx] + vz

            dist_sq_center = x * x + y * y + z * z
            if dist_sq_center > radius_sq:
                dist_center = math.sqrt(dist_sq_center)
                clamp = radius / dist_center
                x *= clamp
                y *= clamp
                z *= clamp

            lik.vx = vx
            lik.vy = vy
            lik.vz = vz
            lik.x = x
            lik.y = y
            lik.z = z


@dataclass
class TorchBackendAvailability:
    torch: object
    device: str


def _resolve_torch_backend() -> TorchBackendAvailability | None:
    try:
        import torch  # type: ignore
    except ImportError:
        return None

    if torch.cuda.is_available():
        device = "cuda"
    else:
        device = "cpu"
    return TorchBackendAvailability(torch=torch, device=device)


class TorchSwarmIntegrator(BaseSwarmIntegrator):
    """Torch based backend leveraging GPU acceleration when possible."""

    def __init__(self, config: Config, torch_api: TorchBackendAvailability) -> None:
        super().__init__(config)
        self._torch = torch_api.torch
        self._device = torch_api.device

    def update(self, frame: int, liks: Sequence["Lik"], global_drift: Vector3) -> None:  # noqa: D401
        torch = self._torch
        swarm = self.config.swarm
        interaction = self.config.interaction
        fg = self.config.field_geometry

        count = len(liks)
        if count == 0:
            return

        positions = torch.tensor(
            [[lik.x, lik.y, lik.z] for lik in liks], dtype=torch.float32, device=self._device
        )
        velocities = torch.tensor(
            [[lik.vx, lik.vy, lik.vz] for lik in liks], dtype=torch.float32, device=self._device
        )
        hues = torch.tensor([lik.hue for lik in liks], dtype=torch.float32, device=self._device)

        drift = torch.tensor(global_drift, dtype=torch.float32, device=self._device)
        forces = drift.repeat(count, 1)

        migration = swarm.base_migration_speed
        rand = (torch.rand((count, 3), device=self._device) - 0.5) * migration
        forces += rand

        delta = positions.unsqueeze(1) - positions.unsqueeze(0)
        dist_sq = torch.sum(delta * delta, dim=-1)
        diag_mask = torch.eye(count, device=self._device, dtype=torch.bool)
        dist_sq = dist_sq.masked_fill(diag_mask, float("inf"))
        dist = torch.sqrt(dist_sq)

        dx = -delta  # match original (other - self)

        ps_radius = swarm.personal_space_radius
        mask_ps = dist < ps_radius
        repulsion = torch.zeros_like(dist)
        repulsion[mask_ps] = swarm.personal_space_repulsion * (
            ps_radius - dist[mask_ps]
        ) / dist[mask_ps]
        repulsion_vec = repulsion.unsqueeze(-1) * dx
        forces -= repulsion_vec.sum(dim=1)
        forces += repulsion_vec.sum(dim=0)

        # hue similarity matrix
        hi = hues.unsqueeze(1)
        hj = hues.unsqueeze(0)
        diff = torch.abs(hi - hj) % 360.0
        diff = torch.minimum(diff, 360.0 - diff)
        similarity = 1.0 - (diff / 180.0)

        attraction_mask = similarity > swarm.attraction_similarity_threshold
        attraction_strength = torch.zeros_like(dist)
        repulsion_strength = torch.zeros_like(dist)
        attraction_strength[attraction_mask] = (
            swarm.attraction_strength * similarity[attraction_mask] / dist_sq[attraction_mask]
        )
        repulsion_strength[~attraction_mask] = (
            swarm.repulsion_strength * (1.0 - similarity[~attraction_mask]) / dist_sq[~attraction_mask]
        )

        attraction_vec = attraction_strength.unsqueeze(-1) * dx
        repulsion_vec = repulsion_strength.unsqueeze(-1) * dx

        forces += attraction_vec.sum(dim=1)
        forces -= attraction_vec.sum(dim=0)
        forces -= repulsion_vec.sum(dim=1)
        forces += repulsion_vec.sum(dim=0)

        velocities = (velocities + forces) * interaction.global_drift_momentum
        positions = positions + velocities

        radius = fg.universe_radius
        dist_to_center = torch.sqrt(torch.sum(positions * positions, dim=-1))
        mask = dist_to_center > radius
        if torch.any(mask):
            factor = radius / dist_to_center[mask]
            positions[mask] = positions[mask] * factor.unsqueeze(-1)

        new_positions = positions.detach().cpu().tolist()
        new_velocities = velocities.detach().cpu().tolist()

        for idx, lik in enumerate(liks):
            lik.x, lik.y, lik.z = new_positions[idx]
            lik.vx, lik.vy, lik.vz = new_velocities[idx]


class SwarmIntegrator(BaseSwarmIntegrator):
    """Facade that selects the most capable backend available."""

    def __init__(self, config: Config) -> None:
        torch_backend = _resolve_torch_backend()
        if torch_backend is not None:
            self._delegate: BaseSwarmIntegrator = TorchSwarmIntegrator(config, torch_backend)
        else:
            self._delegate = CpuSwarmIntegrator(config)

    def update(self, frame: int, liks: Sequence["Lik"], global_drift: Vector3) -> None:  # noqa: D401
        self._delegate.update(frame, liks, global_drift)


__all__ = [
    "BaseSwarmIntegrator",
    "CpuSwarmIntegrator",
    "SwarmIntegrator",
]
