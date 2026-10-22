from abc import ABC, abstractmethod

Pose = tuple[int, int]


class SearchStrategy(ABC):
    @abstractmethod
    def search(self, start: Pose, target: Pose, neighbors) -> list[Pose]:
        pass
    
    def _record(self, stored: int, peak_frontier: int) -> None:
        """Proxy mémoire: taille du dict principal + pic de la frontière (file, pile ou tas)."""
        self.stats = {"stored": stored, "peak_frontier": peak_frontier}
        
        