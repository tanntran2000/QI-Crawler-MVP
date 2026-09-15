# Builder return — Operational Profile bounded forward fix

Date: 2026-09-08. WP: `WP-BID-RADAR-OPERATIONAL-PROFILE-01`.
Role: `BUILDER_SINGLE_WRITER`. Recipient: `PLANNER_ARCHITECT`.
Authority: Human's latest request and attached Planner F1–F5 forward-fix order.
This is Builder evidence, not an independent Reviewer verdict.

## Nhận xét Planner và cách sửa

- **Đúng — mã IB chưa chuẩn:** parser chung cố ý giữ chuỗi nguồn thô; lỗi nằm
  ở projection xuất/sàng lọc dùng raw thay vì base ID + revision. Chỉ sửa
  projection TBMT; giữ nguyên parser chung và raw fields. Không đổi PL thành IB.
- **Đúng — baseline cần đối chiếu:** fetch origin và fast-forward từ `206f7e7`
  tới `e5caedd75c8dd83fbb25932376c72b21e98f86da`. Chênh lệch chỉ có
  `CURRENT.md` và `PROJECT_MEMORY.md`; không có khác biệt source/tests.
- **Đúng — không tự duyệt địa bàn:** profile mặc định không cấu hình danh sách
  địa bàn. Không có cấu hình hoặc thiếu trường địa điểm thực hiện thì chưa đủ
  thông tin. Tên bên mời thầu, dự án, địa chỉ chỉ là gợi ý, không chứng minh nơi
  thực hiện. Chưa có phép đo khoảng cách 100 km; không coi cả tỉnh là trong bán kính.
- **Đúng, cần giữ ranh giới — mở rộng công nghệ:** thêm linh kiện điện tử,
  hạ tầng/thiết bị CNTT và rack có ngữ cảnh. Đào tạo chỉ nhắc chủ đề phần mềm
  không đủ bằng chứng mua/cung cấp công nghệ. Đào tạo kèm hạng mục cung cấp
  công nghệ riêng vẫn có thể đáp ứng; không loại toàn bộ ngành đào tạo.
  Không tự thêm “phòng họp không giấy” ngoài danh sách F3 được giao.
- **Đúng — sheet cần bổ sung không chứa gói đã trượt điều kiện cứng:** chỉ giữ
  NEEDS_INFO; ưu tiên nhóm đã đạt ngành nghề, giá, hình thức, phương thức và chỉ
  thiếu địa điểm; sau đó nhóm có căn cứ CNTT khác; cuối cùng nhóm chưa rõ CNTT.
  Trong mỗi nhóm giữ thứ tự dòng nguồn. Mọi gói vẫn có ở sheet kiểm toán.

## Team Bid đọc kết quả như thế nào

Hai sheet nghiệp vụ dùng tên và kết quả tiếng Việt:

| Thuật ngữ nội bộ | Hiển thị/ý nghĩa nghiệp vụ |
|---|---|
| C07 | Phù hợp ngành công nghệ thông tin |
| C09 | Ưu tiên ngân sách (≤ 2 tỷ), không tự đổi nghĩa canonical |
| C10 | Địa bàn theo sàng lọc nguồn; không phải xác nhận địa điểm thực hiện |
| Budget Status | Ngân sách theo hồ sơ sàng lọc; điều kiện cứng riêng |
| FIT | Phù hợp hồ sơ sàng lọc, không phải quyết định dự thầu |
| NEEDS_INFO | Cần bổ sung thông tin, không phải hàng đợi bắt buộc Human duyệt |
| OUTSIDE_PROFILE | Ngoài hồ sơ sàng lọc hiện tại, vẫn giữ ở sheet kiểm toán |

Các cột ghi rõ hình thức, phương thức lựa chọn nhà thầu, trích dẫn căn cứ,
địa điểm thực hiện, thông tin cần bổ sung và điều kiện chưa đáp ứng.
Sheet kiểm toán giữ mã trạng thái máy để đối chiếu; META giải nghĩa.
`MACHINE_OUTPUT_GROUND_TRUTH = NO`.

## Kiểm chứng 51 dòng — giới hạn bằng chứng quan trọng

Không tìm thấy workbook nguồn `TBMT_7_9_2026.xlsx` tại đường dẫn đã giao.
Dùng bản xuất đã lưu `C:/Users/Admin/Downloads/TBMT_7_9_2026_OPERATIONAL_PROFILE.xlsx`
theo F5, không thay bằng workbook khác. Dựng đầu vào replay từ tên gói, giá,
hình thức, phương thức và căn cứ địa điểm lưu trong sheet kiểm toán cũ.
Không phục hồi giả nội dung chính, bên mời thầu hay dự án đã mất.

`EVIDENCE_MODE = SAVED_OUTPUT_REPLAY_NOT_RAW_SOURCE_ACCEPTANCE`.
Bản xuất cũ không đổi hash trong quá trình chạy. File kết quả ghi giới hạn
trong META; dòng Excel gốc kế thừa được lưu ở cột riêng. SHA nguồn của replay
là SHA file replay, không được hiểu là SHA workbook gốc.

| Chỉ số | Kết quả replay |
|---|---:|
| Dòng dữ liệu / đọc được / lỗi đọc | 51 / 51 / 0 |
| Mã IB canonical sai định dạng | 0 |
| Có căn cứ CNTT / chưa rõ CNTT | 21 / 30 |
| Phù hợp / cần bổ sung / ngoài hồ sơ | 0 / 30 / 21 |
| Dòng sheet 02 | 30 |
| Có căn cứ CNTT và chỉ thiếu địa điểm | 9 |

Không yêu cầu số gói phù hợp lớn hơn 0. Chưa cấu hình địa bàn và thiếu
căn cứ nơi thực hiện thì giữ chưa đủ thông tin là đúng, không nới luật để tạo FIT.

### Mười dòng đầu sheet 02 sau sắp xếp

| IB chuẩn | Giá VND | Dòng Excel gốc kế thừa | Cần bổ sung |
|---|---:|---:|---|
| IB2600513038-00 | 991000000 | 26 | Địa điểm/cấu hình địa bàn |
| IB2600478315-00 | 947277000 | 30 | Địa điểm/cấu hình địa bàn |
| IB2600465975-01 | 531520000 | 33 | Địa điểm/cấu hình địa bàn |
| IB2600505517-00 | 493750000 | 40 | Địa điểm/cấu hình địa bàn |
| IB2600513598-00 | 317000000 | 41 | Địa điểm/cấu hình địa bàn |
| IB2600512865-00 | 650000000 | 49 | Địa điểm/cấu hình địa bàn |
| IB2600476591-00 | 1185998000 | 55 | Địa điểm/cấu hình địa bàn |
| IB2600494776-01 | 270000000 | 56 | Địa điểm/cấu hình địa bàn |
| IB2600513959-00 | 846250000 | 59 | Địa điểm/cấu hình địa bàn |
| IB2600510206-00 | Chưa có | 11 | Giá, hình thức, phương thức, địa điểm |

Tên gói đầy đủ và căn cứ nằm trong workbook kết quả, không suy diễn địa bàn
từ các địa danh trong tên gói ở bảng trên.

## Engineering evidence and handoff boundary

- CodeGraph invoked for `parse_tbmt_notice_identity`, `_screen_c07`,
  `_screen_execution_location`. Impact: shared identity parser has 20 callers;
  no shared-parser mutation. Edit radius: Excel screening/export module and
  its tests; documentation radius: this report and Unreleased changelog.
- Superpowers systematic-debugging and TDD used: regression RED 16 failures,
  then targeted GREEN 30 passing. Verification-before-completion used.
- Collection baseline 991; final 1012, no collection errors or decrease.
- Full suite: `1012 passed in 149.89s`, using repository virtualenv,
  `pytest -q -p no:cacheprovider --basetemp .tmp/pytest-operational-final`.
  Ruff: all checks passed. `git diff --check`: passed (only Git CRLF notices).
  No hosted-CI claim.
- Protected pre-existing artifacts were not edited, moved, staged or committed.
- No business workbook is added to Git. Replay/output reside under ignored `.tmp`.
- RELEASE IMPACT: new user-visible shortlist capability, MINOR candidate;
  no version/release publication authorized or performed.
- No commit, push, merge, browser/e-GP action or independent audit performed.

## Planner decisions still required

1. Review this bounded diff and the replay limitation; require raw-source
   acceptance when the original workbook becomes available.
2. Resolve the authoritative geographic configuration and evidence standard;
   alias matching is not a validated 100 km distance engine.
3. Reconcile active CURRENT and formal review scope before assigning Reviewer.
   CURRENT on main still records the preceding merged Parent; Builder did not
   invent Planner reconciliation or overwrite that authority without write scope.

SPINE_IMPACT = CURRENT (pending governed Planner reconciliation)
SPINE_TARGET_FILES = docs/agent_handoff/CURRENT.md
SPINE_SYNC_STATE = HOLD
HANDOFF_READY = NO_FOR_INDEPENDENT_AUDIT
NEXT_AUTHORITY = PLANNER_ARCHITECT
EXACTLY_ONE_NEXT_ACTION = PLANNER_BUILDER_RESULT_REVIEW
