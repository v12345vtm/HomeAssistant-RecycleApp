from datetime import date
from fostplus_api import FostPlusApi


def main():
    postcode = int(input("Postcode: "))
    street = input("Street: ")
    house_number = int(input("House number: "))
    language = input("Language (nl/fr/en): ") or "nl"

    api = FostPlusApi()

    zip_id, zip_name = api.get_zip_code(postcode, language)[0]
    street_id, street_name = api.get_street(street, zip_id, language)

    collections = api.get_collections(zip_id, street_id, house_number)

    print(f"\nAddress: {street_name} {house_number}, {zip_name}\n")

    for fraction, dates in collections.items():
        dates.sort()
        print(f"{fraction.upper()}:")
        for d in dates[:10]:
            print(" ", d)
        print()


if __name__ == "__main__":
    main()
