from qi_crawler.parser import extract_detail_links, parse_money, parse_notice_html


def test_parse_money_vnd():
    amount, currency = parse_money("1.234.567.890 VND")
    assert amount == 1234567890.0
    assert currency == "VND"


def test_parse_notice_html():
    html = """
    <html><body>
      <h1>Chi tiet thong bao</h1>
      <div>Ma TBMT: IB2400012345</div>
      <div>Ten goi thau: Mua sam thiet bi mang</div>
      <div>Ben moi thau: Cong ty A</div>
      <div>Chu dau tu: Don vi B</div>
      <div>Gia goi thau: 2.500.000.000 VND</div>
      <div>Ngay dang tai: 01/01/2026</div>
      <div>Thoi diem dong thau: 10:00 10/01/2026</div>
      <a href="/files/hsmt.pdf">Tai HSMT</a>
    </body></html>
    """
    notice = parse_notice_html(html, "https://muasamcong.mpi.gov.vn/detail/1")
    assert notice.notice_code == "IB2400012345"
    assert notice.title == "Mua sam thiet bi mang"
    assert notice.buyer == "Cong ty A"
    assert notice.package_price == 2500000000.0
    assert len(notice.attachments) == 1
    assert notice.attachments[0].source_url == "https://muasamcong.mpi.gov.vn/files/hsmt.pdf"


def test_extract_detail_links_allowlist():
    html = """
      <div class="item"><a href="/detail/1">One</a></div>
      <div class="item"><a href="https://evil.example/a">Bad</a></div>
    """
    links = extract_detail_links(
        html,
        "https://muasamcong.mpi.gov.vn/search",
        ".item",
        "a",
        ["muasamcong.mpi.gov.vn"],
    )
    assert links == ["https://muasamcong.mpi.gov.vn/detail/1"]
