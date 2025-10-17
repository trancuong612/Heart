import random
from math import sin, cos, pi, log
from tkinter import *

# ==== CẤU HÌNH ====
IMAGE_ENLARGE = 11
HEART_COLOR = "#f76070"
EXPLODE_TIME = 6000      # ms trước khi nổ
RESTART_DELAY = 1500     # ms chờ sau khi nổ xong trước khi tạo tim mới
FRAME_DELAY = 33         # ~30 FPS

# global sẽ được gán ở phần main
CANVAS_WIDTH = 640
CANVAS_HEIGHT = 480
CANVAS_CENTER_X = CANVAS_WIDTH / 2
CANVAS_CENTER_Y = CANVAS_HEIGHT / 2

def heart_function(t, shrink_ratio: float = IMAGE_ENLARGE):
    x = 16 * (sin(t) ** 3)
    y = -(13 * cos(t) - 5 * cos(2 * t) - 2 * cos(3 * t) - cos(4 * t))
    x *= shrink_ratio
    y *= shrink_ratio
    x += CANVAS_CENTER_X
    y += CANVAS_CENTER_Y
    return int(x), int(y)


def scatter_inside(x, y, beta=0.15):
    ratio_x = -beta * log(random.random())
    ratio_y = -beta * log(random.random())
    dx = ratio_x * (x - CANVAS_CENTER_X)
    dy = ratio_y * (y - CANVAS_CENTER_Y)
    return x - dx, y - dy


def shrink(x, y, ratio):
    force = -1 / (((x - CANVAS_CENTER_X) ** 2 + (y - CANVAS_CENTER_Y) ** 2) ** 0.6)
    dx = ratio * force * (x - CANVAS_CENTER_X)
    dy = ratio * force * (y - CANVAS_CENTER_Y)
    return x - dx, y - dy


def curve(p):
    # hàm nhịp mượt
    return 2 * sin(2 * p) * (sin(p) ** 2)


class Heart:
    def __init__(self, generate_frame=20):
        self._points = set()
        self._edge_diffusion_points = set()
        self._center_diffusion_points = set()
        self.all_points = {}
        self.generate_frame = generate_frame

        self.build(2000)

        # trạng thái nổ / fade
        self.exploded = False
        self.explode_particles = []  # khi nổ, chứa các hạt
        self.opacity = 0.0           # fade-in: 0..1

        # tiền tính các frame cho nhịp đập
        for frame in range(generate_frame):
            self.calc(frame)

    def build(self, number):
        for _ in range(number):
            t = random.uniform(0, 2 * pi)
            x, y = heart_function(t)
            self._points.add((x, y))

        for _x, _y in list(self._points):
            for _ in range(3):
                x, y = scatter_inside(_x, _y, 0.05)
                self._edge_diffusion_points.add((x, y))

        point_list = list(self._points)
        for _ in range(4000):
            x, y = random.choice(point_list)
            x, y = scatter_inside(x, y, 0.17)
            self._center_diffusion_points.add((x, y))

    @staticmethod
    def calc_position(x, y, ratio):
        force = 1 / (((x - CANVAS_CENTER_X) ** 2 + (y - CANVAS_CENTER_Y) ** 2) ** 0.52)
        dx = ratio * force * (x - CANVAS_CENTER_X) + random.randint(-1, 1)
        dy = ratio * force * (y - CANVAS_CENTER_Y) + random.randint(-1, 1)
        return x - dx, y - dy

    def calc(self, generate_frame):
        ratio = 10 * curve(generate_frame / 10 * pi)
        halo_radius = int(4 + 6 * (1 + curve(generate_frame / 10 * pi)))
        halo_number = int(3000 + 4000 * abs(curve(generate_frame / 10 * pi) ** 2))
        all_points = []

        heart_halo_point = set()
        for _ in range(halo_number):
            t = random.uniform(0, 2 * pi)
            x, y = heart_function(t, shrink_ratio=11.6)
            x, y = shrink(x, y, halo_radius)
            if (x, y) not in heart_halo_point:
                heart_halo_point.add((x, y))
                x += random.randint(-14, 14)
                y += random.randint(-14, 14)
                size = random.choice((1, 2, 2))
                all_points.append((x, y, size))

        for x, y in self._points:
            x, y = self.calc_position(x, y, ratio)
            size = random.randint(1, 3)
            all_points.append((x, y, size))

        for x, y in self._edge_diffusion_points:
            x, y = self.calc_position(x, y, ratio)
            size = random.randint(1, 2)
            all_points.append((x, y, size))

        for x, y in self._center_diffusion_points:
            x, y = self.calc_position(x, y, ratio)
            size = random.randint(1, 2)
            all_points.append((x, y, size))

        self.all_points[generate_frame] = all_points

    def explode(self):
        if self.exploded:
            return
        self.exploded = True
        self.explode_particles = []
        # dùng frame 0 như điểm xuất phát để có hình giống trước
        for x, y, size in self.all_points[0]:
            angle = random.uniform(0, 2 * pi)
            speed = random.uniform(4, 16)
            dx = speed * cos(angle)
            dy = speed * sin(angle)
            self.explode_particles.append([x, y, dx, dy, size])

    def render_normal(self, canvas, frame_index):
        """Vẽ trái tim ở trạng thái đập (không nổ).
           Áp dụng opacity khi fade-in."""
        opa = max(0.0, min(1.0, self.opacity))
        # map opacity -> simple color interpolation toward black:
        for x, y, size in self.all_points[frame_index % self.generate_frame]:
            # blend HEART_COLOR with black by opacity
            # HEART_COLOR is hex "#rrggbb"
            r = int(HEART_COLOR[1:3], 16)
            g = int(HEART_COLOR[3:5], 16)
            b = int(HEART_COLOR[5:7], 16)
            # multiply by opacity
            rr = int(r * opa)
            gg = int(g * opa)
            bb = int(b * opa)
            color = f"#{rr:02x}{gg:02x}{bb:02x}"
            canvas.create_rectangle(x, y, x + size, y + size, width=0, fill=color)

    def render_explode(self, canvas):
        new_particles = []
        for p in self.explode_particles:
            x, y, dx, dy, size = p
            x += dx
            y += dy
            dy += 0.25  # gravity
            size = max(0.5, size - 0.03)
            canvas.create_rectangle(x, y, x + size, y + size, width=0, fill=HEART_COLOR)
            # keep particles on screen
            if 0 < x < CANVAS_WIDTH and 0 < y < CANVAS_HEIGHT:
                new_particles.append([x, y, dx, dy, size])
        self.explode_particles = new_particles


# ---------- Animation controller ----------
current_heart = None
frame_counter = 0

def start_new_heart(root):
    """Tạo trái tim mới, schedule nổ sau EXPLODE_TIME"""
    global current_heart
    current_heart = Heart()
    current_heart.opacity = 0.0
    # schedule explosion
    root.after(EXPLODE_TIME, lambda: current_heart.explode())

def draw_frame(root, canvas):
    """Vẽ một frame và lên lịch cho frame tiếp theo"""
    global frame_counter, current_heart

    canvas.delete('all')

    if current_heart is None:
        start_new_heart(root)

    # nếu trái tim chưa nổ -> vẽ nhịp đập (frame tăng) và fade-in
    if not current_heart.exploded:
        # tăng opacity mượt đến 1
        if current_heart.opacity < 1.0:
            current_heart.opacity = min(1.0, current_heart.opacity + 0.03)
        # render normal using current frame
        current_heart.render_normal(canvas, frame_counter)
        frame_counter = (frame_counter + 1) % current_heart.generate_frame
        # tiếp tục vẽ
        root.after(FRAME_DELAY, lambda: draw_frame(root, canvas))
    else:
        # render explosion frames until particles list empty
        current_heart.render_explode(canvas)
        if current_heart.explode_particles:
            root.after(FRAME_DELAY, lambda: draw_frame(root, canvas))
        else:
            # nổ xong hoàn toàn -> đợi 1 khoảng và tạo tim mới
            root.after(RESTART_DELAY, lambda: (start_new_heart(root), draw_frame(root, canvas)))

# ---------- Main ----------
if __name__ == '__main__':
    root = Tk()
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()

    # cập nhật toạ độ toàn cục
    CANVAS_WIDTH = screen_w
    CANVAS_HEIGHT = screen_h
    CANVAS_CENTER_X = screen_w / 2
    CANVAS_CENTER_Y = screen_h / 2

    root.overrideredirect(True)
    root.geometry(f"{screen_w}x{screen_h}+0+0")
    root.config(bg='black')
    root.attributes('-topmost', True)

    canvas = Canvas(root, bg='black', height=screen_h, width=screen_w, highlightthickness=0)
    canvas.pack(fill="both", expand=True)

    # bind thoát (Ctrl+C / Esc) trong cửa sổ
    def quit_program(event=None):
        root.destroy()
    root.bind("<Control-c>", quit_program)
    root.bind("<Escape>", quit_program)

    # start
    start_new_heart(root)
    draw_frame(root, canvas)

    print("💖 Nhấn Ctrl + C hoặc Esc trong cửa sổ để thoát.")
    root.mainloop()
