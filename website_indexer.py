import sys
import time
import requests
from bs4 import BeautifulSoup
from io import BytesIO
from PyPDF2 import PdfWriter, PdfReader
from PyQt5.QtCore import QUrl
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
from PyQt5.QtWidgets import QApplication
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from urllib.parse import urlparse, urljoin
from collections import deque
from requests.exceptions import RequestException
import os

def scrape_website(input_url, depth=3):
    
    def is_subpath(base_url, full_url):
        base_parts = urlparse(base_url).path.rstrip('/').split('/')
        full_parts = urlparse(full_url).path.rstrip('/').split('/')
        return full_parts[:len(base_parts)] == base_parts

    def get_all_links_bfs(base_url, max_depth=2):
        if not base_url.endswith('/'):
            base_url += '/'
        visited_links = set()
        queue = deque([(base_url, 0)])

        while queue:
            current_url, depth = queue.popleft()
            if current_url not in visited_links:
                if depth < max_depth:
                    try:
                        response = requests.get(current_url)
                    except RequestException as e:
                        # print(f"Skipped {current_url} due to the following error: {e}")
                        continue

                    if response.status_code != 200:
                        # print(f"Skipped {current_url} due to a non-200 status code: {response.status_code}")
                        continue

                    else:
                        visited_links.add(current_url)
                        # print(f"ACESSED {current_url} || status code: {response.status_code}")

                        soup = BeautifulSoup(response.content, "html.parser")

                        for link in soup.find_all('a', href=True):
                            href = link['href']
                            if not href.startswith('#') and not href.startswith('mailto') and not href.startswith('javascript:'):
                                full_url = urljoin(base_url, href)
                                if full_url not in visited_links and is_subpath(base_url, full_url):
                                    queue.append((full_url, depth + 1))
        
        return visited_links



    temp_pdf = "docs\\temp.pdf"
    urls = get_all_links_bfs(input_url, depth)
    domain = input_url.replace("https://", "").replace("www.", "").replace(".com", "").replace(".io", "").replace(".net", "").replace(".", "_").replace("/", "_")
    final_file = f"docs\\{domain}.pdf"

    def convertIt():
        web.page().print(printer, lambda _: QApplication.exit())

    def create_watermark(url):
        packet = BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)
        can.setFont("Helvetica", 9)
        oknow = time.strftime("%a, %d %b %Y %H:%M")
        can.drawString(5, 2, url)
        can.drawString(605, 2, oknow)
        can.save()
        packet.seek(0)
        return PdfReader(packet)


    output = PdfWriter()

    for url in urls:
        web = QWebEngineView()
        web.settings().setAttribute(QWebEngineSettings.ErrorPageEnabled, False)
        web.settings().setAttribute(QWebEngineSettings.JavascriptEnabled, False)
        web.load(QUrl(url))
        printer = QPrinter()
        printer.setPageSize(QPrinter.A4)
        printer.setOrientation(QPrinter.Landscape)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(temp_pdf)

        web.loadFinished.connect(convertIt)
        app.exec_()
        watermark_pdf = create_watermark(url)
        existing_pdf = PdfReader(open(temp_pdf, "rb"))
        pages = len(existing_pdf.pages)
        for x in range(0, pages):
            page = existing_pdf.pages[x]
            page.merge_page(watermark_pdf.pages[0])
            output.add_page(page)
        
        existing_pdf.stream.close()
    os.remove(temp_pdf)

    outputStream = open(final_file, "wb")
    output.write(outputStream)
    outputStream.close()

    print(final_file, 'is ready.')

websites = [
    'https://lisk.com/documentation/tutorial',
    'https://zulko.github.io/moviepy/',
]


app = QApplication(sys.argv)

for website in websites:
    print("SCRAPING", website + "...")
    scrape_website(website)


print("------------------ FINSHED -------------------")