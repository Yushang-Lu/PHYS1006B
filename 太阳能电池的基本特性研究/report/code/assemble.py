from pypdf import PdfReader, PdfWriter, Transformation


def main():
    original = PdfReader("assets/原始记录.pdf")
    template = PdfReader("main.pdf")
    content = PdfReader("postlab.pdf")
    additions = PdfReader("record-additions.pdf")
    assert len(original.pages) == len(template.pages) == 5
    assert len(content.pages) == 2
    assert len(additions.pages) == 1
    report, postlab = PdfWriter(), PdfWriter()
    for page in original.pages[:3]:
        report.add_page(page)
    record_page = report.pages[2]
    offset = float(record_page.mediabox.height) - float(additions.pages[0].mediabox.height)
    record_page.merge_transformed_page(additions.pages[0], Transformation().translate(0, offset))
    for index in range(2):
        page = template.pages[index + 3]
        page.merge_page(content.pages[index])
        report.add_page(page)
        postlab.add_page(page)
    report.add_metadata({"/Title": "太阳能电池的基本特性研究", "/Author": ""})
    report.write("report.pdf")
    postlab.write("postlab.pdf")
    final = PdfReader("report.pdf")
    for index in range(2):
        assert original.pages[index].get_contents().get_data() == final.pages[index].get_contents().get_data()


if __name__ == "__main__":
    main()
