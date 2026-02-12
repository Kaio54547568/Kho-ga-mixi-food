Tất cả tài nguyên hình ảnh (sprite) trong game nên được đặt trong thư mục này.

Hiện tại game chỉ vẽ hình chữ nhật / hình tròn bằng `pygame.draw`, KHÔNG sử dụng file ảnh,
để đảm bảo không phụ thuộc asset ngoài.

Nếu bạn muốn thay thế bằng sprite trong tương lai, gợi ý cấu trúc:

- `player.png`          - hình xe người chơi
- `enemy_normal.png`    - kẻ địch thường
- `enemy_level2.png`    - kẻ địch cấp 2
- `enemy_special.png`   - kẻ địch đặc biệt
- `pickup_ammo.png`     - pickup đạn
- `pickup_hp.png`       - pickup máu

Sau đó, bạn có thể sửa code (ví dụ trong `entities.py` / `player.py`) để load và vẽ surface
thay vì dùng `pygame.draw`.

