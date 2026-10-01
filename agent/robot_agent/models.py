from dataclasses import dataclass, field

Node = tuple[int, int]

@dataclass(frozen=True) #Frozen because the Agent don't need to modify it
class Problem:
        """All what the Agents knows about his mission (from GET /state)."""
        agent: str
        start: Node
        target: Node
        threshold: float
        size: int
        connectivity: int
        
        
@dataclass
class SearchResult:
    """Return from the algorithm:"""
    algo: str
    found: bool
    path: list[Node] = field(default_factory=list)
    cost: float = 0.0          # theoric cost
    expanded: int = 0          
    api_calls: int = 0
    elapsed: float = 0.0       