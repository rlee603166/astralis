from search.config import neo_config
from neo4j import AsyncGraphDatabase

class NeoManager:
    def __init__(self):
        self.neo_uri = neo_config.NEO4J_URI
        self.neo_username = neo_config.NEO4J_USERNAME
        self.neo_password = neo_config.NEO4J_PASSWORD
        self.instance_id = neo_config.AURA_INSTANCEID
        self.instance_name = neo_config.AURA_INSTANCENAME

    def _get_driver(self):
        _driver = AsyncGraphDatabase.driver(
            self.neo_uri,
            auth=(self.neo_username, self.neo_password)
        )
        return _driver
