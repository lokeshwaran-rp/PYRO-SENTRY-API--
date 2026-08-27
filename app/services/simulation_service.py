import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from app.schemas.simulation import (
    SimulationStartRequest,
    SimulationStatusResponse,
    SimulationStopResponse,
    SimulationStepData,
)
from app.simulation.engine import SimulationEngine
from app.realtime.connection_manager import manager

logger = logging.getLogger(__name__)


class SimulationService:
    """
    Manages active fire spread simulations, background execution tasks,
    and real-time streaming of simulation frames to WebSocket clients.
    """

    def __init__(self):
        self._is_running: bool = False
        self._current_sim_id: Optional[str] = None
        self._step_count: int = 0
        self._max_steps: int = 0
        self._started_at: Optional[datetime] = None
        self._latest_step: Optional[SimulationStepData] = None
        self._task: Optional[asyncio.Task] = None

    def get_status(self) -> SimulationStatusResponse:
        """Return the current status of the simulation service."""
        return SimulationStatusResponse(
            is_running=self._is_running,
            current_simulation_id=self._current_sim_id,
            step_count=self._step_count,
            max_steps=self._max_steps,
            started_at=self._started_at,
            latest_step=self._latest_step,
        )

    async def start_simulation(self, request: SimulationStartRequest) -> SimulationStatusResponse:
        """
        Start a new background simulation loop.
        If a simulation is already running, it stops the existing one first.
        """
        if self._is_running:
            await self.stop_simulation()

        sim_id = request.simulation_id or f"sim-{uuid.uuid4().hex[:8]}"
        self._is_running = True
        self._current_sim_id = sim_id
        self._step_count = 0
        self._max_steps = request.max_steps
        self._started_at = datetime.now(timezone.utc)
        self._latest_step = None

        # Spawn background runner task
        self._task = asyncio.create_task(
            self._run_simulation_loop(
                sim_id=sim_id,
                request=request,
            )
        )

        return self.get_status()

    async def _run_simulation_loop(self, sim_id: str, request: SimulationStartRequest):
        """Internal background async task to step through simulation and broadcast updates."""
        try:
            logger.info(f"Starting simulation run {sim_id}")
            for step_num in range(1, request.max_steps + 1):
                if not self._is_running or self._current_sim_id != sim_id:
                    break

                # Generate step from simulation engine
                step_data = SimulationEngine.generate_step(
                    simulation_id=sim_id,
                    step_number=step_num,
                    origin_lat=request.latitude,
                    origin_lon=request.longitude,
                    wind_speed_kmh=request.wind_speed_kmh,
                    wind_direction_deg=request.wind_direction_deg,
                )

                self._step_count = step_num
                self._latest_step = step_data

                # Stream to WebSocket clients
                await manager.broadcast_json({
                    "type": "SIMULATION_STEP",
                    "data": step_data.model_dump(mode="json"),
                })

                # Wait for configured step interval
                await asyncio.sleep(request.step_interval_seconds)

            logger.info(f"Simulation run {sim_id} completed all {self._step_count} steps.")
        except asyncio.CancelledError:
            logger.info(f"Simulation run {sim_id} was cancelled.")
        except Exception as exc:
            logger.error(f"Simulation run {sim_id} encountered an error: {exc}", exc_info=True)
        finally:
            if self._current_sim_id == sim_id:
                self._is_running = False

    async def stop_simulation(self) -> SimulationStopResponse:
        """Stop the currently active simulation."""
        old_id = self._current_sim_id
        completed_steps = self._step_count

        self._is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        self._current_sim_id = None

        # Notify realtime clients that simulation ended
        await manager.broadcast_json({
            "type": "SIMULATION_STOPPED",
            "simulation_id": old_id,
            "completed_steps": completed_steps,
        })

        return SimulationStopResponse(
            message="Simulation stopped successfully",
            simulation_id=old_id,
            steps_completed=completed_steps,
        )


# Global singleton instance
simulation_service = SimulationService()
