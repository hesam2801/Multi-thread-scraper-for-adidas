import enum
import json
import os
import requests
import threading


class TYPES(enum.Enum):
    NONE = 0
    PAGE = 1
    PRODUCT = 2
    REVIEW = 3


class AdidasThread(threading.Thread):
    t_id = 0
    t_type = TYPES.NONE
    t_url = ""
    t_page = 0
    t_products = []
    t_review_obj = {}
    pages = []
    products = []
    unsuccessful_links = []
    headers = {
        'authority': 'www.adidas.at',
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9,fa;q=0.8',
        'content-type': 'application/json',
        'user-agent': 'PostmanRuntime/7.35.0',
    }

    def __init__(self, t_id, t_type, t_url, t_page, t_review_obj, group=None, target=None, name=None, args=(),
                 kwargs=None, *, daemon=None):
        super().__init__(group, target, name, args, kwargs, daemon=daemon)
        self.t_id = t_id
        self.t_type = t_type
        self.t_url = t_url
        self.t_page = t_page
        self.t_review_obj = t_review_obj
        self.t_products = []

    def request_url(self, params=None):
        try:
            if params is None:
                response = requests.get(self.t_url, headers=self.headers)
                if response.status_code != 200:
                    print(f"error {response.status_code} for {self.t_url}")
                    return
                return response
            response = requests.get(self.t_url, headers=self.headers, params=params)
            if response.status_code != 200:
                print(f"error {response.status_code} for {self.t_url}")
                return
            return response
        except:
            self.unsuccessful_links.append({
                "t_type": self.t_type,
                "t_url": self.t_url,
                "t_page": self.t_page,
                "t_review_obj": self.t_review_obj,
            })
            print(f"error in Exception")
            return

    def get_pages(self):
        params = {'query': 'all', "start": 0}
        response = self.request_url(params=params)
        if response is None:
            return self.get_pages()
        response_json = response.json()
        item_list = response_json["raw"]["itemList"]
        pages_count = item_list["count"] // item_list["viewSize"]
        pages = [i for i in range(1, pages_count + 1)]
        return pages

    @staticmethod
    def load_data(file_name):
        with open(file_name, "r") as f:
            file_contents = json.loads(f.read())
            f.close()
        return file_contents

    @staticmethod
    def save_data(data, file_name):
        items = []
        if os.path.exists(file_name):
            file_contents = AdidasThread.load_data(file_name)
            items = file_contents
        if type(data) is list:
            items.extend(data)
        elif type(data) is dict:
            items.extend(data["reviews"])
        with open(file_name, "w") as f:
            json.dump(items, f)
        return

    def get_products(self):
        params = {'query': 'all', "start": (self.t_page - 1) * 48}
        response = self.request_url(params=params)
        if response is None:
            return
        response_json = response.json()
        try:
            self.t_products = response_json["raw"]["itemList"]["items"]
        except KeyError:
            return
        if not self.t_products:
            return self.get_products()
        AdidasThread.products.extend(self.t_products)
        AdidasThread.save_data(self.t_products, file_name=f"products/products{self.t_page}.json")

    def get_product_reviews(self):
        first_part = "https://www.adidas.at/api/models/"
        second_part = "/reviews?bazaarVoiceLocale=de_AT&feature&includeLocales=de%2A&limit="
        review_obj = self.t_review_obj
        limit = 5
        offset = 0
        while True:
            url = f"{first_part}{review_obj["model_id"]}{second_part}{limit}&offset={offset}&sort=newest"
            self.t_url = url
            response = self.request_url()
            if response is None:
                break
            if "totalResults" not in response.json():
                break
            else:
                if offset >= response.json()["totalResults"]:
                    break
                else:
                    data = {"reviews": response.json()["reviews"], "product_id": review_obj["product_id"]}
                    offset += limit
                    self.save_data(data, f"reviews/reviews{review_obj["product_id"]}.json")
        return

    def run(self):
        if self.t_type == TYPES.PAGE:
            pages = self.get_pages()
            AdidasThread.pages = pages
            return
        elif self.t_type == TYPES.PRODUCT:
            self.get_products()
        elif self.t_type == TYPES.REVIEW:
            self.get_product_reviews()
