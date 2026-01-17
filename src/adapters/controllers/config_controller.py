"""Configuration controller (MVC)."""
from typing import Any, Dict
from ...infrastructure.database import Database


class ConfigController:
    """Controller for configuration management."""

    def __init__(self, database: Database):
        """Initialize controller."""
        self.database = database

    async def get_config(self, key: str) -> Any:
        """Get a configuration value."""
        return await self.database.get_config(key)

    async def set_config(self, key: str, value: Any, category: str = "general") -> None:
        """Set a configuration value."""
        await self.database.set_config(key, value, category)

    async def get_all_configs(self) -> Dict[str, Any]:
        """Get all configurations."""
        return await self.database.get_all_configs()

    async def update_configs(self, configs: Dict[str, Any]) -> None:
        """Update multiple configurations."""
        for key, value in configs.items():
            await self.database.set_config(key, value)

    async def reset_to_defaults(self) -> None:
        """Reset configurations to defaults."""
        await self.database.seed_default_configs()
