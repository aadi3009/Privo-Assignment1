import json
import random
import uuid
import os
import argparse

# -------------------------------
# Config / vocab
# -------------------------------

FIRST_NAMES = [
    "ramesh", "suresh", "amit", "priya", "nupoor", "sanjana",
    "rahul", "arjun", "meera", "vishal", "ananya", "divya"
]
LAST_NAMES = [
    "kumar", "sharma", "patel", "singh", "joshi", "desai",
    "khot", "yadav", "iyer", "reddy", "kapoor"
]

CITIES = [
    "mumbai", "delhi", "pune", "bangalore", "hyderabad",
    "chennai", "kolkata", "ahmedabad"
]

LOCATIONS = [
    "sector 21 gurgaon",
    "whitefield bangalore",
    "hinjewadi phase three",
    "baner pune",
    "andheri east",
    "salt lake city",
    "bkc mumbai",
]

EMAIL_PROVIDERS = ["gmail", "yahoo", "outlook", "hotmail", "protonmail"]

MONTHS = [
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december"
]

DIGITS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
ZERO_VARIANTS = ["zero", "oh"]
FILLERS = [
    "uh", "so", "like", "basically", "actually", "you know",
    "right now", "at the moment"
]

CONNECTORS = [
    "and", "also", "then", "after that", "further", "additionally"
]


# -------------------------------
# Small helper functions
# -------------------------------

def rand_name():
    return random.choice(FIRST_NAMES) + " " + random.choice(LAST_NAMES)


def rand_phone_spoken(length=10):
    tokens = []
    i = 0
    while i < length:
        r = random.random()
        if r < 0.15 and i <= length - 2:
            # "double x"
            d = random.randint(0, 9)
            tokens.append("double " + DIGITS[d])
            i += 2
        elif r < 0.2 and i <= length - 3:
            # "triple x"
            d = random.randint(0, 9)
            tokens.append("triple " + DIGITS[d])
            i += 3
        else:
            d = random.randint(0, 9)
            if d == 0:
                tokens.append(random.choice(ZERO_VARIANTS))
            else:
                tokens.append(DIGITS[d])
            i += 1
    return " ".join(tokens)


def rand_phone_numeric():
    return "".join(str(random.randint(0, 9)) for _ in range(10))


def rand_email(name):
    base = name.replace(" ", "")
    provider = random.choice(EMAIL_PROVIDERS)
    number = random.randint(1, 9999)
    style = random.choice(["spoken", "normal"])
    if style == "spoken":
        # e.g. "rameshkumar nine nine at gmail dot com"
        return f"{base}{number} at {provider} dot com"
    else:
        # e.g. "ramesh.kumar99@gmail.com"
        return f"{base}{number}@{provider}.com"


def rand_credit_card():
    parts = []
    for _ in range(4):
        block_digits = [random.randint(0, 9) for _ in range(4)]
        style = random.choice(["spoken", "mixed"])
        if style == "spoken":
            block = " ".join(DIGITS[d] if d != 0 else random.choice(ZERO_VARIANTS) for d in block_digits)
        else:
            block = "".join(str(d) for d in block_digits)
        parts.append(block)
    return " ".join(parts)


def rand_date_spoken():
    day = random.randint(1, 28)
    month = random.choice(MONTHS)
    year_style = random.choice(["digits", "spoken"])
    if year_style == "digits":
        year = random.choice(["2019", "2020", "2021", "2022", "2023", "2024"])
    else:
        year = random.choice([
            "two thousand nineteen",
            "two thousand twenty",
            "two thousand twenty one",
            "two thousand twenty two",
            "two thousand twenty three",
            "two thousand twenty four",
        ])
    # vary order a bit
    if random.random() < 0.5:
        return f"{day} {month} {year}"
    else:
        return f"{month} {day} {year}"


def pick_city_or_location():
    if random.random() < 0.5:
        return random.choice(CITIES), "CITY"
    else:
        return random.choice(LOCATIONS), "LOCATION"


def random_filler():
    return " " + random.choice(FILLERS) if random.random() < 0.4 else ""


def random_connector():
    return " " + random.choice(CONNECTORS) + " " if random.random() < 0.6 else " "


# -------------------------------
# Utterance builder (safe spans)
# -------------------------------

def build_utterance():
    """
    Build a single noisy STT-style utterance and its entities with correct spans.
    We use explicit concatenation and track character positions.
    """
    name = rand_name()
    phone = random.choice([rand_phone_spoken(), rand_phone_numeric()])
    email = rand_email(name)
    cc = rand_credit_card()
    date = rand_date_spoken()
    place, place_label = pick_city_or_location()

    entities = []
    text_parts = []
    pos = 0

    def add(txt):
        nonlocal pos
        text_parts.append(txt)
        pos += len(txt)

    def add_ent(txt, label):
        nonlocal pos
        start = pos
        text_parts.append(txt)
        end = start + len(txt)
        pos = end
        entities.append({"start": start, "end": end, "label": label})

    # Choose a random template shape
    template_type = random.choice([1, 2, 3])

    add("hi ")
    if template_type == 1:
        add("my name is ")
        add_ent(name, "PERSON_NAME")
        add(random_filler())
        add(random_connector())
        add("my phone number is ")
        add_ent(phone, "PHONE")
        add(random_connector())
        add("my email id is ")
        add_ent(email, "EMAIL")
        add(random_connector())
        add("my credit card number is ")
        add_ent(cc, "CREDIT_CARD")
        add(random_connector())
        add("i made this purchase on ")
        add_ent(date, "DATE")
        add(random_connector())
        add("and i currently live in ")
        add_ent(place, place_label)

    elif template_type == 2:
        add("please update ")
        add_ent(name, "PERSON_NAME")
        add(" details in your system ")
        add(random_connector())
        add("the card i am using is ")
        add_ent(cc, "CREDIT_CARD")
        add(random_connector())
        add("you can call me on ")
        add_ent(phone, "PHONE")
        add(random_connector())
        add("and email me at ")
        add_ent(email, "EMAIL")
        add(random_connector())
        add("date of transaction was ")
        add_ent(date, "DATE")
        add(random_connector())
        add("location ")
        add_ent(place, place_label)

    else:  # template_type 3
        add("this is ")
        add_ent(name, "PERSON_NAME")
        add(random_filler())
        add(" i am from ")
        add_ent(place, place_label)
        add(random_connector())
        add(" today is ")
        add_ent(date, "DATE")
        add(random_connector())
        add(" my registered email is ")
        add_ent(email, "EMAIL")
        add(random_connector())
        add(" contact number ")
        add_ent(phone, "PHONE")
        add(random_connector())
        add(" and my card on file is ")
        add_ent(cc, "CREDIT_CARD")

    text = "".join(text_parts)
    text = text.lower()

    # Lower-casing text does not change spans because we didn't change length.
    # But to be safe, we reconstruct entities with the same indices.
    return text, entities


# -------------------------------
# Generate a labeled or unlabeled sample
# -------------------------------

def generate_sample(sample_id, labeled=True):
    text, entities = build_utterance()
    if labeled:
        return {
            "id": sample_id,
            "text": text,
            "entities": entities,
        }
    else:
        # test set style: no entities
        return {
            "id": sample_id,
            "text": text,
        }


# -------------------------------
# Cleaning synthetic data
# -------------------------------

def clean_file(path):
    """
    Remove all lines where id starts with 'synthetic_'.
    Backup original as <path>.bak
    """
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return

    backup_path = path + ".bak"
    os.rename(path, backup_path)
    kept = 0
    removed = 0

    with open(backup_path, "r", encoding="utf8") as fin, \
         open(path, "w", encoding="utf8") as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                # keep weird lines just in case
                fout.write(line + "\n")
                kept += 1
                continue

            _id = obj.get("id", "")
            if isinstance(_id, str) and _id.startswith("synthetic_"):
                removed += 1
                continue
            else:
                fout.write(json.dumps(obj) + "\n")
                kept += 1

    print(f"Cleaned {path}: kept={kept}, removed synthetic={removed}, backup={backup_path}")


# -------------------------------
# CLI logic
# -------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=["generate", "clean"],
        required=True,
        help="generate: add synthetic data; clean: remove previous synthetic data"
    )
    parser.add_argument(
        "--split",
        choices=["train", "dev", "test"],
        help="Which split to operate on (required for generate mode)"
    )
    parser.add_argument(
        "--file",
        help="Path to jsonl file (e.g. data/train.jsonl). Required."
    )
    parser.add_argument(
        "--num_examples",
        type=int,
        default=50,
        help="Number of synthetic examples to generate (for generate mode)"
    )
    args = parser.parse_args()

    if not args.file:
        raise SystemExit("You must pass --file path/to/file.jsonl")

    if args.mode == "clean":
        clean_file(args.file)
        return

    # mode == generate
    if not args.split:
        raise SystemExit("For --mode generate you must specify --split train/dev/test")

    labeled = args.split in ("train", "dev")

    if not os.path.exists(args.file):
        print(f"{args.file} does not exist. It will be created.")

    with open(args.file, "a", encoding="utf8") as f:
        for _ in range(args.num_examples):
            sample_id = f"synthetic_{args.split}_{uuid.uuid4().hex[:8]}"
            sample = generate_sample(sample_id, labeled=labeled)
            f.write(json.dumps(sample) + "\n")

    print(f"Added {args.num_examples} synthetic {args.split} examples to {args.file}.")


if __name__ == "__main__":
    random.seed(42)
    main()