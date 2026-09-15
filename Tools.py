class IFCValidator:

    def __init__(self, model):
        self.model = model

    def check_missing_attribute(self, attribute, ifc_type="IfcElement"):
        missing = []

        for element in self.model.by_type(ifc_type):
            value = getattr(element, attribute, None)

            if value is None or not str(value).strip():
                missing.append(element)

        return missing