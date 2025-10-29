from typing import TypeVar, Generic, List, Optional, Callable, Iterator
from objects.idrawableobject import InteractDrawableObject

T = TypeVar('T', bound='InteractDrawableObject')

class NotifyObjectCollection(list, Generic[T]):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.added_item: Optional[Callable[['NotifyObjectCollection[T]', T], None]] = None
        self.cleared_collection: Optional[Callable[['NotifyObjectCollection[T]', None], None]] = None

    def add(self, item: T) -> None:
        self.append(item)
        self.notify_added_item(item)

    def clear(self) -> None:
        super().clear()
        if self.cleared_collection is not None:
            self.cleared_collection(self, None)

    def notify_added_item(self, item: T) -> None:
        if self.added_item is not None:
            self.added_item(self, item)

    def __iter__(self) -> Iterator[T]:
        return super().__iter__()