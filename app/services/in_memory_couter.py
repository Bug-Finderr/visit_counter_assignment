from typing import Dict


class VisitCounterService:
    _visit_counter: Dict[str, int] = {}

    async def increment_visit(self, page_id: str) -> None:
        """
        Increment visit count for a page

        Args:
            page_id: Unique identifier for the page
        """
        self.__class__._visit_counter[page_id] = (
            self.__class__._visit_counter.get(page_id, 0) + 1
        )

    async def get_visit_count(self, page_id: str) -> int:
        """
        Get current visit count for a page

        Args:
            page_id: Unique identifier for the page

        Returns:
            Current visit count
        """
        return self.__class__._visit_counter.get(page_id, 0)
