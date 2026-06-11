from datetime import datetime
from typing import Optional
import asyncpg

class Database:
    """Database manager for PostgreSQL"""
    
    def __init__(self, dsn: str):
        self.dsn = dsn
        self.pool = None
    
    async def connect(self):
        """Create connection pool"""
        self.pool = await asyncpg.create_pool(self.dsn)
        await self.create_tables()
    
    async def create_tables(self):
        """Create all tables"""
        async with self.pool.acquire() as conn:
            # Users table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    username VARCHAR(255),
                    first_name VARCHAR(255),
                    last_name VARCHAR(255),
                    joined_at TIMESTAMP DEFAULT NOW(),
                    last_active TIMESTAMP,
                    is_premium BOOLEAN DEFAULT FALSE,
                    is_admin BOOLEAN DEFAULT FALSE
                )
            """)
            
            # Reminders table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS reminders (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id),
                    message TEXT,
                    remind_time TIMESTAMP,
                    created_at TIMESTAMP DEFAULT NOW(),
                    status VARCHAR(50) DEFAULT 'active'
                )
            """)
            
            # Feedback table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id),
                    message TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Usage stats table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS usage_stats (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id),
                    command VARCHAR(100),
                    used_at TIMESTAMP DEFAULT NOW()
                )
            """)
    
    async def add_user(self, user_id: int, username: str = None, 
                       first_name: str = None, last_name: str = None):
        """Add or update user"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO users (user_id, username, first_name, last_name, last_active)
                VALUES ($1, $2, $3, $4, NOW())
                ON CONFLICT (user_id) DO UPDATE SET
                    username = EXCLUDED.username,
                    first_name = EXCLUDED.first_name,
                    last_name = EXCLUDED.last_name,
                    last_active = NOW()
            """, user_id, username, first_name, last_name)
    
    async def add_reminder(self, user_id: int, message: str, remind_time: datetime):
        """Add reminder to database"""
        async with self.pool.acquire() as conn:
            return await conn.fetchval("""
                INSERT INTO reminders (user_id, message, remind_time)
                VALUES ($1, $2, $3)
                RETURNING id
            """, user_id, message, remind_time)
    
    async def add_feedback(self, user_id: int, message: str):
        """Add feedback to database"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO feedback (user_id, message)
                VALUES ($1, $2)
            """, user_id, message)
    
    async def log_command(self, user_id: int, command: str):
        """Log command usage"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO usage_stats (user_id, command)
                VALUES ($1, $2)
            """, user_id, command)