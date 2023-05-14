class TableMixin:
    """
    Mixin to filter aux table in DetailView
    """

    object_table_field: str
    filterset: type
    table: type

    def get_table_qs(self, request, instance):
        return getattr(instance, self.object_table_field).all()

    def get_table_data(self, request, instance):
        qs = self.get_table_qs(request, instance)
        return self.filterset(request.GET, qs, request=request).qs

    def get_table(self, request, instance):
        return self.table(self.get_table_data(request, instance))

    def configure_table(self, request, table, instance):
        table.configure(request)

    def get_extra_context(self, request, instance):
        table = self.get_table(request, instance)
        self.configure_table(request, table, instance)
        return {"table": table, "search_value": request.GET.get("q", "")}
