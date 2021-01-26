import aiomysql

class Queries():
    def __init__(self, config):
        self.config = config
        
    async def execute(self, query: str):
        pool = await aiomysql.create_pool(host=self.config["db_host"], port=self.config["db_port"], user=self.config["db_user"], password=self.config["db_pass"], db=self.config["db_dbname"])
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query)
                r = await cursor.fetchall()
        pool.close()
        await pool.wait_closed()
        return r