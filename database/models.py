from datetime import datetime
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

    async def get_user_stats(self, user_id: int) -> dict:
        """Get individual user statistics"""
        async with self.pool.acquire() as conn:
            joined_at = await conn.fetchval(
                "SELECT joined_at FROM users WHERE user_id = $1", user_id
            )
            commands_count = await conn.fetchval(
                "SELECT COUNT(*) FROM usage_stats WHERE user_id = $1", user_id
            )
            reminders_count = await conn.fetchval(
                "SELECT COUNT(*) FROM reminders WHERE user_id = $1", user_id
            )
            ai_count = await conn.fetchval(
                "SELECT COUNT(*) FROM usage_stats WHERE user_id = $1 AND command = 'ai'", user_id
            )
            weather_count = await conn.fetchval(
                "SELECT COUNT(*) FROM usage_stats WHERE user_id = $1 AND command = 'weather'", user_id
            )
            
            return {
                "joined_at": joined_at or datetime.now(),
                "commands_count": commands_count or 0,
                "reminders_count": reminders_count or 0,
                "ai_count": ai_count or 0,
                "weather_count": weather_count or 0
            }

    async def get_admin_stats(self) -> dict:
        """Get global stats for admin dashboard"""
        async with self.pool.acquire() as conn:
            users_count = await conn.fetchval("SELECT COUNT(*) FROM users")
            active_today = await conn.fetchval(
                "SELECT COUNT(*) FROM users WHERE last_active >= NOW() - INTERVAL '1 day'"
            )
            total_commands = await conn.fetchval("SELECT COUNT(*) FROM usage_stats")
            reminders_set = await conn.fetchval("SELECT COUNT(*) FROM reminders")
            ai_queries = await conn.fetchval(
                "SELECT COUNT(*) FROM usage_stats WHERE command = 'ai'"
            )
            weather_checks = await conn.fetchval(
                "SELECT COUNT(*) FROM usage_stats WHERE command = 'weather'"
            )
            
            return {
                "users": users_count or 0,
                "active_today": active_today or 0,
                "commands_used": total_commands or 0,
                "reminders_set": reminders_set or 0,
                "ai_queries": ai_queries or 0,
                "weather_checks": weather_checks or 0
            }

    async def get_active_reminders(self) -> list:
        """Get all active reminders to reschedule on startup"""
        async with self.pool.acquire() as conn:
            records = await conn.fetch("""
                SELECT id, user_id, message, remind_time, status
                FROM reminders
                WHERE status = 'active' AND remind_time > NOW()
            """)
            return [dict(r) for r in records]

    async def update_reminder_status(self, reminder_id: int, status: str, remind_time: datetime = None):
        """Update status or snooze time of a reminder"""
        async with self.pool.acquire() as conn:
            if remind_time:
                await conn.execute("""
                    UPDATE reminders
                    SET status = $2, remind_time = $3
                    WHERE id = $1
                """, reminder_id, status, remind_time)
            else:
                await conn.execute("""
                    UPDATE reminders
                    SET status = $2
                    WHERE id = $1
                """, reminder_id, status)