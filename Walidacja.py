#pip install -r requirements.txt

from Tools import IFCValidator
import ifcopenshell.validate

paths = [r"SEGMENT.ifc",r"ANTENA.ifc"]

"Sprawdzam poprawność struktury pliku IFC"
for i in paths:


    model = ifcopenshell.open(i)
    logger = ifcopenshell.validate.json_logger()

    ifcopenshell.validate.validate(model, logger)

    if len(logger.statements)>0:
        print(f"Issiues in {i}:")
        for error in logger.statements:
            print(error)

"Sprawdzam brakujące atrybuty, na przykładzie Name"
for i in paths:

    validator = IFCValidator(ifcopenshell.open(i))
    missing_names = validator.check_missing_attribute("Name")
    if len(missing_names)>0:
        print(f"Missing names in {i}:")
        for element in missing_names[:5]:
            print(
                element.id(),
                element.is_a(),
                element.GlobalId
            )
