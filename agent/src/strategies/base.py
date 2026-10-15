from abc import ABC, abstractmethod

Pose = tuple[int, int]


class SearchStrategy(ABC):
    @abstractmethod
    def search(self, start: Pose, target: Pose, neighbors) -> list[Pose]:
        pass
