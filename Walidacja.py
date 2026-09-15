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
        print(f"Problemy w {i}:\n")
        for error in logger.statements:
            print(error)
        print("\n")

"Sprawdzam brakujące atrybuty, na przykładzie Name"
for i in paths:

    validator = IFCValidator(ifcopenshell.open(i))
    missing_names = validator.check_missing_attribute("Name")
    if len(missing_names)>0:
        print(f"Brakujące nazwy w {i}:\n")
        for element in missing_names:
            print(
                element.id(),
                element.is_a(),
                element.GlobalId
            )
        print("\n")

"Szukam zduplikowanych atrybutów jak np. Guid"

for i in paths:
    validator = IFCValidator(ifcopenshell.open(i))
    duplicates = validator.check_duplicate_attribute("GlobalId")

    print(f"Liczba duplikatów w {i}: {len(duplicates)}\n")

    for value, elements in duplicates.items():
        print(f"{value}\n")

        for element in elements:
            print(
                element.id(),
                element.is_a(),
                element.Name
            )
        print("\n")

"Sprawdzam poprawność przypisania poziomów"

for i in paths:
    validator = IFCValidator(ifcopenshell.open(i))
    wrong, intersecting = validator.check_element_levels()

    print(f"Błędnie przypisane w {i}: {len(wrong)}")
    print(f"Przecinające level w {i}: {len(intersecting)}")

    for item in intersecting:
        element = item["element"]

        print(
            element.id(),
            element.is_a(),
            element.GlobalId,
            "Level:", item["level"],
            "Element Z:",
            item["element_min_z"],
            "-",
            item["element_max_z"]
        )
