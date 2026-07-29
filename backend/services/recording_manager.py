"""
Manages recording sessions for building custom voice profiles.
Users record multiple sentences to build a higher-quality voice.
"""

import json
import tempfile
from pathlib import Path
from typing import Optional

from pydub import AudioSegment

from backend.config import RECORDINGS_DIR, SCRIPTS_FILE


class RecordingManager:

    def get_scripts(self) -> list[dict]:
        """Return the list of scripts for recording."""
        if not SCRIPTS_FILE.exists():
            return self._generate_default_scripts()
        return json.loads(SCRIPTS_FILE.read_text(encoding="utf-8"))

    def _generate_default_scripts(self) -> list[dict]:
        """Generate default Vietnamese recording scripts."""
        scripts = [
            {"text": "Bầu trời hôm nay trong xanh và rực rỡ, những đám mây trắng nhẹ nhàng trôi lững lờ giữa không gian bao la và yên tĩnh."},
            {"text": "Chiếc xe buýt chậm rãi lăn bánh qua từng con phố nhỏ, mang theo tiếng cười nói của những hành khách đang trên đường trở về nhà."},
            {"text": "Quán cà phê nhỏ góc phố luôn tấp nập vào buổi sáng, hương cà phê lan tỏa khắp không gian khiến ai đi qua cũng muốn dừng lại."},
            {"text": "Cuộc sống không phải lúc nào cũng dễ dàng, nhưng điều quan trọng là ta không bao giờ từ bỏ hy vọng vào ngày mai tươi sáng hơn."},
            {"text": "Mỗi người có một con đường riêng, và điều đáng quý nhất là họ dám sống thật với chính mình, dù con đường ấy khác biệt."},
            {"text": "Chào bạn, hôm nay bạn cảm thấy thế nào? Mình mong là bạn đã có một ngày thật tuyệt vời và tràn đầy năng lượng."},
            {"text": "Cảm ơn bạn đã đến, sự hiện diện của bạn là niềm vinh hạnh lớn đối với chúng tôi trong buổi gặp mặt hôm nay."},
            {"text": "Tôi tin rằng sự tử tế, dù là nhỏ nhất, cũng có thể tạo nên sự thay đổi lớn lao trong lòng người khác."},
            {"text": "Khi bạn lắng nghe ai đó bằng cả trái tim, bạn không chỉ nghe âm thanh mà còn hiểu được cảm xúc sâu xa bên trong họ."},
            {"text": "Trời đổ mưa rả rích từ sáng sớm, từng giọt nước nhỏ xuống mái hiên tạo nên bản nhạc nền dịu dàng cho một buổi sáng tĩnh lặng."},
            {"text": "Căn phòng nhỏ tràn ngập ánh nắng vàng nhạt, mùi bánh mì mới nướng và tiếng nhạc nhẹ khiến không khí thật ấm cúng và dễ chịu."},
            {"text": "Bữa cơm gia đình đơn giản nhưng ấm áp, nơi tiếng cười, tiếng hỏi han và những câu chuyện nhỏ xóa tan mọi mệt mỏi trong ngày."},
            {"text": "Trên con đường làng uốn lượn giữa cánh đồng lúa xanh mướt, lũ trẻ chạy nhảy tung tăng, tiếng cười vang vọng khắp không gian bình dị."},
            {"text": "Nếu có thể quay ngược thời gian, bạn sẽ thay đổi điều gì trong quá khứ hay vẫn chọn giữ nguyên mọi thứ như hiện tại?"},
            {"text": "Công nghệ phát triển nhanh chóng đã thay đổi hoàn toàn cách chúng ta làm việc, giao tiếp và giải trí trong cuộc sống hàng ngày."},
            {"text": "Một buổi chiều yên bình bên tách trà nóng, ngắm nhìn hoàng hôn từ từ buông xuống phía chân trời xa là khoảnh khắc đáng trân quý."},
            {"text": "Âm nhạc có sức mạnh kỳ diệu, nó có thể chữa lành những vết thương trong tâm hồn mà không cần bất kỳ lời nói nào."},
            {"text": "Hãy luôn mỉm cười vì nụ cười không chỉ làm đẹp khuôn mặt bạn mà còn sưởi ấm trái tim của những người xung quanh."},
            {"text": "Sách là người bạn tốt nhất, luôn ở bên bạn mỗi khi bạn cần, mang đến tri thức và niềm vui không bao giờ cạn kiệt."},
            {"text": "Mùa xuân đến mang theo hơi ấm dịu dàng, cây cối đâm chồi nảy lộc, muôn hoa khoe sắc rực rỡ khắp mọi nẻo đường."},
            {"text": "Biển xanh mênh mông trải dài tận chân trời, từng con sóng vỗ nhẹ vào bờ cát trắng tạo nên giai điệu êm đềm bất tận."},
            {"text": "Những ngôi sao lấp lánh trên bầu trời đêm như hàng triệu viên kim cương được ai đó rải xuống từ thiên đường xa xôi."},
            {"text": "Tiếng chim hót líu lo trên cành cây mỗi buổi sáng sớm là lời chào đón ngày mới tươi đẹp và đầy hy vọng."},
            {"text": "Con đường phía trước có thể dài và gian nan, nhưng chỉ cần bạn kiên trì bước đi thì đích đến sẽ không còn xa."},
            {"text": "Tình bạn chân thành là món quà quý giá nhất mà cuộc đời ban tặng, hãy trân trọng và gìn giữ những người bạn tốt bên mình."},
        ]
        SCRIPTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        SCRIPTS_FILE.write_text(json.dumps(scripts, ensure_ascii=False, indent=2), encoding="utf-8")
        return scripts

    def save_recording(self, voice_id: str, index: int, audio_bytes: bytes, filename: str) -> dict:
        """
        Save a recording for a voice profile.
        Converts webm to wav if needed.
        """
        rec_dir = RECORDINGS_DIR / voice_id
        rec_dir.mkdir(parents=True, exist_ok=True)

        wav_name = f"{index:03d}.wav"
        wav_path = rec_dir / wav_name

        # Convert from webm/other format to wav
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(filename).suffix) as tmp:
            tmp.write(audio_bytes)
            tmp.flush()
            audio = AudioSegment.from_file(tmp.name)
            audio.export(str(wav_path), format="wav")
            Path(tmp.name).unlink(missing_ok=True)

        return {
            "index": index,
            "filename": wav_name,
            "duration_sec": round(len(audio) / 1000.0, 1),
        }

    def get_recorded_indices(self, voice_id: str) -> list[int]:
        """Return list of sentence indices that have been recorded."""
        rec_dir = RECORDINGS_DIR / voice_id
        if not rec_dir.exists():
            return []

        indices = []
        for f in rec_dir.glob("*.wav"):
            try:
                idx = int(f.stem)
                indices.append(idx)
            except ValueError:
                continue
        return sorted(indices)

    def delete_recording(self, voice_id: str, index: int) -> bool:
        wav_path = RECORDINGS_DIR / voice_id / f"{index:03d}.wav"
        if wav_path.exists():
            wav_path.unlink()
            return True
        return False


recording_manager = RecordingManager()
