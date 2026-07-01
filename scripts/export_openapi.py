import json

from app.main import create_app


def main() -> None:
    app = create_app()
    with open("openapi.json", "w", encoding="utf-8") as file:
        json.dump(app.openapi(), file, indent=2, ensure_ascii=False)
        file.write("\n")


if __name__ == "__main__":
    main()
