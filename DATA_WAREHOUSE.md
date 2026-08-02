# QI Data Warehouse

Kho du lieu cuc bo dung DuckDB va Parquet, phu hop may co 12 GB RAM. File mac dinh la
`data/warehouse/qi_warehouse.duckdb`.

## Cac tang du lieu

- `raw`: ban sao du lieu nguon, chi bo sung, khong sua am tham.
- `staging`: du lieu da chuan hoa kieu, ten cot va khoa.
- `mart`: bang phuc vu bao cao va quyet dinh kinh doanh.
- `governance`: danh muc dataset, nhat ky nap va danh gia luu giu.

File lon va lich su nen luu Parquet trong `data/warehouse/parquet`. Backup cuc bo nam trong
`data/warehouse/backups`. Tat ca tep van hanh nay duoc bo qua boi Git.

## Nguyen tac giu va loai

Moi dataset duoc danh gia theo bon trang thai:

- `KEEP`: can cho nghiep vu, kiem toan, doi soat hoac tai tao bao cao.
- `REVIEW`: chua du thong tin de quyet dinh.
- `QUARANTINE`: loi, nghi trung lap, sai schema hoac chua ro nguon; tach khoi bao cao.
- `DROP_PROPOSED`: co the bo, nhung chi la de xuat. Khong xoa vat ly khi chua co nguoi dung duyet.

Khong dua cookie, mat khau, token, CCCD, thong tin ngan hang hoac du lieu ca nhan khong can thiet vao
warehouse. Du lieu nguon va backup khong duoc commit len Git.

## Van hanh

Khoi tao:

```powershell
QI-Crawler warehouse-init
```

Kiem tra:

```powershell
QI-Crawler warehouse-status
```

Sao luu truoc moi thay doi schema hoac nap du lieu lon:

```powershell
QI-Crawler warehouse-backup
```

Ghi nhan mot de xuat danh gia:

```powershell
QI-Crawler warehouse-review ten_dataset REVIEW "Chua xac dinh muc dich su dung"
```

Moi nguon du lieu moi can thong nhat: chu so huu, muc dich, khoa nghiep vu, tan suat cap nhat,
thoi gian luu, truong nhay cam va dieu kien chat luong truoc khi nap vao `mart`.
