# Ke hoach quyen khan cap va khoi phuc QI-Crawler

Trang thai: **Chua trien khai - luu de phat trien sau**.

## Muc tieu

Tao co che `break-glass` hop le de chu so huu QI-Crawler co the khoi phuc quyen quan tri khi mat quyen truy
cap, dong thoi bao ve du lieu, giu dau vet kiem toan va khong tao cua hau bi mat.

## Nguyen tac bat buoc

- Khong nhung mat khau, token, private key hoac recovery key vao source code/GitHub.
- Khong co lenh an de vuot xac thuc, bo audit log hoac am tham lay du lieu.
- Recovery key do chu so huu giu offline, tach khoi may chu va repository.
- Quyen khan cap co pham vi ro rang, thoi han ngan va tu dong thu hoi.
- Moi lan kich hoat deu ghi audit log chong sua doi va phat canh bao.
- Thay doi quyen hoac khoa phai co migration va kiem thu de ton tai an toan qua cac lan cap nhat.
- Ban phat hanh can duoc ky so; branch chinh can protection va CODEOWNERS.

## Luong du kien

1. Chu so huu gui yeu cau khoi phuc.
2. He thong kiem tra recovery key/chu ky so va MFA doc lap.
3. He thong cap vai tro Owner tam thoi cho dung tai khoan va pham vi duoc phep.
4. He thong ghi thoi gian, nguoi yeu cau, ly do, thiet bi/IP va quyen da cap.
5. He thong gui canh bao toi kenh quan tri da cau hinh.
6. Quyen tu het han; muon gia han phai xac thuc lai.

## Hang muc trien khai sau

- Mo hinh vai tro `Owner`, `Admin`, `Reviewer`, `Operator`, `Viewer`.
- Recovery key ngau nhien, hash bang thuat toan phu hop; chi hien thi mot lan khi tao.
- MFA va quy trinh luan chuyen/thu hoi khoa.
- Ma hoa du lieu nhay cam voi khoa nam ngoai repository.
- Audit log append-only va bao cao cac lan dung quyen khan cap.
- Thoi han phien dac quyen va nguyen tac cap quyen toi thieu.
- Kich ban sao luu/khoi phuc repository, database va cau hinh.
- Ky release, xac minh checksum va phat hien ban cai dat bi thay doi.
- Bo test bao dam migration khong lam mat cau hinh khoi phuc qua cac phien ban.

## Dieu kien nghiem thu

- Khong ai co the kich hoat chi bang mot chuoi bi mat nam trong code.
- Khong the dung quyen khan cap ma khong de lai audit log va canh bao.
- Khong lam lo du lieu xac thuc qua Git, log, bao cao hoac file Excel.
- Co the thu hoi/doi recovery key khi nghi ngo bi lo.
- Quy trinh khoi phuc duoc thu dinh ky tren moi truong kiem thu.
