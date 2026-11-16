# Học tiếng Trung — dự án Android bằng Python

**Trạng thái:** Đây là mã nguồn Android và cấu hình tạo APK, chưa phải file APK cài ngay. Đã chạy 13 kiểm thử logic và kiểm thử giao diện Kivy ở kích thước điện thoại trên Linux. Chưa biên dịch thành công APK, chưa chạy trên Android thật; phần chọn tài liệu Android cần kiểm tra sau khi build.

Lần thử build trong môi trường tạo dự án dừng vì thiếu `javac` (Java compiler). Việc cài các phụ thuộc hệ thống cũng không được môi trường cho phép. Workflow GitHub Actions đi kèm cài các phụ thuộc trên máy Ubuntu của GitHub, nhưng workflow này chưa được chạy trong tài khoản của bạn.

## Chức năng đã viết

- Học từ vựng Trung → Việt hoặc Việt → Trung, 4 lựa chọn ngẫu nhiên khác nhau.
- Đáp án sai đỏ, đúng xanh; chỉ ghi điểm lần trả lời đầu tiên.
- Hiển thị chữ Hán, nghĩa, pinyin và Hán Việt sau khi trả lời.
- Ghép câu bằng cách chạm các mảnh; chạm mảnh đã chọn để trả lại; giữ đúng số lần xuất hiện của từ lặp.
- Chọn Excel qua trình chọn tài liệu Android; chọn sheet và có/không dòng tiêu đề.
- Lưu bộ học trong dữ liệu riêng của ứng dụng. Học offline sau khi nhập.
- Bộ mẫu và font chữ Hán đi kèm; không cần tải font khi học.
- Đếm đúng/tổng câu đã trả lời/bỏ qua. Không lặp câu trong một vòng.

## Cách lấy APK qua GitHub Actions

Bạn cần tài khoản GitHub. Thao tác tải thư mục lên dễ hơn trên máy tính. GitHub sẽ dùng máy chủ của họ để biên dịch; bạn không cần cài Python hay Android Studio để dùng cách này.

1. Giải nén gói dự án.
2. Tạo một repository mới trên GitHub (có thể để Private). Không đưa file Excel cá nhân lên repository; chỉ cần dữ liệu mẫu có sẵn trong dự án.
3. Tải **nội dung bên trong thư mục `Hoc_Tieng_Trung_Android`** lên thư mục gốc của repository. `main.py` và `buildozer.spec` phải nằm ngay ở trang gốc, không nằm trong một thư mục con nữa. Nhớ tải cả thư mục `.github`.
4. Kiểm tra đường dẫn `.github/workflows/build-apk.yml` có tồn tại trên nhánh mặc định. Nếu không thấy thư mục này khi tải lên, tạo file trên GitHub bằng **Add file → Create new file**, đặt tên đúng đường dẫn trên, rồi chép nội dung từ file cùng tên trong gói dự án.
5. Mở **Actions → Build Android APK → Run workflow → Run workflow**.
6. Khi lượt chạy có dấu xanh, mở lượt chạy đó. Trong phần **Artifacts**, tải **Hoc-Tieng-Trung-APK**.
7. Giải nén artifact vừa tải. Bên trong mới là file `.apk`.
8. Chuyển APK sang điện thoại, mở file để cài. Nếu Android hỏi, cho phép ứng dụng đang mở file cài đặt từ nguồn này.

Nếu lượt chạy báo đỏ, tải **Android-build-log** hoặc xem bước lỗi trong Actions để chẩn đoán. Không có APK nếu bước build thất bại. File workflow chỉ chạy khi bấm thủ công.

Đây là cấu hình APK debug để cài dùng cá nhân, không phải bản phát hành Google Play. Cấu hình nhắm ARM64, Android 6 trở lên (min API 23), target API 34, NDK 28c. Khả năng hoạt động thực tế còn cần xác nhận trên thiết bị. Không khẳng định hỗ trợ mọi máy Android chỉ từ cấu hình.

Các lượt build ở máy khác có thể dùng khóa debug khác nhau. Nếu cập nhật báo xung đột chữ ký, cần dùng cùng khóa ký hoặc gỡ bản cũ rồi cài lại. Gỡ ứng dụng sẽ xóa bộ học đã nhập; hãy giữ file Excel gốc.

## Excel của bạn

| Cột | Nội dung | Ví dụ |
|---|---|---|
| A | Chữ Hán | 学校 |
| B | Pinyin | xuéxiào |
| C | Nghĩa tiếng Việt | Trường học |
| D | Hán Việt | Học hiệu |

A/C bắt buộc, B/D có thể trống. Dữ liệu 3 cột cũ vẫn đọc được; khi thiếu D sẽ hiện “Chưa có dữ liệu ở cột D”. Hán Việt lấy nguyên văn từ cột D, không tự suy ra.

File `assets/du_lieu_mau.xlsx` là file 3 cột từ phiên bản desktop. Có thể thêm cột D và nhập Hán Việt vào đó. Bộ từ vựng mẫu tích hợp trong ứng dụng đã có Hán Việt trong `assets/vocab.json`; bộ ghép câu mẫu chưa điền Hán Việt.

Hỗ trợ `.xlsx` và `.xlsm` (chỉ đọc, không chạy macro). `.xls` cũ phải lưu lại thành `.xlsx`. Tối đa 20 MB và 20.000 dòng mỗi sheet. Bỏ dòng thiếu A/C, dòng nội dung trên 2.000 ký tự và cặp chữ Hán–nghĩa trùng; không tự gộp các cách đọc khác nhau của một cặp trùng. Nên dùng văn bản trực tiếp, công thức chỉ đọc kết quả đã được Excel lưu.

Từ vựng cần đủ 3 đáp án nhiễu khác nhau cho mỗi câu. Nếu cùng câu hỏi có nhiều đáp án trong dữ liệu, các đáp án thay thế không được dùng làm phương án sai. Câu không đủ phương án được bỏ qua.

Ghép câu: nhập A dạng `我 喜欢 学习 中文 。` để tạo các mảnh theo từ/cụm. Không có dấu cách thì tách từng ký tự. Chấm theo câu mẫu ở A, bỏ khoảng trắng nhưng giữ dấu câu. Những cách diễn đạt khác đúng ngữ pháp không được tự nhận diện.

## Cách dùng trên điện thoại sau khi cài

1. Mở ứng dụng để thử bộ từ vựng mẫu.
2. **Cài đặt** để chọn chế độ và hướng hỏi. **Dùng bài mẫu của chế độ này** thay bộ học hiện tại bằng mẫu từ vựng hoặc ghép câu.
3. **Chọn Excel** → chọn file → sheet → xác định dòng tiêu đề → **Bắt đầu học**.
4. Chạm đáp án hoặc ghép các mảnh rồi **Kiểm tra**.
5. Xem kết quả và bấm **Câu tiếp**. Có thể cuộn phần bài học khi nội dung dài.

Nhập Excel mới thay bộ học đang dùng, không sửa Excel gốc. Bộ học và lựa chọn chế độ được giữ sau khi tắt app; điểm lượt học đặt lại khi mở app. Muốn cập nhật dữ liệu sau khi chỉnh Excel, nhập lại file. File từ dịch vụ đám mây nên tải về máy trước để chọn và học offline.

## Chạy thử mã Python trên máy tính

Python 3.12:

```sh
python -m pip install -r requirements-desktop.txt
python main.py
```

Kiểm thử logic:

```sh
python -m unittest discover -s tests -v
```

Kiểm thử giao diện trên máy có màn hình:

```sh
python tests/ui_smoke.py
```

Trên Linux có SDL offscreen/Mesa, có thể dùng `SDL_VIDEODRIVER=offscreen`. Kiểm thử này không thay thế kiểm thử Android.

## Build APK tại máy tính (tùy chọn)

Chạy Buildozer trong Ubuntu 24.04 hoặc WSL2 Ubuntu trên Windows. Dự án đặt trong filesystem Linux (ví dụ `~/Hoc_Tieng_Trung_Android`), không build trực tiếp dưới `/mnt/c`.

```sh
sudo apt update
sudo apt install -y git zip unzip openjdk-17-jdk python3-venv python3-pip autoconf automake libtool libltdl-dev pkg-config zlib1g-dev libncurses-dev libtinfo6 cmake libffi-dev libssl-dev autopoint gettext
python3 -m venv .venv
source .venv/bin/activate
pip install buildozer==1.6.0 setuptools cython==0.29.34
buildozer -v android debug
```

APK sau khi build thành công nằm trong `bin/`. Lần đầu cần mạng để tải SDK, NDK và các thư viện. `android.accept_sdk_license=True` được đặt trong cấu hình; khi chạy build bạn cần chấp nhận điều khoản SDK tương ứng.

## Cấu trúc mã

| File/thư mục | Vai trò |
|---|---|
| `main.py` | Giao diện Kivy cho thao tác chạm |
| `learning.py` | Đọc Excel, trộn câu, tạo đáp án, chấm điểm, lưu bộ học |
| `android_picker.py` | Mở trình chọn tài liệu Android và nhận kết quả |
| `android_src/vn/hoctiengtrung/DocumentCopy.java` | Sao chép file được chọn vào vùng dữ liệu riêng của ứng dụng |
| `assets/` | Font, giấy phép font, bộ mẫu và Excel mẫu |
| `buildozer.spec` | Cấu hình đóng gói APK |
| `.github/workflows/build-apk.yml` | Quy trình build trên GitHub Actions |
| `tests/` | Kiểm thử logic và giao diện |
| `docs/` | Ảnh giao diện kiểm tra ở kích thước điện thoại |

Phần học và giao diện viết bằng Python. Java chỉ là cầu nối nhỏ để đọc file do người dùng chọn qua Android; không xin quyền truy cập toàn bộ bộ nhớ. Không có mã gửi dữ liệu học lên máy chủ.

## Nguồn kỹ thuật và giấy phép font

- Buildozer: https://buildozer.readthedocs.io/en/latest/installation/
- Android API qua python-for-android: https://python-for-android.readthedocs.io/en/latest/apis.html
- Chạy workflow: https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow
- Tải artifact: https://docs.github.com/en/actions/how-tos/manage-workflow-runs/download-workflow-artifacts
- Noto Sans SC: https://github.com/notofonts/noto-cjk ; giấy phép OFL kèm trong `assets/OFL.txt`.
