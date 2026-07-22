from app.mock_backends import build_backend_registry


if __name__ == "__main__":
    registry = build_backend_registry()
    print("Available mock services:")
    for name in registry:
        print(f"- {name}")
