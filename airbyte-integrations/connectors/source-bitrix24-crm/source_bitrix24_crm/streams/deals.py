from .base import ObjectListStream


class Deals(ObjectListStream):
    def path(self, **kwargs) -> str:
        return "crm.deal.list"
