"""
Database connection and management
"""

import asyncio
import logging
from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text

from config.settings import Settings

logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    """Base class for all database models"""
    pass

class Database:
    """Database connection manager"""
    
    def __init__(self):
        self.settings = Settings()
        self.engine = None
        self.session_factory = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize database connection"""
        if self._initialized:
            return
        
        logger.info("Initializing database connection...")
        
        try:
            # Create async engine
            self.engine = create_async_engine(
                self.settings.database.url,
                echo=self.settings.database.echo,
                pool_size=self.settings.database.pool_size,
                max_overflow=self.settings.database.max_overflow,
                pool_pre_ping=True,
                pool_recycle=3600
            )
            
            # Create session factory
            self.session_factory = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Test connection
            await self._test_connection()
            
            # Create tables
            await self._create_tables()
            
            self._initialized = True
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def _test_connection(self):
        """Test database connection"""
        async with self.engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.debug("Database connection test passed")
    
    async def _create_tables(self):
        """Create database tables"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.debug("Database tables created/updated")
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session context manager"""
        if not self._initialized:
            await self.initialize()
        
        async with self.session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def execute_query(self, query: str, params: dict = None):
        """Execute a raw SQL query"""
        async with self.get_session() as session:
            result = await session.execute(text(query), params or {})
            await session.commit()
            return result
    
    async def fetch_one(self, query: str, params: dict = None):
        """Fetch single row from query"""
        async with self.get_session() as session:
            result = await session.execute(text(query), params or {})
            return result.fetchone()
    
    async def fetch_all(self, query: str, params: dict = None):
        """Fetch all rows from query"""
        async with self.get_session() as session:
            result = await session.execute(text(query), params or {})
            return result.fetchall()
    
    def is_connected(self) -> bool:
        """Check if database is connected"""
        return self._initialized and self.engine is not None
    
    async def close(self):
        """Close database connection"""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connection closed")
    
    async def get_health_status(self) -> dict:
        """Get database health status"""
        try:
            if not self.is_connected():
                return {"status": "disconnected", "error": "Not initialized"}
            
            async with self.get_session() as session:
                result = await session.execute(text("SELECT 1"))
                result.fetchone()
                
                return {
                    "status": "healthy",
                    "url": self.settings.database.url.split('@')[-1] if '@' in self.settings.database.url else self.settings.database.url,
                    "pool_size": self.settings.database.pool_size,
                    "max_overflow": self.settings.database.max_overflow
                }
        
        except Exception as e:
            return {"status": "error", "error": str(e)}