from pydantic import BaseModel, Field
from typing import List

class Entity(BaseModel):
    name: str = Field(..., description="The name of the entity")
    attributes: List[str] = Field(..., description="List of attributes associated with the entity")

class EntityList(BaseModel):
    entities: List[Entity] = Field(..., description="List of entities identified in the response")

class Relationship(BaseModel):
    source: str = Field(..., description="The source entity of the relationship")
    target: str = Field(..., description="The target entity of the relationship")
    type: str = Field(..., description="The type of relationship (e.g., 'one-to-many', 'many-to-many')")

class RelationshipList(BaseModel):
    relationships: List[Relationship] = Field(..., description="List of relationships between entities")

class Response(BaseModel):
    entity: EntityList
    relationships: RelationshipList

    