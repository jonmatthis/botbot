from pydantic import BaseModel

from jonbot.models.context_route import ContextRoute


class CalculateMemoryRequest(BaseModel):
    context_route: ContextRoute
    database_name: str
    limit_messages: int = None
