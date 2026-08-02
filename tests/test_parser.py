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


def test_parse_accented_egp_metadata_and_letter_d() -> None:
    html = """
    <html><body>
      <div>M\u00e3 TBMT: IB2600099999</div>
      <div>T\u00ean g\u00f3i th\u1ea7u: Cung c\u1ea5p c\u00e1p quang</div>
      <div>B\u00ean m\u1eddi th\u1ea7u: C\u00f4ng ty QI</div>
      <div>Gi\u00e1 g\u00f3i th\u1ea7u: 1.500.000.000 VND</div>
      <div>Ng\u00e0y \u0111\u0103ng t\u1ea3i: 01/08/2026</div>
      <div>Th\u1eddi \u0111i\u1ec3m \u0111\u00f3ng th\u1ea7u: 10:00 12/08/2026</div>
      <div>\u0110\u1ecba \u0111i\u1ec3m th\u1ef1c hi\u1ec7n: L\u00e3nh Binh Th\u0103ng</div>
      <div>L\u0129nh v\u1ef1c: C\u00f4ng ngh\u1ec7 th\u00f4ng tin</div>
      <div>Ph\u01b0\u01a1ng th\u1ee9c l\u1ef1a ch\u1ecdn nh\u00e0 th\u1ea7u: M\u1ed9t giai \u0111o\u1ea1n m\u1ed9t t\u00fai h\u1ed3 s\u01a1</div>
      <div>Phi\u00ean b\u1ea3n: 2</div>
    </body></html>
    """

    notice = parse_notice_html(html, "https://muasamcong.mpi.gov.vn/detail/2")

    assert notice.notice_code == "IB2600099999"
    assert notice.location == "L\u00e3nh Binh Th\u0103ng"
    assert notice.sector == "C\u00f4ng ngh\u1ec7 th\u00f4ng tin"
    assert notice.selection_method == "M\u1ed9t giai \u0111o\u1ea1n m\u1ed9t t\u00fai h\u1ed3 s\u01a1"
    assert notice.notice_version == "2"


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
