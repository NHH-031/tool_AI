import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from core.artwork.gemini_director import GeminiScriptDirector

idea = """Cái bụng của Hải réo lên một tràng dài như tiếng sấm giữa trưa hè oi ả. Cậu nằm bẹp dí trên chiếc nệm mỏng trong căn phòng trọ mười lăm mét vuông, nhìn trần nhà ngập ngụa mạng nhện mà thấy tương lai tăm tối không kém. Lục tung khắp các xó xỉnh, kết quả thu về chỉ là một gói mì tôm rỗng không, nửa củ hành tây đã lên mốc ở góc bếp, và cái ví lép xẹp chỉ còn trơ trọi một tờ mười nghìn rách góc cùng hai cái cúc áo kim loại. Nhận thức được việc nếu tiếp tục nằm yên thì đến tối sẽ có người phải đến khiêng xác, Hải đành lết cái thân tàn tạ, xỏ đôi dép tổ ong cọc cạch chiếc vàng chiếc trắng rồi lê từng bước ra khỏi cửa.
Mục tiêu duy nhất của cậu lúc này là tiệm tạp hóa đầu ngõ của ông Sáu. Đến nơi, đập vào mắt cậu là ông Sáu đang ngồi vắt chân chữ ngũ trên ghế bố, tay phe phẩy cái quạt nan rách mép, mắt lim dim canh chừng con mèo Tủn béo ú đang ngáy khò khè đè bẹp cả bao gạo lứt. Hải bước vào, bám lấy mép tủ kính, giọng thều thào như người sắp tắt thở, xin mua thiếu một ổ bánh mì với bịch sữa đậu nành, hẹn mai có tiền thì trả nốt năm nghìn còn thiếu.
Ông Sáu nghe thế liền kéo tụt cái kính lão xuống sống mũi, liếc Hải bằng nửa con mắt rồi tuyên bố chắc nịch rằng sổ nợ đã hết chỗ ghi. Tuy nhiên, nhìn bộ dạng đói lả của thằng nhóc, ông buông một câu điều kiện: nếu Hải chịu quét sạch đống lá rụng ngoài sân và tóm được con chuột cống đang lộng hành trong kho, ông sẽ bao trọn gói một ổ bánh mì kẹp chả giò ngập sốt. Nghe đến hai chữ "kẹp chả", mắt Hải sáng rực như đèn pha ô tô, lập tức giật phắt cây chổi đóm trên tay ông già rồi xông thẳng vào kho.
Nhưng đời vốn không như là mơ. Căn kho tối om nồng nặc mùi mắm muối, Hải vừa bước vào thì một cái bóng đen sì lông lá đã phóng vút qua chân. Quá hoảng hốt, cậu hét toáng lên một tiếng thất thanh rồi vung chổi loạn xạ như múa võ, để rồi trượt chân ngã dập mông ê ẩm xuống sàn gạch. Cú ngã kéo theo một bao trấu trên kệ rơi uỵch xuống đất, đè trúng đuôi con chuột khiến nó hoảng loạn phi thục mạng ra phía cửa. Con Tủn ngoài cửa tiệm đang ngủ say giật mình nhảy cẫng lên trời, tiện chân đá văng cái bát nhôm đựng nước bay thẳng vào ngón chân cái của ông Sáu. Tiếng la hét, tiếng bát vỡ cùng tiếng chửi ầm ĩ của ông già xé toạc buổi trưa yên tĩnh.
Mười lăm phút sau, trận hỗn chiến cũng ngã ngũ. Con chuột đã biến mất không còn dấu vết, còn Hải thì ngồi bệt ở bậc thềm trước cửa, cả người dính đầy bụi bặm và mạng nhện, một tay xoa xoa cái mông ê ẩm, tay kia cầm ổ bánh mì kẹp chả cắn ngập răng. Hương vị pate béo ngậy hòa cùng sốt cay xè xua tan sạch sẽ nỗi nhục vừa xong. Con Tủn béo ục ịch lò dò bước lại gần, dụi đầu vào ống quần cậu kêu meo meo nịnh nọt. Hải cười hề hề, bẻ một mẩu chả ném cho nó rồi tợp một ngụm sữa đậu nành mát lạnh, cảm thán trong bụng rằng hóa ra lao động chân chính cũng có giá của nó. Sau lưng cậu, ông Sáu đứng khoanh tay dựa cửa, nhìn bộ dạng nhếch nhác ấy mà chỉ biết lắc đầu thở dài, làu bàu dặn ăn cho lẹ rồi lo mà ra quét nốt cái sân lá rụng."""

scenes = GeminiScriptDirector.create_storyboard(idea, target_scenes=4, target_duration_sec=60.0)
print(f"Total scenes: {len(scenes)}")
for s in scenes:
    print(f"\n--- Scene {s.scene_index}: {s.title}")
    print(f"    Narration: {s.narration}")
    print(f"    Visual Prompt: {s.visual_prompt}")
