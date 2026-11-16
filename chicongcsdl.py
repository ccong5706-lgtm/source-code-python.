
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
from datetime import datetime

# ==============================
# 1. KHOI TAO CO SO DU LIEU
# ==============================

conn = sqlite3.connect("cafe.db")
conn.execute("PRAGMA foreign_keys = ON")
cursor = conn.cursor()

cursor.executescript("""
CREATE TABLE IF NOT EXISTS DanhMuc (
    MaDM INTEGER PRIMARY KEY AUTOINCREMENT,
    TenDM TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS SanPham (
    MaSP INTEGER PRIMARY KEY AUTOINCREMENT,
    TenSP TEXT NOT NULL,
    MaDM INTEGER NOT NULL,
    DonGia REAL NOT NULL CHECK(DonGia > 0),
    TrangThai TEXT DEFAULT 'Đang bán'
        CHECK(TrangThai IN ('Đang bán', 'Ngừng bán')),
    FOREIGN KEY(MaDM) REFERENCES DanhMuc(MaDM)
);

CREATE TABLE IF NOT EXISTS Ban (
    MaBan INTEGER PRIMARY KEY AUTOINCREMENT,
    TenBan TEXT NOT NULL UNIQUE,
    SoCho INTEGER NOT NULL CHECK(SoCho > 0),
    TrangThai TEXT DEFAULT 'Trống'
);

CREATE TABLE IF NOT EXISTS KhachHang (
    MaKH INTEGER PRIMARY KEY AUTOINCREMENT,
    HoTen TEXT NOT NULL,
    SDT TEXT UNIQUE,
    Email TEXT,
    NgayTao TEXT
);

CREATE TABLE IF NOT EXISTS DonHang (
    MaDH INTEGER PRIMARY KEY AUTOINCREMENT,
    MaBan INTEGER NOT NULL,
    MaKH INTEGER,
    ThoiGianTao TEXT NOT NULL,
    ThoiGianTT TEXT,
    TongTien REAL DEFAULT 0,
    GiamGia REAL DEFAULT 0,
    TrangThai TEXT DEFAULT 'Chờ thanh toán',
    FOREIGN KEY(MaBan) REFERENCES Ban(MaBan),
    FOREIGN KEY(MaKH) REFERENCES KhachHang(MaKH)
);

CREATE TABLE IF NOT EXISTS ChiTietDonHang (
    MaCT INTEGER PRIMARY KEY AUTOINCREMENT,
    MaDH INTEGER NOT NULL,
    MaSP INTEGER NOT NULL,
    SoLuong INTEGER NOT NULL CHECK(SoLuong > 0),
    DonGia REAL NOT NULL CHECK(DonGia > 0),
    ThanhTien REAL NOT NULL,
    FOREIGN KEY(MaDH) REFERENCES DonHang(MaDH),
    FOREIGN KEY(MaSP) REFERENCES SanPham(MaSP)
);
""")

# Du lieu mau
cursor.execute("SELECT COUNT(*) FROM DanhMuc")
if cursor.fetchone()[0] == 0:
    cursor.executemany(
        "INSERT INTO DanhMuc(TenDM) VALUES (?)",
        [("Cà phê",), ("Trà",), ("Nước ép",), ("Bánh ngọt",)]
    )

cursor.execute("SELECT COUNT(*) FROM SanPham")
if cursor.fetchone()[0] == 0:
    cursor.executemany("""
        INSERT INTO SanPham(TenSP, MaDM, DonGia)
        VALUES (?, ?, ?)
    """, [
        ("Cà phê đen", 1, 20000),
        ("Cà phê sữa", 1, 25000),
        ("Bạc xỉu", 1, 30000),
        ("Trà đào", 2, 35000),
        ("Trà chanh", 2, 20000),
        ("Nước cam", 3, 30000),
        ("Bánh ngọt", 4, 25000)
    ])

cursor.execute("SELECT COUNT(*) FROM Ban")
if cursor.fetchone()[0] == 0:
    cursor.executemany("""
        INSERT INTO Ban(TenBan, SoCho) VALUES (?, ?)
    """, [(f"Bàn {i}", 4) for i in range(1, 11)])

conn.commit()


# ==============================
# 2. HAM HO TRO
# ==============================

def query(sql, params=()):
    return conn.execute(sql, params).fetchall()


def refresh_all():
    load_products()
    load_tables()
    load_customers()
    load_orders()
    load_reports()


def clear_tree(tree):
    for item in tree.get_children():
        tree.delete(item)


# ==============================
# 3. GIAO DIEN CHINH
# ==============================

root = tk.Tk()
root.title("HỆ THỐNG QUẢN LÝ QUÁN CÀ PHÊ")
root.geometry("1150x720")
root.minsize(950, 600)
root.configure(bg="#F5F1E8")

style = ttk.Style()
style.theme_use("clam")
style.configure(
    "Treeview",
    rowheight=30,
    font=("Arial", 10)
)
style.configure(
    "Treeview.Heading",
    font=("Arial", 10, "bold")
)
style.configure(
    "TNotebook.Tab",
    font=("Arial", 10, "bold"),
    padding=10
)

header = tk.Frame(root, bg="#51372B", height=80)
header.pack(fill="x")

tk.Label(
    header,
    text="☕ QUẢN LÝ QUÁN CÀ PHÊ",
    font=("Arial", 23, "bold"),
    fg="white",
    bg="#51372B"
).pack(pady=20)

notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True, padx=10, pady=10)


# ==============================
# 4. TAB QUAN LY SAN PHAM
# ==============================

tab_product = ttk.Frame(notebook)
notebook.add(tab_product, text="Thực đơn")

tk.Label(
    tab_product, text="QUẢN LÝ THỰC ĐƠN",
    font=("Arial", 16, "bold")
).pack(pady=10)

frame_product = ttk.Frame(tab_product)
frame_product.pack(fill="x", padx=15)

tk.Label(frame_product, text="Tên sản phẩm:").grid(row=0, column=0)
entry_product = ttk.Entry(frame_product, width=25)
entry_product.grid(row=0, column=1, padx=5)

tk.Label(frame_product, text="Danh mục:").grid(row=0, column=2)
combo_category = ttk.Combobox(
    frame_product,
    values=["Cà phê", "Trà", "Nước ép", "Bánh ngọt"],
    state="readonly",
    width=15
)
combo_category.grid(row=0, column=3, padx=5)
combo_category.current(0)

tk.Label(frame_product, text="Đơn giá:").grid(row=0, column=4)
entry_price = ttk.Entry(frame_product, width=15)
entry_price.grid(row=0, column=5, padx=5)

product_tree = ttk.Treeview(
    tab_product,
    columns=("MaSP", "TenSP", "DanhMuc", "DonGia", "TrangThai"),
    show="headings"
)

for col, name in [
    ("MaSP", "Mã SP"),
    ("TenSP", "Tên sản phẩm"),
    ("DanhMuc", "Danh mục"),
    ("DonGia", "Đơn giá"),
    ("TrangThai", "Trạng thái")
]:
    product_tree.heading(col, text=name)

product_tree.pack(fill="both", expand=True, padx=15, pady=15)


def load_products():
    clear_tree(product_tree)
    rows = query("""
        SELECT SanPham.MaSP, TenSP, TenDM, DonGia, TrangThai
        FROM SanPham JOIN DanhMuc
        ON SanPham.MaDM = DanhMuc.MaDM
    """)
    for row in rows:
        product_tree.insert("", "end", values=row)


def add_product():
    ten = entry_product.get().strip()
    gia_text = entry_price.get().strip()
    dm = combo_category.get()

    if not ten or not gia_text or not dm:
        messagebox.showwarning("Thông báo", "Vui lòng nhập đầy đủ!")
        return

    try:
        gia = float(gia_text)
        if gia <= 0:
            raise ValueError
    except ValueError:
        messagebox.showerror("Lỗi", "Giá phải là số lớn hơn 0!")
        return

    ma_dm = query(
        "SELECT MaDM FROM DanhMuc WHERE TenDM=?", (dm,)
    )[0][0]

    try:
        conn.execute("""
            INSERT INTO SanPham(TenSP, MaDM, DonGia)
            VALUES (?, ?, ?)
        """, (ten, ma_dm, gia))
        conn.commit()
        entry_product.delete(0, tk.END)
        entry_price.delete(0, tk.END)
        load_products()
        messagebox.showinfo("Thành công", "Đã thêm sản phẩm!")
    except sqlite3.IntegrityError as e:
        messagebox.showerror("Lỗi", str(e))


def edit_product():
    selected = product_tree.selection()
    if not selected:
        messagebox.showwarning("Thông báo", "Hãy chọn sản phẩm!")
        return

    ma = product_tree.item(selected[0])["values"][0]
    old = query(
        "SELECT TenSP, MaDM, DonGia, TrangThai FROM SanPham WHERE MaSP=?",
        (ma,)
    )[0]

    ten = simpledialog.askstring("Sửa sản phẩm", "Tên sản phẩm:", initialvalue=old[0])
    if ten is None:
        return
    if not ten.strip():
        messagebox.showerror("Lỗi", "Tên không được để trống!")
        return

    gia = simpledialog.askfloat(
        "Sửa sản phẩm", "Đơn giá:", initialvalue=old[2], minvalue=0.01
    )
    if gia is None:
        return

    dm = simpledialog.askstring(
        "Sửa sản phẩm",
        "Danh mục (Cà phê/Trà/Nước ép/Bánh ngọt):",
        initialvalue=query("SELECT TenDM FROM DanhMuc WHERE MaDM=?", (old[1],))[0][0]
    )
    if dm is None:
        return

    category = query("SELECT MaDM FROM DanhMuc WHERE TenDM=?", (dm.strip(),))
    if not category:
        messagebox.showerror("Lỗi", "Danh mục không tồn tại!")
        return

    conn.execute("""
        UPDATE SanPham SET TenSP=?, MaDM=?, DonGia=?
        WHERE MaSP=?
    """, (ten.strip(), category[0][0], gia, ma))
    conn.commit()
    load_products()


def delete_product():
    selected = product_tree.selection()
    if not selected:
        messagebox.showwarning("Thông báo", "Hãy chọn sản phẩm!")
        return

    ma = product_tree.item(selected[0])["values"][0]

    if not messagebox.askyesno(
        "Xác nhận", "Ngừng kinh doanh sản phẩm này?"
    ):
        return

    conn.execute(
        "UPDATE SanPham SET TrangThai='Ngừng bán' WHERE MaSP=?", (ma,)
    )
    conn.commit()
    load_products()


product_buttons = ttk.Frame(tab_product)
product_buttons.pack(pady=5)

ttk.Button(
    product_buttons, text="Thêm sản phẩm", command=add_product
).pack(side="left", padx=5)

ttk.Button(
    product_buttons, text="Sửa sản phẩm", command=edit_product
).pack(side="left", padx=5)

ttk.Button(
    product_buttons, text="Ngừng bán", command=delete_product
).pack(side="left", padx=5)


# ==============================
# 5. TAB QUAN LY BAN
# ==============================

tab_table = ttk.Frame(notebook)
notebook.add(tab_table, text="Bàn ăn")

tk.Label(
    tab_table, text="QUẢN LÝ BÀN",
    font=("Arial", 16, "bold")
).pack(pady=10)

table_tree = ttk.Treeview(
    tab_table,
    columns=("MaBan", "TenBan", "SoCho", "TrangThai"),
    show="headings"
)

for col, name in [
    ("MaBan", "Mã bàn"),
    ("TenBan", "Tên bàn"),
    ("SoCho", "Số chỗ"),
    ("TrangThai", "Trạng thái")
]:
    table_tree.heading(col, text=name)

table_tree.pack(fill="both", expand=True, padx=15, pady=15)


def load_tables():
    clear_tree(table_tree)
    for row in query("SELECT * FROM Ban"):
        table_tree.insert("", "end", values=row)


def add_table():
    ten = simpledialog.askstring("Thêm bàn", "Tên bàn:")
    if ten is None:
        return
    if not ten.strip():
        messagebox.showerror("Lỗi", "Tên bàn không được trống!")
        return

    so_cho = simpledialog.askinteger(
        "Thêm bàn", "Số chỗ ngồi:", minvalue=1
    )
    if so_cho is None:
        return

    try:
        conn.execute(
            "INSERT INTO Ban(TenBan, SoCho) VALUES (?, ?)",
            (ten.strip(), so_cho)
        )
        conn.commit()
        load_tables()
    except sqlite3.IntegrityError:
        messagebox.showerror("Lỗi", "Tên bàn đã tồn tại!")


def delete_table():
    selected = table_tree.selection()
    if not selected:
        messagebox.showwarning("Thông báo", "Hãy chọn bàn!")
        return

    ma = table_tree.item(selected[0])["values"][0]

    if query("""
        SELECT 1 FROM DonHang
        WHERE MaBan=? AND TrangThai='Chờ thanh toán'
    """, (ma,)):
        messagebox.showerror("Lỗi", "Bàn đang có đơn chưa thanh toán!")
        return

    if messagebox.askyesno("Xác nhận", "Bạn muốn xóa bàn này?"):
        try:
            conn.execute("DELETE FROM Ban WHERE MaBan=?", (ma,))
            conn.commit()
            load_tables()
        except sqlite3.IntegrityError:
            messagebox.showerror(
                "Lỗi", "Bàn có lịch sử đơn hàng, không thể xóa!"
            )


ttk.Button(
    tab_table, text="Thêm bàn", command=add_table
).pack(side="left", padx=20, pady=10)

ttk.Button(
    tab_table, text="Xóa bàn", command=delete_table
).pack(side="left", padx=10, pady=10)


# ==============================
# 6. TAB QUAN LY KHACH HANG
# ==============================

tab_customer = ttk.Frame(notebook)
notebook.add(tab_customer, text="Khách hàng")

tk.Label(
    tab_customer, text="QUẢN LÝ KHÁCH HÀNG",
    font=("Arial", 16, "bold")
).pack(pady=10)

customer_tree = ttk.Treeview(
    tab_customer,
    columns=("MaKH", "HoTen", "SDT", "Email", "NgayTao"),
    show="headings"
)

for col, name in [
    ("MaKH", "Mã KH"),
    ("HoTen", "Họ tên"),
    ("SDT", "Số điện thoại"),
    ("Email", "Email"),
    ("NgayTao", "Ngày tạo")
]:
    customer_tree.heading(col, text=name)

customer_tree.pack(fill="both", expand=True, padx=15, pady=15)


def load_customers():
    clear_tree(customer_tree)
    for row in query("SELECT * FROM KhachHang"):
        customer_tree.insert("", "end", values=row)


def add_customer():
    ten = simpledialog.askstring("Khách hàng", "Họ tên:")
    if ten is None:
        return
    if not ten.strip():
        messagebox.showerror("Lỗi", "Họ tên không được trống!")
        return

    sdt = simpledialog.askstring("Khách hàng", "Số điện thoại:")
    if sdt is None:
        return

    if sdt and not (
        len(sdt) == 10 and sdt.isdigit() and sdt.startswith("0")
    ):
        messagebox.showerror("Lỗi", "Số điện thoại không hợp lệ!")
        return

    email = simpledialog.askstring("Khách hàng", "Email:") or ""

    try:
        conn.execute("""
            INSERT INTO KhachHang(HoTen, SDT, Email, NgayTao)
            VALUES (?, ?, ?, ?)
        """, (
            ten.strip(), sdt or None, email,
            datetime.now().strftime("%Y-%m-%d")
        ))
        conn.commit()
        load_customers()
    except sqlite3.IntegrityError:
        messagebox.showerror("Lỗi", "Số điện thoại đã tồn tại!")


def delete_customer():
    selected = customer_tree.selection()
    if not selected:
        messagebox.showwarning("Thông báo", "Hãy chọn khách hàng!")
        return

    ma = customer_tree.item(selected[0])["values"][0]

    if query("SELECT 1 FROM DonHang WHERE MaKH=?", (ma,)):
        messagebox.showerror(
            "Lỗi", "Khách hàng đã có lịch sử đơn hàng, không thể xóa!"
        )
        return

    if messagebox.askyesno("Xác nhận", "Xóa khách hàng này?"):
        conn.execute("DELETE FROM KhachHang WHERE MaKH=?", (ma,))
        conn.commit()
        load_customers()


customer_buttons = ttk.Frame(tab_customer)
customer_buttons.pack(pady=10)

ttk.Button(
    customer_buttons, text="Thêm khách hàng", command=add_customer
).pack(side="left", padx=5)

ttk.Button(
    customer_buttons, text="Xóa khách hàng", command=delete_customer
).pack(side="left", padx=5)


# ==============================
# 7. TAB QUAN LY DON HANG
# ==============================

tab_order = ttk.Frame(notebook)
notebook.add(tab_order, text="Đơn hàng")

tk.Label(
    tab_order, text="QUẢN LÝ ĐƠN HÀNG",
    font=("Arial", 16, "bold")
).pack(pady=10)

order_tree = ttk.Treeview(
    tab_order,
    columns=("MaDH", "TenBan", "KhachHang", "ThoiGian", "TongTien", "TrangThai"),
    show="headings"
)

for col, name in [
    ("MaDH", "Mã đơn"),
    ("TenBan", "Bàn"),
    ("KhachHang", "Khách hàng"),
    ("ThoiGian", "Thời gian"),
    ("TongTien", "Tổng tiền"),
    ("TrangThai", "Trạng thái")
]:
    order_tree.heading(col, text=name)

order_tree.pack(fill="both", expand=True, padx=15, pady=15)


def load_orders():
    clear_tree(order_tree)
    rows = query("""
        SELECT D.MaDH, B.TenBan,
               COALESCE(K.HoTen, 'Khách lẻ'),
               D.ThoiGianTao, D.TongTien, D.TrangThai
        FROM DonHang D
        JOIN Ban B ON D.MaBan=B.MaBan
        LEFT JOIN KhachHang K ON D.MaKH=K.MaKH
        ORDER BY D.MaDH DESC
    """)
    for row in rows:
        order_tree.insert("", "end", values=row)


def create_order():
    # Chon ban
    free_tables = query("""
        SELECT MaBan, TenBan FROM Ban
        WHERE TrangThai='Trống'
    """)

    if not free_tables:
        messagebox.showwarning("Thông báo", "Không còn bàn trống!")
        return

    table_text = "\n".join(
        [f"{r[0]} - {r[1]}" for r in free_tables]
    )

    ma_ban = simpledialog.askinteger(
        "Tạo đơn hàng",
        "Chọn mã bàn:\n" + table_text
    )
    if ma_ban is None:
        return

    if not any(r[0] == ma_ban for r in free_tables):
        messagebox.showerror("Lỗi", "Bàn không hợp lệ!")
        return

    # Chon khach hang
    customers = query("SELECT MaKH, HoTen FROM KhachHang")
    customer_text = "Để trống nếu là khách lẻ\n"
    customer_text += "\n".join(
        [f"{r[0]} - {r[1]}" for r in customers]
    )

    ma_kh = simpledialog.askinteger(
        "Khách hàng",
        "Nhập mã khách hàng:\n" + customer_text
    )

    if ma_kh is not None and not any(
        r[0] == ma_kh for r in customers
    ):
        messagebox.showerror("Lỗi", "Khách hàng không tồn tại!")
        return

    # Chon san pham
    products = query("""
        SELECT MaSP, TenSP, DonGia FROM SanPham
        WHERE TrangThai='Đang bán'
    """)

    if not products:
        messagebox.showwarning("Thông báo", "Chưa có sản phẩm!")
        return

    product_text = "\n".join(
        [f"{r[0]} - {r[1]} - {r[2]:,.0f}đ" for r in products]
    )

    ma_sp = simpledialog.askinteger(
        "Chọn sản phẩm",
        "Nhập mã sản phẩm:\n" + product_text
    )
    if ma_sp is None:
        return

    product = next((r for r in products if r[0] == ma_sp), None)
    if product is None:
        messagebox.showerror("Lỗi", "Sản phẩm không hợp lệ!")
        return

    so_luong = simpledialog.askinteger(
        "Số lượng", "Nhập số lượng:", minvalue=1
    )
    if so_luong is None:
        return

    # Tao don va chi tiet trong cung transaction
    try:
        with conn:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            tong = so_luong * product[2]

            cur = conn.execute("""
                INSERT INTO DonHang(
                    MaBan, MaKH, ThoiGianTao, TongTien
                ) VALUES (?, ?, ?, ?)
            """, (ma_ban, ma_kh, now, tong))

            ma_dh = cur.lastrowid

            conn.execute("""
                INSERT INTO ChiTietDonHang(
                    MaDH, MaSP, SoLuong, DonGia, ThanhTien
                ) VALUES (?, ?, ?, ?, ?)
            """, (ma_dh, ma_sp, so_luong, product[2], tong))

            conn.execute("""
                UPDATE Ban SET TrangThai='Đang sử dụng'
                WHERE MaBan=?
            """, (ma_ban,))

        refresh_all()
        messagebox.showinfo("Thành công", f"Đã tạo đơn hàng #{ma_dh}!")
    except sqlite3.Error as e:
        messagebox.showerror("Lỗi", str(e))


def show_order_detail():
    selected = order_tree.selection()
    if not selected:
        messagebox.showwarning("Thông báo", "Hãy chọn đơn hàng!")
        return

    ma = order_tree.item(selected[0])["values"][0]

    details = query("""
        SELECT S.TenSP, C.SoLuong, C.DonGia, C.ThanhTien
        FROM ChiTietDonHang C
        JOIN SanPham S ON C.MaSP=S.MaSP
        WHERE C.MaDH=?
    """, (ma,))

    if not details:
        messagebox.showinfo("Chi tiết", "Đơn hàng không có sản phẩm!")
        return

    content = ""
    for row in details:
        content += (
            f"{row[0]} | SL: {row[1]} | "
            f"Đơn giá: {row[2]:,.0f} | "
            f"Thành tiền: {row[3]:,.0f}\n"
        )

    messagebox.showinfo("Chi tiết đơn hàng", content)


def checkout():
    selected = order_tree.selection()
    if not selected:
        messagebox.showwarning("Thông báo", "Hãy chọn đơn hàng!")
        return

    values = order_tree.item(selected[0])["values"]
    ma_dh = values[0]

    order = query("""
        SELECT MaBan, TongTien, TrangThai
        FROM DonHang WHERE MaDH=?
    """, (ma_dh,))

    if not order or order[0][2] != "Chờ thanh toán":
        messagebox.showerror("Lỗi", "Đơn hàng không thể thanh toán!")
        return

    ma_ban, tong_tien, _ = order[0]

    if not query("SELECT 1 FROM ChiTietDonHang WHERE MaDH=?", (ma_dh,)):
        messagebox.showerror("Lỗi", "Đơn hàng không có sản phẩm!")
        return

    giam = simpledialog.askfloat(
        "Thanh toán", "Nhập số tiền giảm giá:",
        minvalue=0, initialvalue=0
    )
    if giam is None:
        return

    if giam > tong_tien:
        messagebox.showerror("Lỗi", "Giảm giá không được vượt tổng tiền!")
        return

    thanh_tien = tong_tien - giam

    if not messagebox.askyesno(
        "Xác nhận thanh toán",
        f"Tổng tiền: {tong_tien:,.0f}đ\n"
        f"Giảm giá: {giam:,.0f}đ\n"
        f"Phải thanh toán: {thanh_tien:,.0f}đ\n\n"
        "Xác nhận thanh toán?"
    ):
        return

    try:
        with conn:
            # Chi cap nhat neu don van dang cho thanh toan
            result = conn.execute("""
                UPDATE DonHang
                SET GiamGia=?, TongTien=?,
                    TrangThai='Đã thanh toán',
                    ThoiGianTT=?
                WHERE MaDH=? AND TrangThai='Chờ thanh toán'
            """, (
                giam, thanh_tien,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                ma_dh
            ))

            if result.rowcount != 1:
                raise ValueError("Đơn hàng đã được thanh toán!")

            # Chi giai phong ban neu khong con don dang mo
            remaining = query("""
                SELECT 1 FROM DonHang
                WHERE MaBan=? AND TrangThai='Chờ thanh toán'
                  AND MaDH<>?
            """, (ma_ban, ma_dh))

            if not remaining:
                conn.execute("""
                    UPDATE Ban SET TrangThai='Trống'
                    WHERE MaBan=?
                """, (ma_ban,))

        refresh_all()
        messagebox.showinfo(
            "Thành công",
            f"Thanh toán thành công!\nSố tiền: {thanh_tien:,.0f}đ"
        )
    except (sqlite3.Error, ValueError) as e:
        messagebox.showerror("Lỗi", str(e))


order_buttons = ttk.Frame(tab_order)
order_buttons.pack(pady=10)

ttk.Button(
    order_buttons, text="Tạo đơn hàng", command=create_order
).pack(side="left", padx=5)

ttk.Button(
    order_buttons, text="Chi tiết đơn", command=show_order_detail
).pack(side="left", padx=5)

ttk.Button(
    order_buttons, text="Thanh toán", command=checkout
).pack(side="left", padx=5)


# ==============================
# 8. TAB BAO CAO DOANH THU
# ==============================

tab_report = ttk.Frame(notebook)
notebook.add(tab_report, text="Báo cáo")

tk.Label(
    tab_report, text="BÁO CÁO DOANH THU",
    font=("Arial", 16, "bold")
).pack(pady=10)

report_tree = ttk.Treeview(
    tab_report,
    columns=("TenSP", "SoLuong", "DoanhThu"),
    show="headings",
    height=8
)

for col, name in [
    ("TenSP", "Sản phẩm"),
    ("SoLuong", "Số lượng bán"),
    ("DoanhThu", "Doanh thu")
]:
    report_tree.heading(col, text=name)

report_tree.pack(fill="x", padx=15, pady=10)

hour_tree = ttk.Treeview(
    tab_report,
    columns=("KhungGio", "SoDon", "DoanhThu"),
    show="headings",
    height=6
)

for col, name in [
    ("KhungGio", "Khung giờ"),
    ("SoDon", "Số đơn"),
    ("DoanhThu", "Doanh thu")
]:
    hour_tree.heading(col, text=name)

hour_tree.pack(fill="x", padx=15, pady=10)

total_label = tk.Label(
    tab_report,
    text="TỔNG DOANH THU: 0 VNĐ",
    font=("Arial", 14, "bold"),
    fg="#9B542F"
)
total_label.pack(pady=10)


def load_reports():
    clear_tree(report_tree)
    clear_tree(hour_tree)

    # Doanh thu theo san pham
    products = query("""
        SELECT S.TenSP,
               SUM(C.SoLuong),
               SUM(C.ThanhTien)
        FROM ChiTietDonHang C
        JOIN SanPham S ON C.MaSP=S.MaSP
        JOIN DonHang D ON C.MaDH=D.MaDH
        WHERE D.TrangThai='Đã thanh toán'
        GROUP BY S.MaSP, S.TenSP
        ORDER BY SUM(C.ThanhTien) DESC
    """)

    for row in products:
        report_tree.insert("", "end", values=(
            row[0], row[1], f"{row[2]:,.0f} VNĐ"
        ))

    # Doanh thu theo khung gio thanh toan
    rows = query("""
        SELECT
            CASE
                WHEN CAST(strftime('%H', ThoiGianTT) AS INTEGER) >= 6
                     AND CAST(strftime('%H', ThoiGianTT) AS INTEGER) < 10
                    THEN 'Sáng (06-10)'
                WHEN CAST(strftime('%H', ThoiGianTT) AS INTEGER) >= 10
                     AND CAST(strftime('%H', ThoiGianTT) AS INTEGER) < 14
                    THEN 'Trưa (10-14)'
                WHEN CAST(strftime('%H', ThoiGianTT) AS INTEGER) >= 14
                     AND CAST(strftime('%H', ThoiGianTT) AS INTEGER) < 18
                    THEN 'Chiều (14-18)'
                WHEN CAST(strftime('%H', ThoiGianTT) AS INTEGER) >= 18
                     AND CAST(strftime('%H', ThoiGianTT) AS INTEGER) < 22
                    THEN 'Tối (18-22)'
                ELSE 'Ngoài khung giờ'
            END AS KhungGio,
            COUNT(*),
            SUM(TongTien)
        FROM DonHang
        WHERE TrangThai='Đã thanh toán'
        GROUP BY KhungGio
        ORDER BY MIN(strftime('%H', ThoiGianTT))
    """)

    for row in rows:
        hour_tree.insert("", "end", values=(
            row[0], row[1], f"{row[2]:,.0f} VNĐ"
        ))

    total = query("""
        SELECT COALESCE(SUM(TongTien), 0)
        FROM DonHang
        WHERE TrangThai='Đã thanh toán'
    """)[0][0]

    total_label.config(
        text=f"TỔNG DOANH THU: {total:,.0f} VNĐ"
    )


ttk.Button(
    tab_report,
    text="Cập nhật báo cáo",
    command=load_reports
).pack(pady=5)


# ==============================
# 9. KHOI DONG CHUONG TRINH
# ==============================

refresh_all()

def close_app():
    conn.close()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", close_app)
root.mainloop()
