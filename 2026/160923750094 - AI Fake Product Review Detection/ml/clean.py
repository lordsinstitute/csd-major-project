# STEP 2: Clean the text so the model only sees useful words.
import re


def clean_text(text):
    text = str(text).lower()                  # "GREAT" -> "great"
    text = re.sub(r"<.*?>", " ", text)        # remove HTML tags like <br>
    text = re.sub(r"[^a-z\s]", " ", text)     # keep only letters and spaces
    text = re.sub(r"\s+", " ", text).strip()  # remove extra spaces
    return text


if __name__ == "__main__":
    print(clean_text("WOW!!! Best <br> product 100% LOVED it."))
