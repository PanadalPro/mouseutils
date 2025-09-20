from .app import main

if __name__ == "__main__":
    main()

def main():
    # keep the same callable for entry point; import above also works
    from .app import main as _main
    _main()
