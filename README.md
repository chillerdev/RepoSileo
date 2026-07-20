# Sileo static repository

Repo APT tĩnh dành cho Sileo, Zebra và các package manager tương thích. GitHub Pages hiển thị danh sách app từ chính metadata của file `.deb`.

## Sử dụng

1. Sửa tên và mô tả repo trong `repo.config.json`.
2. Chép các file `.deb` vào thư mục `debs/`.
3. Trên Windows, chạy `./scripts/update-repo.ps1` để tạo lại `Packages`, các bản nén, `Release` và `packages.json`.
4. Tạo một repository trống trên GitHub, rồi upload lần đầu:

   ```powershell
   ./scripts/publish.ps1 -RemoteUrl https://github.com/USERNAME/REPOSITORY.git
   ```

5. GitHub Pages phục vụ trực tiếp thư mục gốc của nhánh `main`. Script publish sẽ build lại metadata trước mỗi lần push.

URL thêm vào Sileo sẽ là `https://USERNAME.github.io/REPOSITORY/`. Các lần sau chỉ cần thêm/thay/xóa `.deb` và chạy `./scripts/publish.ps1`.

Nếu file deb dùng `control.tar.zst`, cài thêm `python -m pip install zstandard` trên máy local.
