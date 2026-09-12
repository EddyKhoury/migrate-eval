import gzip
import json
from pathlib import Path
from urllib.request import urlretrieve


BASE_URL = (
    "https://raw.githubusercontent.com/zai-org/CodeGeeX/main/"
    "codegeex/benchmark/humaneval-x"
)

FILES = {
    "java": f"{BASE_URL}/java/data/humaneval_java.jsonl.gz",
    "go": f"{BASE_URL}/go/data/humaneval_go.jsonl.gz",
}

OUTPUT_DIR = Path("data/humaneval_x")
EXPECTED_PROBLEMS = 164


def count_problems(path: Path) -> int:
    count = 0

    with gzip.open(path, "rt", encoding="utf-8") as file:
        for line in file:
            json.loads(line)
            count += 1

    return count


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for language, url in FILES.items():
        output_path = OUTPUT_DIR / f"humaneval_{language}.jsonl.gz"

        if not output_path.exists():
            print(f"Downloading {language} dataset...")
            urlretrieve(url, output_path)
            print(f"Saved to {output_path}")
        else:
            print(f"{language} dataset already exists.")

        count = count_problems(output_path)

        print(f"{language}: {count} problems")

        if count != EXPECTED_PROBLEMS:
            raise RuntimeError(
                f"Expected {EXPECTED_PROBLEMS} {language} problems, "
                f"but found {count}."
            )

    print("HumanEval-X verification successful.")


if __name__ == "__main__":
    main()