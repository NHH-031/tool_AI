# TÀI LIỆU QUY CHUẨN THỊ GIÁC: WHITEBOARD ART & RENDER REFERENCE
*(Trích xuất và chuẩn hóa trực tiếp từ `geeklee/srt-whiteboard-animation`)*

## 1. Bản chất cốt lõi (Core Philosophy)
Whiteboard Animation chất lượng cao là sự kết hợp chặt chẽ giữa:
1. **Source Artwork (Hình minh họa nguồn)**: Hình vẽ vector/line-art hoàn chỉnh mang phong cách phác thảo doodle tối giản nhưng giàu biểu cảm (tương tự mỹ học vẽ tay tinh tế của Notion).
2. **Stream Progressive Drawing (Bộ kết xuất nét vẽ liên tục)**: Đầu bút lông đen di chuyển mượt mà trên nền giấy kem ấm, phủ nét phác thảo (`ink`), sau đó điểm xuyết màu nhấn (`color`), tuân thủ nghiêm ngặt thứ tự kể chuyện.

---

## 2. Quy chuẩn thị giác thống nhất (Unified Visual Specification)

### 2.1. Nền giấy & Tông màu (Color & Medium)
- **Nền giấy bắt buộc**: Giấy kem ấm cũ (Warm cream paper), mã màu khuyến nghị `#F5EBD7` (RGB: `245, 235, 215` / BGR: `215, 235, 245`).
- **Nghiêm cấm**: Nền trắng tinh chói gắt (`#FFFFFF`) hoặc nền xám lạnh.
- **Nét vẽ chủ đạo (Primary Line)**: Màu than chì đậm / đen phác thảo (`#1A1A1A`), đường nét sạch, có chủ ý, độ dày nét đồng nhất (5.0px - 7.0px trên canvas 1080p).
- **Màu nhấn hạn chế (Restricted Accents)**: Chỉ cho phép tối đa 3 màu khái niệm:
  - **Đỏ (#E05A47)**: Nhấn mạnh cảnh báo, điểm dừng, quả chín, quả bóng.
  - **Cam (#E67E22)**: Nhấn mạnh năng lượng, chuyển động, ánh nắng.
  - **Xanh lam (#3498DB)**: Nhấn mạnh nước, quỹ đạo, công nghệ, bầu trời.
- **Tuyệt đối cấm**: Bảng màu sặc sỡ, độ bão hòa cao, gradient lòe loẹt, hoa văn phức tạp.

### 2.2. Nhân vật & Đối tượng (Character & Object Quality)
- **Nguyên tắc "Few but Intentional Strokes"**: Tối giản KHÔNG đồng nghĩa với sơ sài (Minimal != Shoddy).
  - Không vẽ người que (stick figures) gầy guộc vô hồn.
  - Không vẽ động vật chỉ gồm hình tròn và 4 que thẳng.
  - Mọi nhân vật phải có **silhouette nhận diện rõ nét**: đầu, mắt/biểu cảm, thân thể, 4 chi và đuôi cân đối theo phong cách hoạt họa thanh lịch.
- **Độ đọc được của hành động (Action Readability)**: Tư thế (pose) của nhân vật và bố cục phải truyền tải ngay hành động:
  - *Mèo leo cây*: Mèo vươn mình, 4 chân và móng vuốt bám trực tiếp thân cây, lưng cong lực leo.
  - *Chó đuổi bóng*: Chó chân sải dài ở tư thế chạy, hướng về quả bóng phía trước có vệt lăn.
  - *Nông dân trồng cây*: Nông dân cúi người, tay cầm cây non chạm luống đất.
  - *Trái Đất quay Mặt Trời*: Mặt Trời tỏa tia sáng ở trung tâm, Trái Đất có trục nghiêng nằm trên đường elip quỹ đạo.
- **Bố cục & Khoảng trống âm (Composition & Negative Space)**:
  - Đối tượng chính đặt ở vùng trọng tâm, kích thước vừa phải (chiếm 30% - 60% chiều cao canvas).
  - Khoảng trống âm (negative space) rộng rãi, thoáng đãng, không bị ngột ngạt.
  - Không có đối tượng bị cắt mép khung hình.

### 2.3. Điều cấm kỵ tuyệt đối (Strict Negative Constraints)
- **KHÔNG chữ / typography**: Nghiêm cấm tạo chữ, nhãn, số, ký tự trong hình minh họa cảnh (trừ trường hợp logo trên thân bút `drawing-hand.png`).
- **KHÔNG phong cách 3D / Realistic**: Nghiêm cấm ảnh chụp tả thực, bóng đổ 3D phức tạp, kết cấu sơn dầu/màu nước loang lổ.
- **KHÔNG chi tiết rác / Watermark**: Không có watermark, ký hiệu vô nghĩa, nét thừa chồng chéo.

---

## 3. Quy chuẩn kết xuất Whiteboard (Renderer Execution Standards)

| Thuộc tính | Tùy chọn | Khuyến nghị & Trường hợp áp dụng |
|---|---|---|
| **Nền Canvas** | `#F5EBD7` | Luôn áp dụng màu kem ấm, lấy mẫu đồng nhất |
| **Đường dẫn nét vẽ (`--ink-path`)** | `skeleton` vs `grid` | Dùng `skeleton` cho tranh line-art vector sạch (bám khung xương); dùng `grid` làm fallback ổn định khi nét vẽ dày |
| **Phong cách lên màu (`--color-fill`)** | `contour-wipe` vs `brush` | `contour-wipe` cho hiệu ứng quét màu tự nhiên; `brush` cho phong cách cọ vẽ theo quỹ đạo |
| **Tỷ lệ pha vẽ (`ink : color`)** | `2 : 1` | 67% thời lượng dành cho vẽ nét viền, 33% thời lượng lên màu điểm xuyết |
| **Bảo vệ vùng vẽ (`protectedRegions`)** | Bounding box mask | Giữ các vùng chưa đến lượt vẽ hoàn toàn ẩn, không lộ nét sớm |
| **Đồng bộ âm thanh - hình ảnh** | Silence Padding | Bù silence vào audio stream để `duration_delta = 0.0s`, triệt tiêu drift |
| **Giữ khung hình cuối** | `>= 0.5s` | Giữ nguyên vẹn 100% hình minh họa ở cuối cảnh để người xem chiêm ngưỡng |

---

## 4. Ngân sách chi tiết theo thứ bậc (Detail Budget Architecture)
Mỗi phân cảnh có ngân sách chi tiết phân bổ có chủ đích:
1. **Chủ thể chính (Main Character)**: Ngân sách cao (High) — Ưu tiên hình thái, cử chỉ hành động, nét mặt, điểm bám tiếp xúc.
2. **Đối tượng tương tác (Interaction Target)**: Ngân sách trung bình (Medium) — Đặc trưng loài cây/đồ vật rõ ràng.
3. **Mặt đất / Khung cảnh cơ bản (Ground / Environment)**: Ngân sách thấp (Low) — Đường chân trời, mô đất tối giản.
4. **Họa tiết trang trí (Decorations)**: Tối thiểu (Minimal) — Chỉ thêm khi phục vụ trực tiếp câu chuyện.
