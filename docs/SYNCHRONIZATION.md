# Kiến Trúc Đồng Bộ Hóa Whiteboard: Drawing Timeline & Hand Synchronization

Tài liệu này đặc tả cơ chế lõi của **Phase 08 — Drawing Timeline & Hand Synchronization**, hợp nhất 4 thành phần nền tảng:
```text
Narration Timing (TTS) + Visual Scene Graph + Assets + Drawing Strokes = Drawing Timeline
```

---

## 1. Mục Tiêu & Nguyên Lý Cốt Lõi

Trong video Whiteboard Animation, nét vẽ và bàn tay của họa sĩ không được xuất hiện ngẫu nhiên hoặc hiển thị theo mốc thời gian cố định (hardcoded timestamps). Toàn bộ nhịp điệu vẽ phải **nương theo từng âm tiết và ngữ nghĩa của giọng đọc thuyết minh (Narration Timing)**.

### Công Thức Đồng Bộ
$$\text{Narration Timing} + \text{Visual Scene Graph} + \text{Assets} + \text{Ordered Strokes} \longrightarrow \text{Drawing Timeline}$$

### 4 Nguyên Tắc Bắt Buộc
1. **Adaptive Duration (Không dùng thời lượng cứng)**: Thời lượng vẽ của từng đối tượng co giãn tự động theo tốc độ phát âm (Word/Sentence Timing) của TTS Provider.
2. **Semantic Cue Alignment**:
   - Âm thanh nhắc tới thực thể nào ("Con khỉ...") $\rightarrow$ thực thể đó bắt đầu được vẽ.
   - Âm thanh miêu tả hành động ("...đang trèo lên cây...") $\rightarrow$ cây và tư thế leo bám hoàn thiện.
   - Âm thanh chỉ mục tiêu tương tác ("...để lấy một quả chuối.") $\rightarrow$ nải chuối xuất hiện và tay với tới chuối.
3. **Continuous Hand Motion (Bàn tay vẽ liên tục)**:
   - Ngòi bút (Hand Nib) di chuyển dọc theo từng nét vẽ đang hoạt động ($p \in [0, 1]$).
   - Khi chuyển từ nét này sang nét khác hoặc từ đối tượng này sang đối tượng khác, bàn tay thực hiện thao tác **nhấc bút trên không (Hand Travel)** với đường cong cubic ease in-out tự nhiên, tuyệt đối không dịch chuyển tức thời (teleportation).
   - Không được xảy ra tình trạng: *bàn tay xuất hiện $\rightarrow$ ảnh hiện ra ngay $\rightarrow$ bàn tay biến mất*.
4. **Visual Progression & Monotonicity**:
   - **First Frame ($t=0$)**: Bảng trắng sạch sẽ, 0 nét vẽ hiển thị trước.
   - **During Drawing**: Bàn tay luôn xuất hiện và ngòi bút nằm sát nét vẽ đang hoạt động.
   - **Final Frame ($t \ge t_{end}$)**: 100% nét vẽ của toàn bộ các đối tượng trong phân cảnh hoàn thành, bàn tay êm dịu rút khỏi khung hình.

---

## 2. Kiến Trúc Dữ Liệu: DrawingTimeline & DrawingTimelineEvent

Được định nghĩa tại [`core/schemas/timeline.py`](file:///d:/Tool/core/schemas/timeline.py):

```python
class DrawingTimelineEvent(BaseModel):
    start_time: float = Field(ge=0.0, description="Mốc bắt đầu (giây)")
    end_time: float = Field(ge=0.0, description="Mốc kết thúc (giây)")
    asset_id: str = Field(description="Mã asset hoặc đối tượng (monkey, tree, banana)")
    stroke_id: str = Field(description="Mã nét vẽ hoặc mã đoạn travel")
    action: Literal["draw", "hand_travel", "erase", "pause"] = Field(default="draw")
    hand_path: List[Tuple[float, float]] = Field(description="Chuỗi tọa độ (x, y) trên canvas")
    semantic_purpose: str = Field(description="Mục đích ngữ nghĩa: head, body, trunk, leaves, travel,...")
    stroke_d: Optional[str] = Field(default=None, description="Chuỗi SVG path d trên canvas 1920x1080")
    stroke_width: float = Field(default=4.0)
    color_hex: str = Field(default="#1A1A1A")
    entity_id: Optional[str] = Field(default=None)
    points: List[Tuple[float, float]] = Field(default_factory=list)
```

### Các Phương Thức Truy Vấn Tức Thời
- `get_active_event_at(t)`: Trả về sự kiện đang thực thi tại thời điểm $t$.
- `get_drawn_strokes_at(t)`: Danh sách các nét vẽ đã hoàn thành tính đến mốc $t$.
- `get_hand_position_at(t)`: Tính toán vị trí $(x, y)$ của đầu ngòi bút tại mốc $t$, hỗ trợ nội suy mượt mà qua các điểm polyline.

---

## 3. Thuật Toán Phân Bổ Thời Gian (Time Budgeting Engine)

Triển khai trong [`core/timeline/synchronizer.py`](file:///d:/Tool/core/timeline/synchronizer.py):

### Bước 1: Phát Hiện Cụm Từ Ngữ Nghĩa (Phrase Alignment)
Hệ thống quét qua danh sách `WordTiming` từ TTS để xác định chính xác thời điểm bắt đầu $S_i$ của từng thực thể thông qua `_find_phrase_start`:
- `monkey`: Ghép cụm `"con khỉ"`, `"chú khỉ"` $\rightarrow$ mốc $t=0.10s$.
- `tree`: Ghép cụm `"trèo lên cây"`, `"trèo"` $\rightarrow$ mốc $t=1.10s$.
- `banana`: Ghép cụm `"lấy một quả chuối"`, `"lấy"` $\rightarrow$ mốc $t=2.45s$.

### Bước 2: Thiết Lập Cửa Sổ Thực Thể (Entity Time Windows)
Khung thời gian của thực thể $i$ được khoanh vùng nghiêm ngặt giữa mốc bắt đầu của nó và thực thể kế tiếp:
$$W_i = [S_i, S_{i+1}]$$
Thực thể cuối cùng kết thúc tại tổng thời lượng âm thanh $T_{audio}$:
$$W_{last} = [S_{last}, T_{audio}]$$
Nhờ đó, không có hiện tượng chồng lấn nét vẽ hoặc làm phình thời lượng ngoài ý muốn.

### Bước 3: Phân Bổ Ngân Sách Di Chuyển & Vẽ (Travel vs Draw Budget)
Trong mỗi cửa sổ $W_i$:
- Nếu có sự kiện di chuyển từ đối tượng trước tới đối tượng hiện tại:
  $$T_{inter} = \min(0.06s, T_{window} \times 0.08)$$
- Khoảng thời gian còn lại được chia tỉ lệ:
  - **12% cho di chuyển tay nội bộ (Internal Travel)** giữa các nét vẽ liên tiếp.
  - **88% cho thao tác hạ bút vẽ (Draw Budget)**.
- Thời lượng của từng nét vẽ tỉ lệ thuận với độ dài hình học của nét đó:
  $$T_{stroke\_j} = T_{draw\_budget} \times \frac{L_j}{\sum L}$$

---

## 4. Quỹ Đạo Bàn Tay (Hand Trajectory & Nib Calibration)

Tọa độ bàn tay được gắn chặt với đầu ngòi bút (pen nib):
- File đồ họa bàn tay: `assets/drawing-hand.png` ($320 \text{px}$).
- Tọa độ đầu ngòi bút nằm tại góc trên bên trái: $\Delta x = -18\text{px}, \Delta y = -14\text{px}$.
- Khi vẽ nét: Ngòi bút trượt dọc theo polyline của nét vẽ từ $P_0$ tới $P_n$.
- Khi nhấc bút: Ngòi bút di chuyển theo quỹ đạo đường cong làm mềm:
  $$P(t) = P_{start} + (3t^2 - 2t^3)(P_{end} - P_{start}) + (0, -15\sin(\pi t))$$
  Thành phần $-15\sin(\pi t)$ mô phỏng độ nhấc bút tự nhiên của cổ tay người thật.

---

## 5. Kết Quả Kiểm Tra Hồi Quy (Regression Test: Monkey-Banana Demo)

### Phân Cảnh Thử Nghiệm
- **Câu thoại**: *"Con khỉ đang trèo lên cây để lấy một quả chuối."*
- **Thời lượng âm thanh**: $4.50\text{s}$ (Tổng thời lượng timeline: $5.00\text{s}$ kèm padding).
- **Thực thể**:
  - `tree`: Cây dừa cao bên phải $(820, 80, 720, 880)$ gồm 23 nét vẽ.
  - `monkey`: Khỉ leo bám $(720, 400, 440, 440)$ gồm 22 nét vẽ.
  - `banana`: Nải chuối treo ngọn $(1120, 180, 240, 240)$ gồm 14 nét vẽ.
- **Tổng số nét vẽ**: 59 strokes (117 sự kiện gồm 59 draw + 58 travel).

### Kết Quả Visual Assertion
1. **First frames empty**: Tại $t=0.00s$, 0/59 nét vẽ, bảng trắng sạch $\rightarrow$ **PASS**.
2. **Monkey sync**: $t=0.10s \dots 1.10s$, khỉ bắt đầu được vẽ ngay khi phát âm "Con khỉ" $\rightarrow$ **PASS**.
3. **Tree sync**: $t=1.10s \dots 2.45s$, thân dừa và lá dừa được vẽ khi phát âm "trèo lên cây" $\rightarrow$ **PASS**.
4. **Banana sync**: $t=2.45s \dots 4.50s$, nải chuối xuất hiện ở ngọn cây khi phát âm "lấy quả chuối" $\rightarrow$ **PASS**.
5. **Hand proximity**: Bàn tay luôn bám sát nét vẽ với khoảng cách $< 2\text{px}$, không giật chuyển $\rightarrow$ **PASS**.
6. **Final frame**: $t \ge 5.00s$, 59/59 nét vẽ hoàn thành, bố cục đúng ngữ nghĩa $\rightarrow$ **PASS**.
