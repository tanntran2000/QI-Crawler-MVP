# WP8-E0 — e-GP Authentication Evidence Mapping

```text
DOCUMENT_CLASS = DATED_EVIDENCE_SNAPSHOT
EVIDENCE_AS_OF = 2026-08-13
LIVE_STATUS_AUTHORITY = REQUIRES_REVERIFICATION
```

`VERIFIED` means verified by the recorded evidence as of the date above;
`TO_VERIFY_LIVE` means not safe to treat as current; `HOLD` means the evidence
is insufficient for implementation. Material auth selectors, origins and
flows must be reverified before any future automation Work Package.

Ngày khảo sát: **13/08/2026**  
Phạm vi: cổng Hệ thống mạng đấu thầu quốc gia và luồng xác thực trước đăng nhập.  
Trạng thái E0: **HOLD — chưa đủ bằng chứng sau đăng nhập để triển khai WP8-E1 mà không đoán flow/selector.**

## Nguyên tắc khảo sát

- Chỉ quan sát trang công khai, URL và DOM không chứa bí mật.
- Không nhập, đọc hoặc lưu username, password, OTP, CAPTCHA, PIN, cookie hay token.
- Không thử vượt 401/403/CAPTCHA/TLS hoặc biện pháp bảo mật.
- Không coi đổi URL là bằng chứng đăng nhập thành công.
- Không coi Agent hoặc USB Token là điều kiện đăng nhập khi chưa có bằng chứng.
- Mọi origin mới ngoài allowlist phải dừng ở `HUMAN_REQUIRED` để xác minh trước.

## Nguồn bằng chứng chính

| Mã | Nguồn chính thức | Mục đích |
|---|---|---|
| S1 | <https://muasamcong.mof.gov.vn/> | Entry do Bộ Tài chính công bố |
| S2 | <https://muasamcong.mpi.gov.vn/> | Portal e-GP đích hiện tại |
| S3 | <https://muasamcong.mpi.gov.vn/c/portal/login?p_l_id=139795> | Login entry point công khai |
| S4 | <https://muasamcong.mpi.gov.vn/web/guest/news?_egpportalnews_WAR_egpportalnews_render=detail&id=7e4ca348-c06b-4495-bf51-59ffdb43e037&p_p_id=egpportalnews_WAR_egpportalnews&p_p_lifecycle=0&p_p_mode=view&p_p_state=normal> | Thông báo chính thức về xác thực VNeID |
| S5 | <https://muasamcong.mpi.gov.vn/web/guest/profile-info> | Trang cá nhân, nhóm vai trò và dấu hiệu phiên hết hạn |
| S6 | <https://muasamcong.mpi.gov.vn/vi/web/guest/guideline-contractors> | Hướng dẫn Nhà thầu, Agent và chứng thư số |
| S7 | <https://muasamcong.mpi.gov.vn/web/guest/news> | Tin chính thức về Agent phiên bản mới |

## 1. ENTRY

### E-01 — Entry chính thức chuyển sang portal đang vận hành

- **Claim:** Truy cập `https://muasamcong.mof.gov.vn/` dẫn trình duyệt tới `https://muasamcong.mpi.gov.vn/`.
- **Evidence source:** S1, S2; quan sát trình duyệt headed ngày 13/08/2026.
- **Evidence type:** `LIVE_OBSERVATION`
- **Status:** `VERIFIED`
- **URL/domain:** `muasamcong.mof.gov.vn` → `muasamcong.mpi.gov.vn`
- **DOM indicator:** Trang đích có tiêu đề “Hệ thống mạng đấu thầu quốc gia - Bộ Tài chính - EGP_v2.0 - EGP”.
- **Security implication:** Không được cho phép redirect tùy ý sang host không xác minh.
- **Implementation consequence:** Allowlist entry/canonical tối thiểu gồm đúng hai hostname trên. Redirect sang origin khác phải dừng để người dùng xác minh. Không hard-code HTTP status vì khảo sát này chỉ xác nhận navigation đích.

### E-02 — Login entry point công khai

- **Claim:** Portal công khai nút “Đăng nhập” trỏ đến `/c/portal/login?p_l_id=139795`.
- **Evidence source:** S2, S3; DOM công khai ngày 13/08/2026.
- **Evidence type:** `LIVE_OBSERVATION`
- **Status:** `VERIFIED`
- **URL/domain:** `https://muasamcong.mpi.gov.vn/c/portal/login?p_l_id=139795`
- **DOM indicator:** Link có accessible name `Đăng nhập`; sau navigation chuyển vào `/security/auth/realms/egp/protocol/openid-connect/auth` với tham số OIDC động.
- **Security implication:** `state`, `nonce`, `session_code` và các tham số OIDC là dữ liệu phiên, không được log hoặc hard-code.
- **Implementation consequence:** E1 phải mở login entry công khai rồi để portal tự tạo URL xác thực. Không xây URL OIDC bằng chuỗi cố định.

## 2. AUTH METHODS

### A-01 — Đăng nhập truyền thống vẫn hiện diện

- **Claim:** Trang xác thực hiện có phương thức tên đăng nhập và mật khẩu.
- **Evidence source:** S3; DOM login quan sát ngày 13/08/2026.
- **Evidence type:** `LIVE_OBSERVATION`
- **Status:** `VERIFIED`
- **URL/domain:** `muasamcong.mpi.gov.vn/security/auth/realms/egp/...`
- **DOM indicator:** Nhãn `Tên đăng nhập`, `Mật khẩu`, checkbox `Lưu mật khẩu`, link `Quên mật khẩu?`, button `Đăng nhập`.
- **Security implication:** QI-Crawler không đọc, điền, log hoặc lưu giá trị của các trường này; không chọn “Lưu mật khẩu”.
- **Implementation consequence:** E1 chỉ mở trình duyệt headed và chuyển quyền thao tác cho người dùng. Không tự động hóa credential fields.

### A-02 — VNeID là phương thức đăng nhập song song

- **Claim:** Người dùng có thể chọn đăng nhập bằng tài khoản định danh điện tử bên cạnh phương thức truyền thống.
- **Evidence source:** S3 (DOM live) và S4 (tin chính thức ngày 22/03/2026).
- **Evidence type:** `OFFICIAL_DOCUMENT`
- **Status:** `VERIFIED`
- **URL/domain:** Broker entry tương đối `/security/auth/realms/egp/broker/vneid/login`; origin cuối của VNeID chưa được mở trong khảo sát.
- **DOM indicator:** Link `Đăng nhập bằng tài khoản định danh điện tử`, có hình `VNeID`.
- **Security implication:** Origin VNeID cuối, QR/push/OTP hoặc bước xác nhận trên thiết bị là vùng người dùng tự thao tác; không ghi hình hoặc log dữ liệu bí mật.
- **Implementation consequence:** Không ép một phương thức duy nhất. E1 chờ người dùng hoàn tất phương thức họ chọn và chỉ kiểm tra trạng thái sau đăng nhập.

### A-03 — MFA/OTP theo từng flow chưa được xác minh

- **Claim:** Portal có khái niệm “mã xác thực”, nhưng chưa có bằng chứng về thời điểm, điều kiện hoặc UI MFA/OTP của từng phương thức đăng nhập.
- **Evidence source:** S5 công khai nội dung “thay đổi hình thức nhận mã xác thực”; không nhập credentials trong khảo sát.
- **Evidence type:** `OFFICIAL_DOCUMENT`
- **Status:** `TO_VERIFY_LIVE`
- **URL/domain:** `muasamcong.mpi.gov.vn/web/guest/profile-info`
- **DOM indicator:** Text công khai `thay đổi hình thức nhận mã xác thực`; chưa quan sát màn hình nhập mã sau login.
- **Security implication:** Không giả định OTP luôn có hoặc không có; không thu thập mã.
- **Implementation consequence:** E1 phải coi mọi bước MFA/OTP là `WAITING_FOR_HUMAN`; chỉ tiếp tục sau khi người dùng hoàn tất và post-login indicators được xác minh.

## 3. ROLE

### R-01 — e-GP có nhiều vai trò nghiệp vụ

- **Claim:** Portal phân tách các nhóm chức năng theo vai trò như Nhà thầu, Nhà đầu tư, Chủ đầu tư/Bên mời thầu, Cơ quan có thẩm quyền và Đơn vị quản lý đấu thầu.
- **Evidence source:** S5.
- **Evidence type:** `OFFICIAL_DOCUMENT`
- **Status:** `VERIFIED`
- **URL/domain:** `muasamcong.mpi.gov.vn/web/guest/profile-info`
- **DOM indicator:** Các khu vực `Thông tin nhà thầu`, `Thông tin nhà đầu tư`, `Thông tin về bên mời thầu`, `Thông tin về chủ đầu tư`, `Thông tin về cơ quan có thẩm quyền`, `Thông tin về đơn vị quản lý đấu thầu`.
- **Security implication:** Đăng nhập thành công không đồng nghĩa tài khoản có quyền Nhà thầu hoặc quyền đọc mọi trang.
- **Implementation consequence:** `AUTHENTICATED` và `CRAWL_READY` phải tách biệt; chỉ `CRAWL_READY` khi vai trò/capability phù hợp được xác minh.

### R-02 — Thời điểm chọn vai trò Nhà thầu chưa được xác minh

- **Claim:** Chưa xác định vai trò được chọn trong login, ngay sau login, từ profile hay tự động theo account.
- **Evidence source:** Không thực hiện đăng nhập trong E0; pre-login DOM không có role selector.
- **Evidence type:** `LIVE_OBSERVATION`
- **Status:** `TO_VERIFY_LIVE`
- **URL/domain:** post-login trên `muasamcong.mpi.gov.vn`
- **DOM indicator:** Cần ghi lại accessible name/role indicator sau khi người dùng tự đăng nhập; không chấp nhận selector suy đoán.
- **Security implication:** Chọn nhầm vai trò có thể dẫn tới truy cập sai capability hoặc tổ chức.
- **Implementation consequence:** WP8-E1 chưa được code role selector. Một buổi quan sát headed có người dùng phải xác minh cách chọn/chuyển vai trò và trạng thái Nhà thầu đang active.

### R-03 — Vai trò e-GP khác vai trò kiểm soát nội bộ QI

- **Claim:** `Maker/Checker/Approver/Submitter` là phân quyền quy trình nội bộ QI, không phải bằng chứng về role của e-GP.
- **Evidence source:** Yêu cầu kiểm soát của QI trong WP8-E0.
- **Evidence type:** `QI_INTERNAL_POLICY`
- **Status:** `VERIFIED`
- **URL/domain:** Không áp dụng.
- **DOM indicator:** Không áp dụng.
- **Security implication:** Không ánh xạ tự động quyền nội bộ QI thành quyền trên cổng e-GP.
- **Implementation consequence:** Mô hình quyền QI phải nằm ngoài auth state của e-GP; E1 chỉ quan sát role/capability do portal hiển thị.

## 4. POST-LOGIN IDENTITY

### I-01 — URL change không đủ chứng minh authenticated

- **Claim:** Success phải dựa trên nhiều indicator, không chỉ URL rời trang login.
- **Evidence source:** Luồng OIDC có nhiều redirect/state động; chính sách an toàn QI.
- **Evidence type:** `QI_INTERNAL_POLICY`
- **Status:** `VERIFIED`
- **URL/domain:** `muasamcong.mpi.gov.vn`
- **DOM indicator:** Tối thiểu cần đồng thời: login form biến mất, account/profile control xuất hiện, trang validation bảo vệ không báo hết phiên và identity/organization hợp lệ.
- **Security implication:** Dựa vào URL đơn lẻ có thể lưu session chưa xác thực hoặc session sai tài khoản.
- **Implementation consequence:** E1 phải fail closed về `UNKNOWN_STATE` nếu không đủ indicator độc lập.

### I-02 — Indicator identity/organization thực tế chưa được quan sát

- **Claim:** Tên người dùng, tên tổ chức, MST/mã doanh nghiệp và role/capability post-login chưa được xác minh.
- **Evidence source:** E0 không yêu cầu người dùng đăng nhập và không thu thập dữ liệu nhận dạng.
- **Evidence type:** `LIVE_OBSERVATION`
- **Status:** `TO_VERIFY_LIVE`
- **URL/domain:** Trang account/profile sau login trên `muasamcong.mpi.gov.vn`.
- **DOM indicator:** Cần quan sát tên nhãn và vị trí hiển thị, chỉ ghi schema/selector semantic; không ghi giá trị thật của tài khoản hoặc tổ chức vào log/tài liệu.
- **Security implication:** Có nguy cơ dùng nhầm tổ chức hoặc nhầm role nếu chỉ thấy account menu.
- **Implementation consequence:** E1 phải nhận expected organization từ cấu hình nội bộ an toàn và so khớp indicator đã xác minh; mismatch → `ORGANIZATION_MISMATCH`.

## 5. SESSION

### S-01 — Luồng xác thực sử dụng OpenID Connect

- **Claim:** Login entry chuyển tới endpoint `protocol/openid-connect/auth` với `client_id=user-mpi`, `state` và `nonce` động.
- **Evidence source:** S3; URL live ngày 13/08/2026.
- **Evidence type:** `LIVE_OBSERVATION`
- **Status:** `VERIFIED`
- **URL/domain:** `muasamcong.mpi.gov.vn/security/auth/realms/egp/protocol/openid-connect/auth`
- **DOM indicator:** Login page title `MẠNG ĐẤU THẦU QUỐC GIA`.
- **Security implication:** Không ghi URL đầy đủ chứa state/nonce/session code; không tái tạo token.
- **Implementation consequence:** Browser context phải giữ nguyên xuyên suốt human login và validation; không chuyển sang HTTP client riêng giữa flow.

### S-02 — Dấu hiệu phiên hết hạn có text rõ ràng

- **Claim:** Khi không có phiên hợp lệ, trang profile công khai hiển thị `Phiên đăng nhập của bạn đã hết hạn. Vui lòng đăng nhập lại`.
- **Evidence source:** S5; DOM live ngày 13/08/2026.
- **Evidence type:** `LIVE_OBSERVATION`
- **Status:** `VERIFIED`
- **URL/domain:** `https://muasamcong.mpi.gov.vn/web/guest/profile-info`
- **DOM indicator:** Exact visible text trên.
- **Security implication:** Không cố refresh token hoặc lặp login tự động khi gặp indicator này.
- **Implementation consequence:** Đây là negative session indicator đáng tin cậy: chuyển `SESSION_EXPIRED` → `HUMAN_REQUIRED` và hướng dẫn login lại.

### S-03 — Cookie/storage_state, logout và idle timeout chưa được xác minh

- **Claim:** Chưa xác minh tên cookie, storage key, logout control, idle warning hoặc thời gian timeout chính xác.
- **Evidence source:** Không kiểm tra cookie/local storage và không đăng nhập trong E0.
- **Evidence type:** `LIVE_OBSERVATION`
- **Status:** `TO_VERIFY_LIVE`
- **URL/domain:** post-login trên `muasamcong.mpi.gov.vn` và origin VNeID nếu có.
- **DOM indicator:** Cần quan sát semantic logout control, idle modal và redirect/expired message; tuyệt đối không ghi giá trị cookie/token.
- **Security implication:** Không được đưa thời gian timeout phỏng đoán vào code; storage state là dữ liệu nhạy cảm phải nằm ngoài Git, log và report.
- **Implementation consequence:** E1 chỉ lưu browser storage state sau khi identity + organization + session validation đều pass; quyền file hạn chế, xóa khi logout/session expired. Exact timeout để cấu hình `unknown`, không hard-code.

### S-04 — Validation target đề xuất

- **Claim:** `profile-info` là ứng viên validation target vì có nội dung role/account và indicator hết phiên rõ ràng, nhưng positive authenticated DOM chưa được quan sát.
- **Evidence source:** S5.
- **Evidence type:** `INFERENCE`
- **Status:** `TO_VERIFY_LIVE`
- **URL/domain:** `https://muasamcong.mpi.gov.vn/web/guest/profile-info`
- **DOM indicator:** Negative: exact expired text; Positive: cần xác minh account/organization/role elements sau login.
- **Security implication:** Negative indicator có thể dùng ngay; thiếu negative không được tự suy ra authenticated.
- **Implementation consequence:** E1 cần live observation xác nhận target này trước khi dùng làm session validator.

## 6. AGENT

### G-01 — Agent không xuất hiện ở màn hình login quan sát được

- **Claim:** Pre-login UI quan sát được không yêu cầu cài/chạy Agent để hiển thị hoặc bắt đầu xác thực.
- **Evidence source:** S3 live DOM.
- **Evidence type:** `LIVE_OBSERVATION`
- **Status:** `VERIFIED`
- **URL/domain:** OIDC login trên `muasamcong.mpi.gov.vn`
- **DOM indicator:** Login form và VNeID link; không có Agent control/message trong màn hình này.
- **Security implication:** Không khởi chạy phần mềm native chỉ để thực hiện login nếu portal không yêu cầu.
- **Implementation consequence:** Agent không phải dependency của `OPENING_PORTAL`/`WAITING_FOR_HUMAN`. Nếu post-login phát sinh yêu cầu khác, phải bổ sung bằng chứng riêng.

### G-02 — Agent gắn với chuẩn bị/tham dự và chữ ký số

- **Claim:** Hướng dẫn Nhà thầu đặt VNeGP Client Agent trong chuỗi đăng ký/cài đặt, chuẩn bị/tham dự thầu và cảnh báo lỗi ký số do thiết bị chứng thư số.
- **Evidence source:** S6.
- **Evidence type:** `OFFICIAL_DOCUMENT`
- **Status:** `VERIFIED`
- **URL/domain:** `muasamcong.mpi.gov.vn/vi/web/guest/guideline-contractors`
- **DOM indicator:** `Phần mềm VNeGP Client Agent`; cảnh báo `lỗi trong quá trình ký số` và `thiết bị chứng thư số`.
- **Security implication:** Agent là phần mềm native nhạy cảm; chỉ dùng bộ cài/chữ ký số chính thức và không tự động điều khiển trong crawler.
- **Implementation consequence:** Đưa Agent vào nhánh signing riêng; không dùng Agent làm auth-success indicator.

### G-03 — Phiên bản Agent công bố hiện tại

- **Claim:** Portal thông báo triển khai Agent phiên bản `2.0.1` từ 18/07/2026.
- **Evidence source:** S2, S7; thông báo công khai trên trang chủ quan sát ngày 13/08/2026.
- **Evidence type:** `OFFICIAL_DOCUMENT`
- **Status:** `VERIFIED`
- **URL/domain:** `muasamcong.mpi.gov.vn`
- **DOM indicator:** Text `Agent phiên bản 2.0.1` trong “THÔNG BÁO QUAN TRỌNG”.
- **Security implication:** Phiên bản có thể thay đổi; không hard-code làm điều kiện login.
- **Implementation consequence:** Nếu sau này kiểm tra Agent, lấy version từ nguồn chính thức tại runtime/maintenance, không khóa WP8-E1 vào 2.0.1.

## 7. USB TOKEN / CERTIFICATE

### C-01 — Chứng thư số thuộc vùng account/signing, không phải login form quan sát được

- **Claim:** Portal tách `Thông tin tài khoản và chứng thư số`/`đăng ký CTS`; hướng dẫn liên hệ chứng thư số với lỗi ký số, trong khi login UI không có USB Token/certificate control.
- **Evidence source:** S3, S5, S6.
- **Evidence type:** `OFFICIAL_DOCUMENT`
- **Status:** `VERIFIED`
- **URL/domain:** `muasamcong.mpi.gov.vn`
- **DOM indicator:** Profile: `Thông tin tài khoản và chứng thư số`, `đăng ký CTS`; guide: `lỗi trong quá trình ký số`; login: chỉ credential/VNeID controls.
- **Security implication:** Không yêu cầu PIN/token trong login automation; không đọc certificate store hoặc điều khiển ký.
- **Implementation consequence:** Giữ ranh giới bắt buộc: `LOGIN != CRAWL_READY != SIGN_READY`.

### C-02 — Điều kiện sign-ready cụ thể chưa được xác minh

- **Claim:** Chưa xác minh UI phát hiện Agent, USB Token, certificate validity, PIN prompt hoặc capability ký của tài khoản Nhà thầu.
- **Evidence source:** Không thao tác nghiệp vụ ký trong E0.
- **Evidence type:** `LIVE_OBSERVATION`
- **Status:** `TO_VERIFY_LIVE`
- **URL/domain:** Nghiệp vụ ký sau login trên e-GP.
- **DOM indicator:** Chưa xác minh.
- **Security implication:** Không được tự ký, submit, nhập PIN hoặc giả lập certificate readiness.
- **Implementation consequence:** WP8-E1 không chứa signing. Nhánh signing chỉ được nghiên cứu bằng task riêng và human-in-the-loop.

## 8. Quy trình live observation còn thiếu

Buổi xác minh tiếp theo phải dùng browser headed do QI-Crawler quản lý:

1. QI-Crawler mở S3 và chuyển sang `WAITING_FOR_HUMAN`.
2. Người dùng tự chọn phương thức, nhập bí mật và xử lý OTP/CAPTCHA trên browser.
3. Observer chỉ ghi URL origin/path, accessible labels và trạng thái DOM không chứa giá trị nhận dạng.
4. Không chụp/ghi secret fields, cookie, token, QR, OTP, password, PIN hay MST/tên tổ chức thật vào log.
5. Xác minh tối thiểu: account indicator, organization indicator, role Nhà thầu, protected target, logout control, expired redirect/message và idle warning nếu xuất hiện tự nhiên.
6. Kết thúc bằng logout thủ công; không test ký số hoặc submit.

## 9. State model đề xuất

```text
IDLE
  -> OPENING_PORTAL
  -> WAITING_FOR_HUMAN
  -> VERIFYING_IDENTITY
  -> VERIFYING_ORGANIZATION
  -> VERIFYING_SESSION
  -> AUTHENTICATED
  -> CRAWL_READY
```

Safe terminal/interruption states:

```text
AUTH_FAILED
SESSION_EXPIRED
ORGANIZATION_MISMATCH
UNKNOWN_STATE
CANCELLED
HUMAN_REQUIRED
```

Guard đề xuất:

- `WAITING_FOR_HUMAN` không có timeout giả; người dùng có thể cancel.
- `VERIFYING_IDENTITY` cần ít nhất hai indicator, không dùng URL alone.
- `VERIFYING_ORGANIZATION` không log giá trị thật; mismatch fail closed.
- `VERIFYING_SESSION` phải kiểm tra protected target và negative expired indicator.
- Chỉ lưu storage state sau khi đến `AUTHENTICATED` và xác minh `CRAWL_READY`.
- 401/403/CAPTCHA/TLS error/origin lạ → `HUMAN_REQUIRED`, không retry để vượt kiểm soát.

Nhánh signing độc lập:

```text
AGENT_READY
  -> TOKEN_READY
  -> CERTIFICATE_VALID
  -> SIGN_READY
```

Nhánh này không được kích hoạt từ crawler và không nằm trong WP8-E1.

## 10. E0 exit gate

### Kết quả phiên live verification ngày 13/08/2026

- Entry redirect, login entry, hai auth method và việc không có role selector ở pre-login đã được xác minh lại bằng browser headed.
- Người dùng chưa thể hoàn tất đăng nhập trong phiên khảo sát này.
- Không có quan sát post-login; không thu thập credential, OTP, CAPTCHA, cookie, token hoặc dữ liệu tổ chức.
- Các mục post-login bên dưới tiếp tục giữ `TO_VERIFY_LIVE`; không được chuyển thành selector hoặc logic production dựa trên suy luận.

### Đã đủ bằng chứng

- Entry redirect và canonical portal.
- Login entry point và OIDC boundary.
- Hai phương thức hiện hữu: truyền thống và VNeID.
- Negative session indicator rõ ràng.
- Agent không xuất hiện ở pre-login và Agent 2.0.1 được portal công bố.
- Certificate/Agent thuộc vùng account/signing, không phải bằng chứng login-ready.

### Còn phải xác minh live trước WP8-E1

- MFA/OTP thực tế theo từng auth method.
- Positive authenticated indicators.
- Organization name/MST indicator và cách so khớp không lộ dữ liệu.
- Thời điểm/cách chọn role Nhà thầu và capability crawl.
- Positive session validation target.
- Logout control, expired redirect, idle warning và timeout chính xác.
- Storage-state lifecycle mà không đọc/log cookie hoặc token.

**Quyết định:** Chưa code WP8-E1. E0 chỉ chuyển `PASS` sau một buổi human-operated login xác minh các mục trên và cập nhật chúng từ `TO_VERIFY_LIVE` thành `VERIFIED`.
