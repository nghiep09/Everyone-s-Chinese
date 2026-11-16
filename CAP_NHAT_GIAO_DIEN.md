# Giao diện xanh ngọc – phiên bản 0.2.0

Bản mã Python/Kivy dành cho ứng dụng Android học tiếng Trung, thiết kế theo ảnh tham chiếu: nền kem, các thẻ trắng bo góc, tab chế độ, thanh tiến độ, ô ghép chữ, khung phản hồi xanh/đỏ và điều hướng cuối màn hình.

## Cập nhật repository hiện tại

1. Giải nén ZIP.
2. Thay file `main.py` trong repository bằng file mới.
3. Thêm `assets/transparent.png` vào đúng thư mục `assets`. File này dùng cho nền nút bo góc.
4. Thay `android_picker.py` bằng bản kèm theo nếu chưa áp dụng bản sửa chọn Excel.
5. Có thể dùng `buildozer.spec` đi kèm (version 0.2.0, minapi/ndk_api 24, p4a.branch develop). Nếu đã có cấu hình riêng, giữ cấu hình đó và bảo đảm đưa tài nguyên png vào APK.
6. Commit changes vào main. Vào Actions → Build Android APK → Run workflow → main để chạy lượt mới.
7. Tải artifact Hoc-Tieng-Trung-APK, giải nén và cài APK mới.

Các thư mục và file khác được kèm để có đủ mã nguồn dự án. Không cần tạo repository mới. Không thay toàn bộ repository nếu bạn đã tự bổ sung chức năng ngoài bản gốc.

## Chức năng

- Excel .xlsx/.xlsm: A chữ Hán, B Pinyin, C nghĩa tiếng Việt, D Hán Việt tùy chọn; chọn sheet và dòng tiêu đề.
- Từ vựng hai hướng hỏi: chọn trong Cài đặt.
- Ghép từ/câu: chạm để chọn và chạm lại để trả mảnh; kiểm tra sau khi chọn đủ.
- Tô màu đáp án đúng/sai, hiển thị chữ Hán, Pinyin, nghĩa và Hán Việt.
- Bộ từ: xem tối đa 200 mục đầu để giữ giao diện nhẹ; toàn bộ dữ liệu vẫn tham gia luyện tập.
- Tab chuyển chế độ giữ bộ dữ liệu và bắt đầu lượt mới. Bài mẫu riêng từng chế độ nằm trong Cài đặt.
- Thanh tiến độ tính số câu đã trả lời hoặc bỏ qua trong một vòng trên các câu đủ điều kiện; điểm đúng/sai/bỏ qua cộng dồn trong lượt học. Điểm đặt lại khi mở lại ứng dụng hoặc đổi chế độ.
- Các thẻ nằm trong vùng cuộn để dùng được trên màn hình nhỏ. Nút chuyển câu và điều hướng nằm cố định bên dưới.

## Kiểm tra

Đã qua 13 kiểm tra logic và kiểm tra giao diện Kivy trên máy tính: tô màu đúng/sai, khóa điểm sau trả lời, Hán Việt, chọn/trả mảnh, chấm ghép câu và mở Cài đặt. Ảnh thực tế của giao diện máy tính nằm trong docs.

Chưa biên dịch và thử bản APK giao diện mới trên điện thoại trong môi trường này. Cần kiểm tra nhập Excel và hiển thị trên thiết bị sau khi GitHub build xong. Đây là mã nguồn để build, không phải APK hay bản phát hành CH Play.
