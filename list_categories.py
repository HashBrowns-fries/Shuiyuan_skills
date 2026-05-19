from shuiyuan_client import ShuiyuanClient


def main():
    client = ShuiyuanClient()
    data = client.categories()

    categories = data.get("category_list", {}).get("categories", [])

    for c in categories:
        print(f'{c.get("id")}\t{c.get("name")}')


if __name__ == "__main__":
    main()