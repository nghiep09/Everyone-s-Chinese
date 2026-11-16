# Học tiếng Trung 0.3.0

- App gốc dùng Python/Kivy, không dùng CSS. Giao diện được làm mới bằng Kivy Canvas, màu xanh, nền sáng, thẻ bo góc.
- Trang chủ: số bài ngữ pháp đạt >=60 điểm, điểm cao nhất từng bài cộng 10 điểm/mục từ vựng từng trả lời đúng; tiến độ = (mục từ đúng + bài ngữ pháp hoàn thành)/(tổng mục từ hiện tại + tổng bài ngữ pháp). Điểm lượt từ vựng cũ vẫn theo cơ chế cũ.
- Ngữ pháp: 6 cấp độ, 6 bài mẫu, 30 câu thuộc 5 dạng. Dữ liệu mẫu không phải giáo trình HSK đầy đủ.
- Nhập ngữ pháp: vào Ngữ pháp > Nhập Excel / JSON. Dùng assets/Grammar.xlsx hoặc assets/grammar.json làm mẫu. Giữ ID ổn định và duy nhất. Tokens và AcceptedAnswers trong Excel phân cách bằng |. Type: multiple_choice, fill_blank, reorder, zh_to_vi, vi_to_zh. Nhập thay toàn bộ bộ ngữ pháp, không thay bộ từ vựng. Các đáp án dịch khác cần khai báo AcceptedAnswers; không sử dụng AI để chấm.
- GitHub: tải assets/grammar.json lên repo công khai, mở file Raw, sao chép URL https://raw.githubusercontent.com/... vào Ngữ pháp > Tải JSON từ GitHub. App lưu URL và kiểm tra/tải lại khi mở; lỗi mạng giữ dữ liệu cũ. Nếu không muốn dữ liệu GitHub ghi đè dữ liệu nhập tay, tắt đồng bộ tự động. Không đưa dữ liệu cá nhân lên repo công khai.
- Ôn tập ngữ pháp: sai lưu ngay, ôn sau 10 phút; đúng liên tiếp 1/3/7/14/30 ngày. Có thể ôn toàn bộ ngay. Lưu tại progress.json trong thư mục riêng của app. Gỡ app có thể mất tiến độ.
- Phát âm Android dùng TTS hiện có; cần giọng tiếng Trung trên thiết bị. Desktop không có phát âm.
- Build Android: giữ package ID cũ, workflow .github/workflows/build-apk.yml. Push source lên GitHub, chạy workflow và tải APK từ Artifacts. Không có APK trong ZIP này.
- Kiểm tra logic: python -m unittest discover -s tests -v. Chạy desktop: pip install -r requirements-desktop.txt; python main.py. Môi trường tạo bản này không có Kivy/Android SDK nên chưa chạy giao diện hoặc build APK.
