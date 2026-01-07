"""FostPlus API."""

from collections import defaultdict
from datetime import date, datetime, timedelta

from requests import Session

from const import FRACTION_MAP


class FostPlusApi:
    __session: Session | None = None
    __endpoint: str

    def __ensure_initialization(self):
        if self.__session:
            return

        self.__session = Session()
        self.__session.headers.update(
            {
                "Accept": "application/json, text/plain, */*",
                "Accept-Encoding": "gzip, deflate",
                "User-Agent": "HomeAssistant-RecycleApp",
                "x-consumer": "recycleapp.be",
            }
        )

        base_url = self.__session.get(
            "https://www.recycleapp.be/config/app.settings.json"
        ).json()["API"]
        self.__endpoint = f"{base_url}/public/v1"
        #print(self.__endpoint)

    def __get(self, action: str):
        self.__ensure_initialization()
        print("REQUEST URL:", f"{self.__endpoint}/{action}")

        for _ in range(2):
            r = self.__session.get(f"{self.__endpoint}/{action}")
            if r.status_code == 200:
                return r.json()
        return {}

    def __post(self, action: str, data=None):
        self.__ensure_initialization()
        for _ in range(2):
            r = self.__session.post(f"{self.__endpoint}/{action}", json=data)
            if r.status_code == 200:
                return r.json()
        return {}

    def get_zip_code(self, zip_code: int, language: str = "nl"):
        result = self.__get(f"zipcodes?q={zip_code}")
        return [
            (item["id"], f'{item["code"]} - {name[language]}')
            for item in result.get("items", [])
            for name in item.get("names", [])
        ]

    def get_street(self, street: str, zip_code_id: str, language: str = "nl"):
        street = street.strip().lower()
        result = self.__post(f"streets?q={street}&zipcodes={zip_code_id}")

        if result.get("total") != 1:
            for item in result.get("items", []):
                if item["names"][language].strip().lower() == street:
                    return item["id"], item["names"][language]
            raise Exception("invalid_streetname")

        item = result["items"][0]
        return item["id"], item["names"][language]

    # ✅ THIS METHOD IS INSIDE THE CLASS (IMPORTANT)
    def get_collections(
        self,
        zip_code_id,
        street_id,
        house_number,
        from_date=None,
        until_date=None,
        size=100,
    ):
        if not from_date:
            from_date = datetime.now()
        if not until_date:
            until_date = from_date + timedelta(weeks=26)

        result = defaultdict(list)

        response = self.__get(
            f"collections?"
            f"zipcodeId={zip_code_id}&streetId={street_id}"
            f"&houseNumber={house_number}"
            f"&fromDate={from_date:%Y-%m-%d}"
            f"&untilDate={until_date:%Y-%m-%d}"
            f"&size={size}"
        )

        for item in response.get("items", []):
            if item.get("exception", {}).get("replacedBy"):
                continue

            fraction_id = (
                item.get("fraction", {})
                .get("logo", {})
                .get("id")
            )

            if fraction_id not in FRACTION_MAP:
                continue

            date_str = item["timestamp"].split("T")[0]
            y, m, d = date_str.split("-")
            collection_date = date(int(y), int(m), int(d))

            fraction_key = FRACTION_MAP[fraction_id]["key"]
            result[fraction_key].append(collection_date)

        return result
