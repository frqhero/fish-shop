import os

import requests
from dotenv import load_dotenv


def main():
    load_dotenv()
    strapi_token = os.getenv('STRAPI_TOKEN')

    url = 'http://localhost:1337/api/products'
    headers = {
        'Authorization': f'Bearer {strapi_token}'
    }
    response = requests.get(url, headers=headers)
    1


if __name__ == '__main__':
    main()
