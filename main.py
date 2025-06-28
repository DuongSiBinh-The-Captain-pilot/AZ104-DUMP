import os, re, requests, time
from bs4 import BeautifulSoup
from urllib.parse import urlsplit, unquote

BASE_URL = 'https://cloudcert.vn/dump/az-104-microsoft-azure-administrator.html?page={}'
IMAGES_DIR = 'images'

def ensure_dirs():
    os.makedirs(IMAGES_DIR, exist_ok=True)

def download_image(img_url):
    path = urlsplit(img_url).path
    filename = os.path.basename(unquote(path))
    local_path = os.path.join(IMAGES_DIR, filename)
    if not os.path.isfile(local_path):
        resp = requests.get(img_url); resp.raise_for_status()
        with open(local_path, 'wb') as f: f.write(resp.content)
    return filename

def process_html_images(soup_fragment):
    for img in soup_fragment.find_all('img'):
        src = img.get('src')
        if not src: continue
        fname = download_image(src)
        md_tag = f'![]({IMAGES_DIR}/{fname})'
        img.replace_with(md_tag)
    return soup_fragment.get_text(separator='\n', strip=True)

def parse_page(html):
    soup = BeautifulSoup(html, 'html.parser')
    results = []
    for card in soup.select('.exam-question-card'):
        header = card.select_one('.card-header').get_text(strip=True)
        num = re.search(r'#Question\s*(\d+)', header).group(1)
        title = card.select_one('.question-title-topic').get_text(strip=True)

        body = card.select_one('.question-body .card-text')
        question_md = process_html_images(body)

        choices = []
        for li in card.select('.question-choices-container ul li'):
            letter = li.select_one('.charLetter').get_text(strip=True)
            text = li.get_text(strip=True).replace(letter, '').strip()
            choices.append(f"{letter} {text}")

        ans_box = card.select_one('.correct-answer-box .correct-answer')
        answer_md = process_html_images(ans_box) if ans_box else ''

        desc_div = card.select_one('.answer-description')
        desc = desc_div.get_text(separator='\n', strip=True) if desc_div else ''

        results.append({
            'num': num, 'title': title,
            'question': question_md, 'choices': choices,
            'answer': answer_md, 'description': desc
        })
    return results

def main():
    ensure_dirs()
    with open('output.md', 'w', encoding='utf-8') as f:
        cnt = 1
        for page in range(1, 123):
            resp = requests.get(BASE_URL.format(page)); resp.raise_for_status()
            for q in parse_page(resp.text):
                f.write(f"### Question {cnt}: {q['title']}\n\n")
                f.write(q['question'] + "\n\n")
                if q['choices']:
                    for c in q['choices']:
                        f.write(f"- {c}\n")
                    f.write("\n")
                f.write(f"**Correct Answer:** {q['answer']}\n\n")
                if q['description']:
                    f.write(f"_Explanation:_\n{q['description']}\n\n")
                f.write("---\n\n")
                cnt += 1
            time.sleep(1)
    print("Done! Mở output.md và images/ để kiểm tra.")
if __name__ == '__main__':
    main()