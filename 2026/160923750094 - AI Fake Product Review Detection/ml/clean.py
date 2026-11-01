import re


def clean_text(text):
    text = str(text).lower()                  
    text = re.sub(r"<.*?>", " ", text)      
    text = re.sub(r"[^a-z\s]", " ", text)     
    text = re.sub(r"\s+", " ", text).strip() 
    return text


if __name__ == "__main__":
    print(clean_text("WOW!!! Best <br> product 100% LOVED it."))
