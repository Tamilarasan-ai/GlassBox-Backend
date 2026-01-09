"""Startup utilities for syncing configuration"""
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent
from app.core.config import settings

logger = logging.getLogger(__name__)


async def sync_agent_model_config(db: AsyncSession) -> None:
    """
    Sync agent model configuration with environment settings
    
    Called on application startup to ensure database reflects current .env settings
    """
    target_config = {
        "model": settings.LLM_MODEL,
        "temperature": 0.1
    }
    
    result = await db.execute(select(Agent))
    agents = result.scalars().all()
    
    updated_count = 0
    for agent in agents:
        # Check if config needs update
        if agent.model_config != target_config:
            old_config = agent.model_config.copy() if agent.model_config else {}
            agent.model_config = target_config
            updated_count += 1
            
            logger.info(
                f"Updated agent '{agent.slug}' model config: "
                f"{old_config.get('model', 'unknown')} → {target_config['model']}"
            )
    
    if updated_count > 0:
        await db.commit()
        logger.info(f"✅ Synced {updated_count} agent(s) with .env model configuration")
    else:
        logger.debug("Agent model configs already in sync with .env")
